import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.models import AgentRunRequest, ExecutionContext, SubTask
from app.orchestrator.dependencies import get_orchestrator
from app.orchestrator.service import OrchestratorService

router = APIRouter()


# ── Existing workflow endpoint ────────────────────────────────────────────────

class RunRequest(BaseModel):
    input: str = Field(..., description="User prompt or task")
    agent_id: str = Field("default", description="Which agent to run")
    project_id: str = Field("default-project", description="Project context")
    task_id: str | None = Field(default=None, description="Task identifier")
    user_id: str = Field("system", description="Caller identity")
    mode: str = Field("autonomous", description="Execution mode")


class ProjectGenerationRequest(BaseModel):
    request: str = Field(..., description="Project intent")
    project_id: str = Field("generated-project")
    user_id: str = Field("system")


@router.post("/agents/run")
async def run_agent(req: RunRequest, orchestrator: OrchestratorService = Depends(get_orchestrator)):
    result = await orchestrator.run(
        AgentRunRequest(
            input=req.input,
            project_id=req.project_id,
            task_id=req.task_id,
            user_id=req.user_id,
            mode=req.mode,
        )
    )
    return result.model_dump()


@router.get("/agents")
async def list_agents(orchestrator: OrchestratorService = Depends(get_orchestrator)):
    return {"ok": True, "agents": orchestrator.registry.list_knb_agents()}


@router.post("/agents/generate-project")
async def generate_project(
    req: ProjectGenerationRequest,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
):
    enriched = (
        f"Génère un blueprint de projet complet.\n"
        f"Demande : {req.request}\n"
        f"Inclure : architecture, frontend, backend, QA et déploiement."
    )
    result = await orchestrator.run(
        AgentRunRequest(
            input=enriched,
            project_id=req.project_id,
            user_id=req.user_id,
            mode="project-generation",
        )
    )
    return result.model_dump()


# ── Direct agent chat endpoint ────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    agent_id: str = Field(..., description="Agent name (snake_case or PascalCase)")
    message: str = Field(..., description="User message")
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    project_id: str = Field("knb-agents", description="Project context")
    use_web_learning: bool = Field(True, description="Inject web learning insights")


def _resolve_agent_name(agent_id: str, registry) -> str | None:
    """Accept both snake_case and PascalCase agent identifiers."""
    # Direct match
    try:
        registry.get(agent_id)
        return agent_id
    except (KeyError, Exception):
        pass
    # Try matching by snake id
    for agent_info in registry.list_agents():
        if agent_info["id"] == agent_id or agent_info["name"].lower() == agent_id.lower():
            return agent_info["name"]
    return None


_GREETING_PATTERNS = {
    "hello", "hi", "bonjour", "bonsoir", "salut", "hey", "coucou",
    "bonne journée", "bonne soirée", "bonne nuit", "merci", "ok", "d'accord",
    "super", "parfait", "cool", "👋", "😊",
}

def _is_greeting(message: str) -> bool:
    """Détecte les messages conversationnels courts qui ne nécessitent pas le pipeline complet."""
    stripped = message.strip().lower().rstrip("!?., ")
    if stripped in _GREETING_PATTERNS:
        return True
    if len(stripped) <= 20 and not any(c in stripped for c in ["?", "comment", "quel", "quoi", "aide", "besoin"]):
        return True
    return False


_AGENT_GREETINGS: dict[str, str] = {
    "CommercialAgent":         "Bonjour ! Je suis votre expert commercial KNB. Que puis-je faire pour vous ? Devis, proposition, stratégie de vente, réponse à une objection… je suis là.",
    "MarketingAgent":          "Bonjour ! Je suis votre expert marketing. Quelle est votre prochaine campagne, cible ou problématique marketing ?",
    "CommunityManagerAgent":   "Bonjour ! Je gère votre présence digitale. Besoin d'un calendrier éditorial, d'une publication ou d'une stratégie réseaux sociaux ?",
    "ArchitecteAgent":         "Bonjour ! Je suis votre architecte technique. Quel système voulez-vous concevoir ou auditer ?",
    "DevFrontendAgent":        "Bonjour ! Je suis votre développeur frontend. Quel composant, page ou problème UI souhaitez-vous résoudre ?",
    "DevBackendAgent":         "Bonjour ! Je suis votre développeur backend. API, base de données, performance… sur quoi travaillons-nous ?",
    "DevMobileAgent":          "Bonjour ! Je suis votre développeur mobile (React Native / Flutter). Quel écran ou fonctionnalité développons-nous ?",
    "DevOpsAgent":             "Bonjour ! Je suis votre ingénieur DevOps. CI/CD, Docker, déploiement Render/Vercel… quel est votre chantier ?",
    "QAAgent":                 "Bonjour ! Je suis votre expert QA. Tests, bugs, critères d'acceptation… que voulez-vous valider ?",
    "DesignerUXUIAgent":       "Bonjour ! Je suis votre designer UX/UI. Quelle expérience utilisateur voulez-vous concevoir ?",
    "DesignerGraphiqueAgent":  "Bonjour ! Je suis votre designer graphique. Charte graphique, logo, visuels… quel projet créatif ?",
    "RedacteurAgent":          "Bonjour ! Je suis votre rédacteur. Articles, copies, scripts… quel contenu souhaitez-vous créer ?",
    "ChefDeProjetAgent":       "Bonjour ! Je suis votre chef de projet. Planning, roadmap, coordination d'équipe… comment vous aider ?",
    "SupportClientAgent":      "Bonjour ! Je suis votre expert support client. Comment puis-je vous aider aujourd'hui ?",
    "FinanceAgent":            "Bonjour ! Je suis votre expert finance. Budget, factures, trésorerie… quelle analyse souhaitez-vous ?",
    "ReviewerAgent":           "Bonjour ! Je suis votre reviewer. Soumettez votre livrable et je l'évalue selon nos critères qualité.",
}


@router.post("/agents/chat")
async def chat_with_agent(
    req: ChatRequest,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
):
    agent_name = _resolve_agent_name(req.agent_id, orchestrator.registry)
    if agent_name is None:
        return {"ok": False, "error": f"Agent '{req.agent_id}' not found"}

    # Court-circuit pour les salutations : pas besoin du pipeline complet
    if _is_greeting(req.message):
        greeting = _AGENT_GREETINGS.get(
            agent_name,
            f"Bonjour ! Je suis {agent_name}. Comment puis-je vous aider ?"
        )
        from app.models import AgentResponse
        return {
            "ok": True,
            "agent_id": req.agent_id,
            "agent_name": agent_name,
            "response": AgentResponse(
                agent=agent_name,
                summary=greeting,
                artifacts=[],
                followups=["Décrivez votre besoin", "Quel est votre projet ?", "Comment puis-je vous aider ?"],
                score=1.0,
            ).model_dump(),
            "learned_from": [],
        }

    # Si le LLM n'est pas disponible, retourner un message clair plutôt que le fallback métier
    if not orchestrator.llm.enabled():
        from app.models import AgentResponse
        return {
            "ok": True,
            "agent_id": req.agent_id,
            "agent_name": agent_name,
            "response": AgentResponse(
                agent=agent_name,
                summary=(
                    "⚠️ Le service IA n'est pas disponible en ce moment. "
                    "Aucune clé LLM (GROQ_API_KEY, GEMINI_API_KEY) n'est configurée "
                    "sur le service knb-ai-service. Ajoutez une clé sur Render Dashboard "
                    "→ knb-ai-service → Environment Variables."
                ),
                artifacts=[],
                followups=[],
                score=0.0,
            ).model_dump(),
            "learned_from": [],
        }

    # Build memory snippets from conversation history
    memory_snippets: list[str] = []
    for msg in req.conversation_history[-20:]:  # last 20 messages for context
        memory_snippets.append(f"{msg.role}: {msg.content[:200]}")

    # Optionally inject web learning insights
    learned_from: list[str] = []
    if req.use_web_learning:
        try:
            from app.tools.learning_engine import get_cached_knowledge, learn_from_web
            from app.core.settings import settings
            topic = req.message[:80]
            cached = get_cached_knowledge(topic)
            if cached:
                memory_snippets.extend(cached)
                learned_from = cached
            elif settings.web_learning_enabled:
                insights = await learn_from_web(topic, context_hint=req.project_id)
                memory_snippets.extend(insights)
                learned_from = insights
        except Exception:
            pass

    context = ExecutionContext(
        workflow_id=f"chat-{req.project_id}",
        project_id=req.project_id,
        task_id=None,
        user_id="user",
        memory_snippets=memory_snippets,
        metadata={"chat": True},
    )

    # Build a synthetic SubTask from the chat message
    subtask = SubTask(
        id="chat-task",
        title=req.message[:100],
        description=(
            f"[MODE CHAT — Réponse conversationnelle attendue]\n"
            f"Message utilisateur : {req.message}\n\n"
            "Si le message est une question ou une demande simple, réponds directement et "
            "concisément. Ne génère un livrable complet que si le message le justifie explicitement."
        ),
        assigned_agent=agent_name,
        priority=1,
    )

    try:
        agent = orchestrator.registry.get(agent_name)
        response = await agent.execute(subtask, context, orchestrator.llm)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    # Persist conversation in Firestore
    try:
        from app.core.firebase import get_firestore_client
        from firebase_admin import firestore as fs

        client = get_firestore_client()
        if client:
            conv_ref = (
                client.collection("agentConversations")
                .document(req.project_id)
                .collection(agent_name)
                .document()
            )
            await asyncio.to_thread(conv_ref.set, {
                "message": req.message,
                "response": response.model_dump(),
                "learnedFrom": learned_from,
                "createdAt": fs.SERVER_TIMESTAMP,
            })
    except Exception:
        pass

    return {
        "ok": True,
        "agent_id": req.agent_id,
        "agent_name": agent_name,
        "response": response.model_dump(),
        "learned_from": learned_from,
    }


# ── Feedback / rating endpoint ────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    workflow_id: str = Field(..., description="Workflow or chat session ID")
    agent_id: str = Field(..., description="Agent that produced the response")
    rating: int = Field(..., ge=1, le=5, description="1 (bad) to 5 (excellent)")
    comment: str = Field("", description="Optional qualitative feedback")
    task_title: str = Field("", description="Task title for context")


@router.post("/agents/feedback")
async def submit_feedback(req: FeedbackRequest):
    """Store agent response feedback in Firestore for future fine-tuning signals."""
    try:
        from app.core.firebase import get_firestore_client
        from firebase_admin import firestore as fs

        client = get_firestore_client()
        if client:
            doc = {
                "workflow_id": req.workflow_id,
                "agent_id": req.agent_id,
                "rating": req.rating,
                "comment": req.comment,
                "task_title": req.task_title,
                "createdAt": fs.SERVER_TIMESTAMP,
            }
            await asyncio.to_thread(
                client.collection("agentFeedback").document().set, doc
            )
            return {"ok": True, "message": "Feedback enregistré"}
        return {"ok": False, "error": "Firestore non disponible"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ── Self-training endpoints ────────────────────────────────────────────────────

class TrainRequest(BaseModel):
    agent_id: str | None = Field(None, description="Specific agent to train, or null for all")
    force: bool = Field(False, description="Re-train even if knowledge is still fresh")


@router.post("/agents/train")
async def trigger_training(req: TrainRequest):
    """
    Launch agent self-training in background.
    Each agent researches the web on its curriculum topics and stores insights in Firestore.
    These insights are then automatically injected before every future task execution.
    """
    from app.tools.agent_trainer import AGENT_CURRICULUMS, run_global_training, train_agent

    if req.agent_id:
        if req.agent_id not in AGENT_CURRICULUMS:
            return {"ok": False, "error": f"Agent '{req.agent_id}' inconnu ou sans curriculum"}
        asyncio.create_task(train_agent(req.agent_id, force=req.force))
        return {
            "ok": True,
            "message": f"Formation de {req.agent_id} lancée en arrière-plan",
            "topics": len(AGENT_CURRICULUMS[req.agent_id]),
        }

    agents = list(AGENT_CURRICULUMS.keys())
    asyncio.create_task(run_global_training(force=req.force))
    return {
        "ok": True,
        "message": "Formation globale lancée en arrière-plan pour tous les agents",
        "agents": len(agents),
        "total_topics": sum(len(v) for v in AGENT_CURRICULUMS.values()),
    }


# ── Learn a custom topic or URL ───────────────────────────────────────────────

class LearnCustomRequest(BaseModel):
    agent_id: str = Field(..., description="Agent who should learn this")
    topic: str = Field(..., description="Keyword topic OR https:// URL of a course/doc page")


@router.post("/agents/learn-custom")
async def learn_custom(req: LearnCustomRequest, orchestrator: OrchestratorService = Depends(get_orchestrator)):
    """
    Assign a custom learning topic or URL to an agent.
    - If topic starts with http(s)://, the page is scraped and summarised directly.
    - Otherwise, a web search is performed and results are summarised.
    Insights are saved in Firestore and injected into the agent's future responses.
    """
    agent_name = _resolve_agent_name(req.agent_id, orchestrator.registry)
    if agent_name is None:
        return {"ok": False, "error": f"Agent '{req.agent_id}' introuvable"}

    topic = req.topic.strip()

    async def _do_learn() -> list[str]:
        from app.tools.agent_trainer import _save_agent_topic
        from app.tools.learning_engine import learn_from_web

        if topic.startswith(("http://", "https://")):
            from app.tools.web_scraper import scrape
            from app.core.llm import LlmClient
            page = await asyncio.to_thread(scrape, topic)
            if not page or not page.content:
                return []
            llm = LlmClient()
            data = llm.json_completion(
                system_prompt=(
                    "Tu es expert en synthèse de cours et documentation technique. "
                    "Extrais les insights clés, actionnables et pratiques de ce contenu "
                    "pour un agent IA d'agence digitale africaine. "
                    "Retourne JSON: {\"insights\": [\"insight1\", ...]} — max 8 insights en français."
                ),
                user_prompt=f"Source: {topic}\n\nContenu:\n{page.content[:3500]}",
                fallback={"insights": [f"Contenu étudié depuis {topic}"]},
            )
            insights = [str(i) for i in data.get("insights", [])[:8]]
            await _save_agent_topic(agent_name, topic, insights, [topic])
            return insights
        else:
            return await learn_from_web(topic, context_hint=agent_name)

    try:
        insights = await _do_learn()
        return {
            "ok": True,
            "agent_id": req.agent_id,
            "agent_name": agent_name,
            "topic": topic,
            "insights_count": len(insights),
            "insights": insights,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.get("/agents/training-status")
async def training_status():
    """Return what each agent has learned so far."""
    from app.tools.agent_trainer import get_training_status
    statuses = await get_training_status()
    total_topics = sum(s.get("topics_learned", 0) for s in statuses if isinstance(s, dict))
    trained_agents = sum(1 for s in statuses if isinstance(s, dict) and s.get("is_trained"))
    return {
        "ok": True,
        "agents": statuses,
        "summary": {
            "total_agents": len(statuses),
            "trained_agents": trained_agents,
            "total_topics_learned": total_topics,
        },
    }
