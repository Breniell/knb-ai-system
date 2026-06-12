"""
tools/scheduler.py — Scheduler d'auto-formation autonome des agents (v2).

Tourne en tâche asyncio dédiée depuis le démarrage de l'app FastAPI.

Cycles d'exécution :
  1. BOOTSTRAP (30s après démarrage) : premier cycle de formation ciblé.
  2. LOOP (toutes les 24h) : re-vérifie les topics obsolètes et relance.
  3. FORCE : endpoint /api/learning/retrain peut déclencher un cycle immédiat.

Sources d'apprentissage utilisées :
  - learning_resources.py : curriculum curated par agent (docs officielles,
    Google Digital Garage, Meta Blueprint, HubSpot Academy, OHADA, MDN, etc.)
  - learning_engine_v2.py : scraping + synthèse LLM + stockage Firestore
  - learning_engine.py (original) : web search généraliste + cache

L'agent FORME ET s'AMÉLIORE sans intervention humaine.
Non-bloquant : toute erreur est loggée et avalée, jamais propagée.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("scheduler")

_BOOTSTRAP_DELAY_SECONDS = 30
_LOOP_INTERVAL_HOURS = 24
_PER_AGENT_DELAY_SECONDS = 5  # pause entre agents pour les rate limits
_MAX_AGENTS_PER_CYCLE = 3     # réduit de 5 → économise les quotas gratuits
_TOPICS_PER_AGENT = 2         # réduit de 3 → idem


class TrainingScheduler:
    """Singleton de formation continue des agents."""

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._running = False
        self.last_cycle_summary: dict[str, Any] = {}
        self.total_cycles: int = 0
        self.total_insights_stored: int = 0

    async def start(self) -> None:
        if self._task is not None:
            return
        try:
            from app.core.settings import settings
            if not settings.web_learning_enabled:
                logger.info("scheduler.disabled (WEB_LEARNING_ENABLED=false)")
                return
        except Exception:
            pass
        self._stop_event.clear()
        self._task = asyncio.create_task(self._loop(), name="knb-training-scheduler")
        logger.info(
            "scheduler.started bootstrap=%ds interval=%dh max_agents=%d topics_per_agent=%d",
            _BOOTSTRAP_DELAY_SECONDS, _LOOP_INTERVAL_HOURS,
            _MAX_AGENTS_PER_CYCLE, _TOPICS_PER_AGENT,
        )

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop_event.set()
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        logger.info("scheduler.stopped total_cycles=%d insights=%d",
                    self.total_cycles, self.total_insights_stored)

    async def trigger_now(self, agent_name: str | None = None, force: bool = False) -> dict[str, Any]:
        """Déclenche un cycle immédiat (depuis l'API /learning/retrain)."""
        return await self._run_cycle(agent_filter=agent_name, force=force)

    # ── Boucle interne ──────────────────────────────────────────────────────

    async def _loop(self) -> None:
        try:
            await asyncio.sleep(_BOOTSTRAP_DELAY_SECONDS)
            if await self._bootstrap_needed():
                await self._run_cycle(force=False)
            interval_sec = _LOOP_INTERVAL_HOURS * 3600
            while not self._stop_event.is_set():
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=interval_sec)
                except asyncio.TimeoutError:
                    pass
                if self._stop_event.is_set():
                    return
                await self._run_cycle(force=False)
        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.error("scheduler.loop.crashed: %s", exc)

    async def _run_cycle(
        self,
        agent_filter: str | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        self._running = True
        cycle_start = datetime.now(timezone.utc)
        report: dict[str, Any] = {
            "started_at": cycle_start.isoformat(),
            "trained": [],
            "skipped": [],
            "failed": [],
            "insights_total": 0,
        }

        try:
            llm = self._get_llm()
            if llm is None or not llm.enabled():
                logger.info("scheduler.cycle.skip (no LLM configured)")
                report["skipped"] = ["all — LLM non configuré"]
                return report

            from app.tools.learning_resources import ALL_CURRICULA

            # Sélectionne les agents à former
            agent_names = list(ALL_CURRICULA.keys())
            if agent_filter and agent_filter in ALL_CURRICULA:
                agent_names = [agent_filter]
            elif not agent_filter:
                agent_names = agent_names[:_MAX_AGENTS_PER_CYCLE]

            logger.info("scheduler.cycle.start agents=%s force=%s", agent_names, force)

            from app.tools.learning_engine_v2 import train_agent_on_curriculum

            for agent_name in agent_names:
                if self._stop_event.is_set():
                    break
                try:
                    agent_report = await train_agent_on_curriculum(
                        agent_name=agent_name,
                        llm=llm,
                        force=force,
                        max_topics=_TOPICS_PER_AGENT,
                    )
                    if agent_report.get("ok"):
                        report["trained"].append(agent_name)
                        insights = agent_report.get("insights_total", 0)
                        report["insights_total"] += insights
                        self.total_insights_stored += insights
                        logger.info(
                            "scheduler.agent_trained agent=%s insights=%d topics=%s",
                            agent_name, insights, agent_report.get("trained_topics", []),
                        )
                    else:
                        report["failed"].append({
                            "agent": agent_name,
                            "error": agent_report.get("error", "unknown"),
                        })
                except Exception as exc:
                    logger.warning("scheduler.agent_failed agent=%s: %s", agent_name, exc)
                    report["failed"].append({"agent": agent_name, "error": str(exc)[:120]})

                await asyncio.sleep(_PER_AGENT_DELAY_SECONDS)

            await self._persist_cycle_timestamp()

        except Exception as exc:
            logger.error("scheduler.cycle.error: %s", exc)
            report["error"] = str(exc)[:200]
        finally:
            self._running = False
            self.total_cycles += 1
            elapsed = (datetime.now(timezone.utc) - cycle_start).total_seconds()
            report["elapsed_seconds"] = round(elapsed, 1)
            self.last_cycle_summary = report
            logger.info(
                "scheduler.cycle.done trained=%d skipped=%d failed=%d insights=%d time=%.1fs",
                len(report["trained"]),
                len(report["skipped"]) if isinstance(report["skipped"], list) else 1,
                len(report["failed"]),
                report["insights_total"],
                elapsed,
            )
        return report

    async def _bootstrap_needed(self) -> bool:
        """Return False (et logue) si un cycle s'est terminé il y a moins de _LOOP_INTERVAL_HOURS."""
        try:
            from app.core.firebase import get_firestore_client
            db = get_firestore_client()
            if db is None:
                return True  # Firestore indisponible → comportement normal
            doc_ref = db.collection("schedulerState").document("training")
            doc = await asyncio.to_thread(doc_ref.get)
            if not doc.exists:
                return True
            last_at = doc.to_dict().get("last_cycle_at")
            if last_at is None:
                return True
            age_hours = (datetime.now(timezone.utc) - last_at).total_seconds() / 3600
            if age_hours < _LOOP_INTERVAL_HOURS:
                logger.info(
                    "scheduler.bootstrap_skipped last_cycle=%s (%.1fh ago)",
                    last_at.isoformat(), age_hours,
                )
                return False
            return True
        except Exception as exc:
            logger.warning("scheduler.bootstrap_check_failed: %s", exc)
            return True  # Non-fatal : on exécute le bootstrap normalement

    async def _persist_cycle_timestamp(self) -> None:
        """Écrit l'horodatage du dernier cycle dans Firestore (collection schedulerState)."""
        try:
            from app.core.firebase import get_firestore_client
            db = get_firestore_client()
            if db is None:
                return
            doc_ref = db.collection("schedulerState").document("training")
            await asyncio.to_thread(doc_ref.set, {"last_cycle_at": datetime.now(timezone.utc)})
        except Exception as exc:
            logger.warning("scheduler.persist_timestamp_failed: %s", exc)

    def _get_llm(self):
        try:
            from app.core.llm import LlmClient
            return LlmClient()
        except Exception:
            return None

    @property
    def running(self) -> bool:
        return self._running

    def status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "total_cycles": self.total_cycles,
            "total_insights_stored": self.total_insights_stored,
            "last_cycle": self.last_cycle_summary,
        }


# Singleton
scheduler = TrainingScheduler()
