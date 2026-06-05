"""
orchestrator/service.py — Service principal de coordination (v3.2).

Nouveautés vs original :
  1. Indexation automatique des ARTEFACTS dans Qdrant après chaque workflow
     réussi → les agents peuvent retrouver leurs propres productions passées.
  2. Injection de livrables similaires passés dans memory_snippets avant
     d'exécuter le workflow (context enrichment).
  3. Meilleure gestion du fallback quand Redis/Qdrant/Postgres sont absents.
"""

from uuid import uuid4

from app.core.llm import LlmClient
from app.core.logging import get_logger
from app.core.metrics import metrics
from app.core.settings import settings
from app.models import AgentExecutionResult, AgentRunRequest, ExecutionContext
from app.orchestrator.agent_registry import AgentRegistry


class OrchestratorService:
    def __init__(self) -> None:
        self.logger = get_logger("orchestrator")
        self.llm = LlmClient()
        self.registry = AgentRegistry()

        try:
            from app.memory.redis_memory import RedisMemory
            self.redis = RedisMemory()
        except Exception as e:
            self.logger.warning("RedisMemory init failed: %s", e)
            self.redis = None

        try:
            from app.memory.vector_memory import VectorMemory
            self.vector = VectorMemory()
        except Exception as e:
            self.logger.warning("VectorMemory init failed: %s", e)
            self.vector = None

        try:
            from app.memory.postgres_memory import PostgresMemory
            self.pg = PostgresMemory()
        except Exception as e:
            self.logger.warning("PostgresMemory init failed: %s", e)
            self.pg = None

        try:
            from app.memory.firestore_workflow_store import FirestoreWorkflowStore
            self.firestore = FirestoreWorkflowStore()
        except Exception as e:
            self.logger.warning("FirestoreWorkflowStore init failed: %s", e)
            self.firestore = None

        try:
            from app.workflows.langgraph_workflow import build_workflow
            self.workflow = build_workflow(self.registry, self.llm)
        except Exception as e:
            self.logger.warning("Workflow build failed: %s", e)
            self.workflow = None

    async def startup(self) -> None:
        if self.pg is not None:
            try:
                await self.pg.ensure_schema()
            except Exception as e:
                self.logger.warning("pg.ensure_schema skipped: %s", e)

    async def run(self, req: AgentRunRequest) -> AgentExecutionResult:
        workflow_id = str(uuid4())
        memory_snippets: list[str] = []

        # ── 1. Connaissances web apprises (learning engine) ───────────────────
        if settings.web_learning_enabled:
            try:
                from app.tools.learning_engine import get_cached_knowledge, learn_from_web
                topic = req.input[:80]
                cached = get_cached_knowledge(topic)
                if cached:
                    memory_snippets.extend(cached[:5])
                else:
                    insights = await learn_from_web(topic, context_hint=req.project_id)
                    memory_snippets.extend(insights[:5])
            except Exception as exc:
                self.logger.warning("web_learning_skipped: %s", exc)

        # ── 2. Recherche de livrables similaires passés (mémoire institutionnelle) ──
        if self.vector is not None:
            try:
                past_hits = self.vector.search_past_work(
                    query=req.input, limit=4, project_id=req.project_id,
                )
                for hit in past_hits:
                    if hit["score"] > 0.45 and hit.get("content"):
                        agent = hit.get("agent", "")
                        title = hit.get("title", "")
                        preview = hit["content"][:400]
                        memory_snippets.append(
                            f"[TRAVAIL PASSÉ SIMILAIRE — {agent} — {title}]\n{preview}"
                        )
            except Exception as e:
                self.logger.warning("vector.search_past_work skipped: %s", e)

        # ── 3. Connaissances Firestore (learning_engine_v2) ───────────────────
        try:
            from app.tools.learning_engine_v2 import get_agent_knowledge_v2
            # Injection généraliste — le topic = l'input brut
            v2_snippets = await get_agent_knowledge_v2("general", req.input, max_snippets=4)
            memory_snippets.extend(v2_snippets)
        except Exception:
            pass

        context = ExecutionContext(
            workflow_id=workflow_id,
            project_id=req.project_id,
            task_id=req.task_id,
            user_id=req.user_id,
            memory_snippets=memory_snippets[:15],  # cap pour ne pas exploser le contexte
            metadata={"mode": req.mode},
        )

        initial_state = {
            "request": req.input,
            "context": context,
            "plan": [],
            "queue": [],
            "responses": [],
            "timeline": [],
            "retry_map": {},
            "errors": [],
            "total_steps": 0,
            "rework_rounds": 0,
        }

        self.logger.info("workflow.start id=%s project=%s snippets=%d",
                         workflow_id, req.project_id, len(memory_snippets))
        metrics.inc("workflow_started")

        # Sauvegarde initiale Firestore
        if self.firestore is not None:
            try:
                await self.firestore.save_execution(
                    workflow_id=workflow_id, user_id=req.user_id,
                    project_id=req.project_id, task_id=req.task_id,
                    input_text=req.input, status="running",
                    selected_agents=[], plan=[], responses=[],
                    timeline=[], errors=[], metadata={"mode": req.mode},
                )
            except Exception as e:
                self.logger.warning("firestore.save_execution (start) skipped: %s", e)

        if self.workflow is None:
            from app.workflows.langgraph_workflow import build_workflow
            self.workflow = build_workflow(self.registry, self.llm)

        state = await self.workflow.ainvoke(initial_state)

        # ── 4. Indexer les artefacts produits dans Qdrant ─────────────────────
        if self.vector is not None and not state.get("errors"):
            await self._index_artifacts(
                state["responses"], req.input, req.project_id, workflow_id
            )

        # ── 5. Sauvegarde Redis ───────────────────────────────────────────────
        serialized = {
            "plan": state["plan"],
            "responses": state["responses"],
            "timeline": state["timeline"],
            "errors": state.get("errors", []),
        }
        if self.redis is not None:
            try:
                await self.redis.save_short_term(
                    f"workflow:{workflow_id}",
                    {"input": req.input, "state": serialized,
                     "context": context.model_dump()},
                    ttl_seconds=86400,
                )
            except Exception as e:
                self.logger.warning("redis.save_short_term skipped: %s", e)

        # ── 6. Compatibilité vector (input text) ──────────────────────────────
        memory_id = workflow_id
        if self.vector is not None:
            try:
                memory_id = self.vector.save_semantic_memory(
                    req.input,
                    {
                        "workflow_id": workflow_id,
                        "project_id": req.project_id,
                        "task_id": req.task_id,
                        "selected_agents": [r["agent"] for r in state["responses"]],
                    },
                )
            except Exception as e:
                self.logger.warning("vector.save_semantic_memory skipped: %s", e)

        # ── 7. Sauvegarde PostgreSQL ──────────────────────────────────────────
        primary_response = state["responses"][0] if state["responses"] else {"summary": ""}
        if self.pg is not None:
            try:
                await self.pg.save_history(
                    memory_id=memory_id, project_id=req.project_id,
                    task_id=req.task_id, user_id=req.user_id,
                    agent_name="workflow", input_text=req.input,
                    output_text=primary_response.get("summary", ""),
                    metadata={"workflow_id": workflow_id, **serialized},
                )
                for step in state["timeline"]:
                    await self.pg.save_step(
                        step_id=str(uuid4()), workflow_id=workflow_id,
                        node_name=step.node if hasattr(step, "node") else step.get("node", ""),
                        success=step.success if hasattr(step, "success") else step.get("success", True),
                        details=step.model_dump() if hasattr(step, "model_dump") else step,
                    )
            except Exception as e:
                self.logger.warning("pg.save_history/steps skipped: %s", e)

        # ── 8. Sauvegarde finale Firestore ────────────────────────────────────
        selected_agents = [r["agent"] for r in state["responses"]]
        status = "failed" if state.get("errors") else "succeeded"

        if self.firestore is not None:
            try:
                await self.firestore.save_execution(
                    workflow_id=workflow_id, user_id=req.user_id,
                    project_id=req.project_id, task_id=req.task_id,
                    input_text=req.input, status=status,
                    selected_agents=selected_agents, plan=state["plan"],
                    responses=state["responses"], timeline=state["timeline"],
                    errors=state.get("errors", []),
                    metadata={"mode": req.mode, "memoryId": memory_id},
                )
            except Exception as e:
                self.logger.warning("firestore.save_execution (final) skipped: %s", e)

        if state.get("errors"):
            metrics.inc("workflow_failed")
        else:
            metrics.inc("workflow_succeeded")

        return AgentExecutionResult(
            workflow_id=workflow_id,
            selected_agents=selected_agents,
            plan=state["plan"],
            responses=state["responses"],
            review=next(
                (r for r in state["responses"] if r["agent"] == "ReviewerAgent"), None
            ),
            timeline=state["timeline"],
            context=context,
        )

    async def _index_artifacts(
        self,
        responses: list[dict],
        input_text: str,
        project_id: str,
        workflow_id: str,
    ) -> None:
        """
        Indexe chaque artefact produit dans la mémoire vectorielle.
        Non-bloquant — les erreurs sont loggées et ignorées.
        """
        input_preview = input_text[:200]
        count = 0
        for resp in responses:
            agent = resp.get("agent", "")
            artifacts = resp.get("artifacts", [])
            for art in artifacts:
                if not isinstance(art, dict):
                    continue
                content = str(art.get("content", ""))
                if len(content) < 50:  # trop court pour être utile
                    continue
                try:
                    self.vector.index_artifact(
                        agent=agent,
                        title=str(art.get("title", "")),
                        content=content,
                        artifact_type=str(art.get("type", "livrable")),
                        workflow_id=workflow_id,
                        project_id=project_id,
                        input_preview=input_preview,
                    )
                    count += 1
                except Exception as e:
                    self.logger.debug("index_artifact failed: %s", e)

        if count > 0:
            self.logger.info("artifacts_indexed count=%d workflow=%s", count, workflow_id)


# Singleton
orchestrator_service = OrchestratorService()
