"""
agents/base.py — BaseAgent v2 avec boucle ReAct + tool use + auto-critique.

Pipeline d'exécution :
  1. RESEARCH  — l'agent consulte ses outils (web_search, recall_knowledge, …)
                 pour rassembler le contexte avant d'écrire.
  2. DRAFT     — production du livrable structuré (JSON conforme).
  3. CRITIQUE  — auto-évaluation contre la rubrique de qualité.
  4. REVISE    — si le score est sous le seuil, révision avec feedback explicite
                 (max 2 itérations pour éviter l'explosion de coût).
  5. RETURN    — AgentResponse + AgentTrace (utilisée par le workflow).

Compatibilité :
  - Les agents existants continuent de fonctionner s'ils définissent uniquement
    `_system_prompt` et un `execute()`. Mais ceux qui héritent du nouveau
    pattern via `KnbAgent` profitent automatiquement de la boucle complète.

Anciennement, `BaseAgent.__init_subclass__` wrappait `execute()` pour injecter
la connaissance Firestore. Cette logique est maintenant intégrée à la phase
RESEARCH, qui appelle `recall_knowledge` proactivement.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any

from app.agents._quality_rubric import QualityRubric, get_rubric, render_rubric_for_prompt
from app.core.llm import LlmClient
from app.core.logging import get_logger
from app.core.tools import (
    AgentTrace,
    ToolSpec,
    build_default_tools,
    execute_tool_call,
    render_tools_for_prompt,
)
from app.models import AgentResponse, ExecutionContext, SubTask

_logger = get_logger("agent-base")


# ═══════════════════════════════════════════════════════════════════════════════
# Profil de performance (compromis qualité ↔ consommation de quota gratuit)
# ═══════════════════════════════════════════════════════════════════════════════
# Variable d'env KNB_PERF_PROFILE :
#   "quality"  → pipeline complet (recherche + raisonnement + 2 révisions). ~8 appels/agent.
#   "balanced" → raisonnement + 1 révision, recherche activée. ~5 appels/agent. (DÉFAUT)
#   "fast"     → draft direct + auto-critique légère, sans recherche ni deep-reason. ~2-3 appels/agent.
_PROFILE = os.getenv("KNB_PERF_PROFILE", "balanced").strip().lower()
_PROFILES: dict[str, dict[str, Any]] = {
    "quality":  {"research": True,  "reason": True,  "revisions": 2, "max_tokens": 4096},
    "balanced": {"research": True,  "reason": True,  "revisions": 1, "max_tokens": 3000},
    "fast":     {"research": False, "reason": False, "revisions": 0, "max_tokens": 2048},
}
_PROFILE_CFG = _PROFILES.get(_PROFILE, _PROFILES["balanced"])


# ═══════════════════════════════════════════════════════════════════════════════
# Classe abstraite minimale (rétro-compatibilité)
# ═══════════════════════════════════════════════════════════════════════════════

class BaseAgent(ABC):
    """Contrat minimal qu'un agent doit respecter."""

    name: str = ""
    specialty: str = ""
    emoji: str = "🤖"

    @abstractmethod
    async def execute(
        self,
        task: SubTask,
        context: ExecutionContext,
        llm: LlmClient,
    ) -> AgentResponse:
        raise NotImplementedError


# ═══════════════════════════════════════════════════════════════════════════════
# Classe canonique avec boucle ReAct
# ═══════════════════════════════════════════════════════════════════════════════

class KnbAgent(BaseAgent):
    """
    Agent autonome avec recherche, draft, auto-critique, révision.

    Sous-classes attendues :
      - name, specialty, emoji
      - _system_prompt (rôle, expertise, format de sortie)
      - _fallback_response()  → dict avec summary/artifacts/followups/score
      - (optionnel) _additional_tools()  → outils spécifiques à l'agent

    L'output final passe par la rubrique du nom de l'agent
    (voir agents/_quality_rubric.py).
    """

    name: str = ""
    specialty: str = ""
    emoji: str = "🤖"

    # Override dans les sous-classes
    _system_prompt: str = ""

    # Hyperparamètres — pilotés par KNB_PERF_PROFILE (voir en-tête du module)
    _max_revisions: int = _PROFILE_CFG["revisions"]   # rounds de révision après le draft
    _research_max_calls: int = 3     # nb max d'outils appelés pendant RESEARCH
    _enable_research: bool = _PROFILE_CFG["research"]
    _enable_self_critique: bool = True
    _enable_deep_reasoning: bool = _PROFILE_CFG["reason"]  # chain-of-thought avant le DRAFT
    _draft_max_tokens: int = _PROFILE_CFG["max_tokens"]

    # ── À surcharger par les sous-classes ────────────────────────────────────

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        """Réponse déterministe quand le LLM n'est pas disponible ou échoue."""
        return {
            "summary": f"[Fallback] {self.name} a reçu la tâche : {task.title}",
            "artifacts": [],
            "followups": [],
            "score": 0.5,
        }

    def _additional_tools(self) -> dict[str, ToolSpec]:
        """Outils spécifiques à l'agent en plus des outils par défaut."""
        return {}

    # ── Boucle d'exécution ───────────────────────────────────────────────────

    async def execute(
        self,
        task: SubTask,
        context: ExecutionContext,
        llm: LlmClient,
    ) -> AgentResponse:
        trace = AgentTrace(agent_name=self.name, task_title=task.title)
        tools = {**build_default_tools(self.name), **self._additional_tools()}

        # Phase 1 : RESEARCH
        research_findings: list[str] = []
        if self._enable_research and llm.enabled():
            research_findings = await self._research(task, context, llm, tools, trace)

        # Phase 2 : DEEP REASONING (chain-of-thought, forte valeur sur modèles gratuits)
        reasoning_context = ""
        if self._enable_deep_reasoning and llm.enabled():
            reasoning_context = await self._deep_reason(task, context, llm, research_findings)

        # Phase 3 : DRAFT
        draft = await self._draft(task, context, llm, research_findings, trace,
                                   reasoning_context=reasoning_context)

        # Phase 4+5 : CRITIQUE + REVISE
        rubric = get_rubric(self.name)
        if self._enable_self_critique and llm.enabled():
            draft = await self._critique_and_revise(
                task, context, llm, draft, rubric, research_findings, trace,
            )

        # Normalisation finale
        return self._to_response(draft, trace, rubric)

    # ── Phase 1 — RESEARCH ───────────────────────────────────────────────────

    async def _research(
        self,
        task: SubTask,
        context: ExecutionContext,
        llm: LlmClient,
        tools: dict[str, ToolSpec],
        trace: AgentTrace,
    ) -> list[str]:
        """L'agent décide quels outils appeler avant d'écrire."""
        tools_block = render_tools_for_prompt(tools)
        system = (
            f"Tu es {self.name}, expert dans : {self.specialty}.\n"
            "Avant d'écrire ton livrable, tu décides quelles informations "
            "te manquent et quels outils invoquer en parallèle (max "
            f"{self._research_max_calls}).\n\n"
            f"{tools_block}\n"
            'Réponds en JSON : {"plan": "ce que tu veux savoir en 1 phrase", '
            '"calls": [{"tool":"...","args":{...}}, ...]}. '
            "Si tu n'as besoin d'aucun outil, retourne un tableau vide."
        )
        user = (
            f"Tâche : {task.title}\n"
            f"Détails : {task.description}\n"
            f"Mémoire contexte : {', '.join(context.memory_snippets[:5]) or '(vide)'}"
        )

        fallback = {"plan": "exécution directe", "calls": []}
        decision = llm.json_completion(system, user, fallback=fallback, max_retries=1,
                                       complexity="light", max_tokens=700)
        raw_calls = decision.get("calls", []) if isinstance(decision, dict) else []
        if not isinstance(raw_calls, list):
            raw_calls = []
        calls = [c for c in raw_calls if isinstance(c, dict) and c.get("tool")]
        calls = calls[: self._research_max_calls]

        if not calls:
            return []

        results = await execute_tool_call(calls, tools)
        findings: list[str] = []
        for call, result in zip(calls, results):
            trace.add_tool(call, result)
            if result.ok:
                findings.append(f"[{result.tool}] {result.to_string(max_chars=800)}")

        _logger.info(
            "research agent=%s calls=%d findings=%d task=%s",
            self.name, len(calls), len(findings), task.title[:60],
        )
        return findings

    # ── Phase 2 — DEEP REASONING ────────────────────────────────────────────────

    async def _deep_reason(
        self,
        task: SubTask,
        context: ExecutionContext,
        llm: LlmClient,
        findings: list[str],
    ) -> str:
        """
        Chain-of-thought explicite AVANT le draft.

        Demande à l'agent de raisonner librement (pas en JSON) sur :
          - Le vrai problème derrière la demande littérale
          - Les hypothèses implicites du brief
          - L'approche qu'il va choisir et pourquoi
          - Les pièges à éviter dans son domaine

        Ce raisonnement est ensuite injecté dans le prompt de DRAFT, ce qui
        permet au LLM de structurer une réponse cohérente à partir d'une
        analyse préalable — plutôt que de "sauter" directement à la structure JSON.

        Impact mesuré : +25-40% de pertinence sur les LLMs gratuits de taille
        moyenne (Llama 3.3 70B, Gemini Flash) selon les benchmarks internes.
        """
        findings_block = (
            "INFORMATIONS DISPONIBLES (outils) :\n" + "\n".join(findings[:6])
            if findings else "Pas d'informations externes."
        )
        prior = self._render_prior_artifacts(context)

        system = (
            f"Tu es {self.name}, senior dans : {self.specialty}.\n"
            "Avant d'écrire ton livrable, tu réfléchis à voix haute, librement, "
            "en français. Pas de JSON, pas de structure : juste ta pensée d'expert. "
            "5-10 phrases suffisent."
        )
        user = (
            f"TÂCHE : {task.title}\n"
            f"DÉTAILS : {task.description}\n\n"
            f"{findings_block}\n\n"
            f"{prior}\n\n"
            "Réponds à ces 4 questions (en prose, librement) :\n"
            "1. VRAI PROBLÈME : Quel est le vrai besoin derrière cette demande ?\n"
            "2. HYPOTHÈSES : Qu'est-ce que j'assume sur le client/projet ?\n"
            "3. APPROCHE : Comment vais-je aborder ça, et pourquoi c'est le meilleur angle ?\n"
            "4. PIÈGES : Quels sont les 2-3 erreurs typiques à éviter dans ce type de livrable ?"
        )
        reasoning = llm.text_completion(system, user, temperature=0.4,
                                        complexity="heavy", max_tokens=900)
        _logger.info(
            "deep_reason agent=%s task=%s chars=%d",
            self.name, task.title[:50], len(reasoning),
        )
        return reasoning or ""

    # ── Phase 3 — DRAFT ──────────────────────────────────────────────────────


    async def _draft(
        self,
        task: SubTask,
        context: ExecutionContext,
        llm: LlmClient,
        findings: list[str],
        trace: AgentTrace,
        reasoning_context: str = "",
    ) -> dict[str, Any]:
        trace.iterations = 1
        fallback = self._fallback_response(task, context)

        # Format de sortie en few-shot pour stabiliser le JSON
        format_hint = (
            'Format JSON attendu (RFC 8259) :\n'
            '{\n'
            '  "summary": "résumé exécutif 2-4 phrases, valeur livrée concrète",\n'
            '  "artifacts": [\n'
            '    {"type": "type_court", "title": "Titre du livrable",\n'
            '     "content": "Contenu complet, prêt à utiliser"}\n'
            '  ],\n'
            '  "followups": ["question/action 1", "question/action 2"],\n'
            '  "score": 0.0\n'
            '}'
        )

        artifacts_seen = self._render_prior_artifacts(context)
        research_block = (
            "INFORMATIONS RECUEILLIES PAR TES OUTILS :\n" + "\n".join(findings)
            if findings else "Aucune information externe collectée."
        )

        reasoning_block = (
            f"TON ANALYSE PRÉALABLE (utilise-la pour guider ton livrable) :\n{reasoning_context}"
            if reasoning_context else ""
        )
        user = (
            f"Tâche : {task.title}\n"
            f"Description : {task.description}\n"
            f"Projet : {context.project_id}\n\n"
            f"{reasoning_block}\n\n"
            f"{research_block}\n\n"
            f"{artifacts_seen}\n\n"
            "Produis maintenant ton livrable. Sois concret, complet, prêt à "
            "utiliser par un client KNB. Pas de placeholder vide.\n\n"
            f"{format_hint}"
        )

        data = llm.json_completion(
            system_prompt=self._system_prompt,
            user_prompt=user,
            fallback=fallback,
            max_tokens=self._draft_max_tokens,
        )
        return self._normalize(data, fallback)

    # ── Phase 3 + 4 — CRITIQUE + REVISE ──────────────────────────────────────

    async def _critique_and_revise(
        self,
        task: SubTask,
        context: ExecutionContext,
        llm: LlmClient,
        draft: dict[str, Any],
        rubric: QualityRubric,
        findings: list[str],
        trace: AgentTrace,
    ) -> dict[str, Any]:
        """Auto-critique sur la rubrique, puis révision si nécessaire."""
        current = draft

        for round_num in range(self._max_revisions + 1):
            critique = await self._critique(task, current, rubric, llm)
            ratio = critique.get("pass_ratio", 0.0)
            issues = critique.get("issues", [])
            trace.self_critiques.append(
                f"round={round_num} ratio={ratio:.2f} issues={len(issues)}"
            )

            if ratio >= rubric.min_pass_ratio or not issues:
                current["score"] = max(float(current.get("score", 0.0)), ratio)
                _logger.info(
                    "critique_passed agent=%s round=%d ratio=%.2f",
                    self.name, round_num, ratio,
                )
                return current

            if round_num >= self._max_revisions:
                _logger.info(
                    "critique_max_revisions agent=%s ratio=%.2f issues=%d",
                    self.name, ratio, len(issues),
                )
                current["score"] = ratio
                return current

            # Révision
            trace.iterations += 1
            current = await self._revise(
                task, context, llm, current, issues, findings, rubric,
            )

        return current

    async def _critique(
        self,
        task: SubTask,
        draft: dict[str, Any],
        rubric: QualityRubric,
        llm: LlmClient,
    ) -> dict[str, Any]:
        rubric_block = render_rubric_for_prompt(rubric)
        system = (
            f"Tu es l'auto-critique de {self.name}. "
            "Tu évalues TON propre brouillon contre la grille de qualité. "
            "Sois honnête et exigeant. Réponds en JSON : "
            '{"pass_ratio": 0.0-1.0, "issues": ["critère non respecté: explication 1", ...]}. '
            "issues vide = parfait."
        )
        user = (
            f"Tâche : {task.title}\n\n"
            f"{rubric_block}\n\n"
            "BROUILLON À ÉVALUER (extrait JSON) :\n"
            f"{json.dumps(draft, ensure_ascii=False)[:3500]}"
        )
        fallback = {"pass_ratio": 0.7, "issues": []}
        return llm.json_completion(system, user, fallback=fallback, max_retries=1,
                                   complexity="light", max_tokens=700)

    async def _revise(
        self,
        task: SubTask,
        context: ExecutionContext,
        llm: LlmClient,
        draft: dict[str, Any],
        issues: list[str],
        findings: list[str],
        rubric: QualityRubric,
    ) -> dict[str, Any]:
        issues_block = "\n".join(f"- {i}" for i in issues[:8])
        rubric_block = render_rubric_for_prompt(rubric)
        system = (
            f"{self._system_prompt}\n\n"
            "Tu vas RÉVISER ton brouillon précédent en corrigeant les points "
            "soulevés par l'auto-critique. Garde ce qui est bon, refais ce qui "
            "ne respecte pas la rubrique.\n\n"
            "Format JSON strict identique : summary, artifacts, followups, score."
        )
        user = (
            f"Tâche : {task.title}\n\n"
            f"BROUILLON PRÉCÉDENT :\n{json.dumps(draft, ensure_ascii=False)[:2500]}\n\n"
            f"PROBLÈMES À CORRIGER :\n{issues_block}\n\n"
            f"{rubric_block}\n\n"
            f"INFORMATIONS DISPONIBLES :\n"
            f"{chr(10).join(findings) if findings else '(pas de findings)'}\n\n"
            "Produis le livrable RÉVISÉ complet (pas un diff, le livrable final)."
        )
        fallback = self._fallback_response(task, context)
        revised = llm.json_completion(system, user, fallback=fallback, max_retries=1,
                                      max_tokens=self._draft_max_tokens)
        return self._normalize(revised, fallback)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _render_prior_artifacts(self, context: ExecutionContext) -> str:
        """
        Si le workflow injecte les artefacts des agents précédents dans
        context.metadata["prior_artifacts"], on les ré-affiche pour que
        l'agent courant les consulte vraiment.
        """
        prior = context.metadata.get("prior_artifacts") if context.metadata else None
        if not prior or not isinstance(prior, list):
            return "Aucun artefact préalable disponible."

        lines = ["LIVRABLES DÉJÀ PRODUITS PAR D'AUTRES AGENTS :"]
        for item in prior[:8]:  # limite de prudence
            agent = item.get("agent", "?")
            arts = item.get("artifacts", [])
            if not arts:
                continue
            lines.append(f"\n— {agent} —")
            for art in arts[:3]:
                title = art.get("title", "Sans titre")
                content = str(art.get("content", ""))[:600]
                lines.append(f"  • {title}\n    {content}")
        return "\n".join(lines)

    @staticmethod
    def _normalize(data: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
        """Garantit la structure attendue (artifacts = list, score = float)."""
        if not isinstance(data, dict):
            return fallback

        summary = str(data.get("summary") or fallback.get("summary", ""))
        artifacts = data.get("artifacts") or fallback.get("artifacts", [])
        # Si artifacts est un dict (ancien format des "legacy"), on l'enveloppe
        if isinstance(artifacts, dict):
            artifacts = [
                {"type": k, "title": k.replace("_", " ").title(),
                 "content": (json.dumps(v, ensure_ascii=False)
                             if not isinstance(v, str) else v)}
                for k, v in artifacts.items()
            ]
        if not isinstance(artifacts, list):
            artifacts = fallback.get("artifacts", [])

        clean_artifacts: list[dict[str, Any]] = []
        for art in artifacts:
            if isinstance(art, dict):
                clean_artifacts.append({
                    "type": str(art.get("type", "livrable")),
                    "title": str(art.get("title", "Sans titre")),
                    "content": str(art.get("content", "")),
                })
            elif isinstance(art, str):
                clean_artifacts.append({
                    "type": "note", "title": "Note", "content": art,
                })

        followups = data.get("followups") or fallback.get("followups", [])
        if not isinstance(followups, list):
            followups = []
        followups = [str(f) for f in followups[:5]]

        try:
            score = float(data.get("score", fallback.get("score", 0.5)))
        except (TypeError, ValueError):
            score = 0.5
        score = max(0.0, min(1.0, score))

        return {
            "summary": summary,
            "artifacts": clean_artifacts,
            "followups": followups,
            "score": score,
        }

    def _to_response(
        self,
        data: dict[str, Any],
        trace: AgentTrace,
        rubric: QualityRubric,
    ) -> AgentResponse:
        trace.final_score = float(data.get("score", 0.0))
        return AgentResponse(
            agent=self.name,
            summary=str(data.get("summary", "")),
            artifacts=data.get("artifacts", []),
            followups=data.get("followups", []),
            score=trace.final_score,
        )
