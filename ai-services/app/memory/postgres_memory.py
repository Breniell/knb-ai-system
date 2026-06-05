"""Persistent history backed by Firestore (replaces PostgreSQL).

Collections:
  aiMemoryHistory  — execution history per agent
  aiWorkflowSteps  — per-step workflow records
"""

import asyncio
from typing import Any
from uuid import uuid4

from firebase_admin import firestore

from app.core.firebase import get_firestore_client
from app.core.logging import get_logger

_logger = get_logger("postgres-memory")


class PostgresMemory:
    def __init__(self) -> None:
        self._client = get_firestore_client()

    def _enabled(self) -> bool:
        return self._client is not None

    async def ensure_schema(self) -> None:
        """No-op: Firestore is schemaless."""
        return

    async def save_history(
        self,
        memory_id: str,
        project_id: str,
        task_id: str | None,
        user_id: str,
        agent_name: str,
        input_text: str,
        output_text: str,
        metadata: dict[str, Any],
    ) -> None:
        if not self._enabled():
            return
        doc = {
            "id": memory_id,
            "projectId": project_id,
            "taskId": task_id,
            "userId": user_id,
            "agentName": agent_name,
            "inputText": input_text,
            "outputText": output_text,
            "metadata": metadata,
            "createdAt": firestore.SERVER_TIMESTAMP,
        }
        try:
            await asyncio.to_thread(
                self._client.collection("aiMemoryHistory")
                .document(memory_id)
                .set,
                doc,
            )
        except Exception as exc:
            _logger.warning("save_history_failed id=%s reason=%s", memory_id, exc)

    async def save_step(
        self,
        step_id: str,
        workflow_id: str,
        node_name: str,
        success: bool,
        details: dict[str, Any],
    ) -> None:
        if not self._enabled():
            return
        doc = {
            "id": step_id,
            "workflowId": workflow_id,
            "nodeName": node_name,
            "success": success,
            "details": details,
            "createdAt": firestore.SERVER_TIMESTAMP,
        }
        try:
            await asyncio.to_thread(
                self._client.collection("aiWorkflowSteps")
                .document(step_id)
                .set,
                doc,
            )
        except Exception as exc:
            _logger.warning("save_step_failed id=%s reason=%s", step_id, exc)

    async def get_workflow_steps(self, workflow_id: str) -> list[dict[str, Any]]:
        if not self._enabled():
            return []
        try:
            docs = await asyncio.to_thread(
                lambda: list(
                    self._client.collection("aiWorkflowSteps")
                    .where("workflowId", "==", workflow_id)
                    .stream()
                )
            )
            return [d.to_dict() for d in docs]
        except Exception as exc:
            _logger.warning("get_workflow_steps_failed wf=%s reason=%s", workflow_id, exc)
            return []
