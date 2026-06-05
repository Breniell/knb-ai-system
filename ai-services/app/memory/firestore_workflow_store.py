import asyncio
from typing import Any

from firebase_admin import firestore

from app.core.firebase import get_firestore_client
from app.core.logging import get_logger
from app.core.settings import settings


class FirestoreWorkflowStore:
    def __init__(self) -> None:
        self.logger = get_logger("firestore-workflows")
        self.client = get_firestore_client()
        self.collection_name = settings.firestore_workflow_collection

    def enabled(self) -> bool:
        return self.client is not None

    async def save_execution(
        self,
        *,
        workflow_id: str,
        user_id: str,
        project_id: str,
        task_id: str | None,
        input_text: str,
        status: str,
        selected_agents: list[str],
        plan: list[dict[str, Any]],
        responses: list[dict[str, Any]],
        timeline: list[dict[str, Any]],
        errors: list[str],
        metadata: dict[str, Any],
    ) -> None:
        if self.client is None:
            return

        payload = {
            "workflowId": workflow_id,
            "workflow_id": workflow_id,
            "userId": user_id,
            "projectId": project_id,
            "taskId": task_id,
            "input": input_text,
            "status": status,
            "selectedAgents": selected_agents,
            "plan": plan,
            "responses": responses,
            "timeline": timeline,
            "errors": errors,
            "metadata": metadata,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }

        await asyncio.to_thread(self._save_sync, workflow_id, user_id, payload, status)

    async def update_execution_status(self, workflow_id: str, status: str) -> None:
        """Lightweight status-only update (avoids re-sending large payloads)."""
        if self.client is None:
            return
        await asyncio.to_thread(self._update_status_sync, workflow_id, status)

    def _update_status_sync(self, workflow_id: str, status: str) -> None:
        try:
            ref = self.client.collection(self.collection_name).document(workflow_id)
            ref.update({"status": status, "updatedAt": firestore.SERVER_TIMESTAMP})
        except Exception as exc:
            self.logger.warning(
                "firestore.status_update_failed workflow=%s reason=%s", workflow_id, exc
            )

    def _save_sync(self, workflow_id: str, user_id: str, payload: dict[str, Any], status: str) -> None:
        try:
            root_ref = self.client.collection(self.collection_name).document(workflow_id)
            user_ref = (
                self.client.collection("users")
                .document(user_id)
                .collection(self.collection_name)
                .document(workflow_id)
            )
            existing = root_ref.get()
            if not existing.exists:
                payload = {**payload, "createdAt": firestore.SERVER_TIMESTAMP}

            batch = self.client.batch()
            batch.set(root_ref, payload, merge=True)
            batch.set(user_ref, payload, merge=True)
            batch.commit()
        except Exception as exc:
            self.logger.warning("firestore.workflow_save_failed workflow=%s status=%s reason=%s", workflow_id, status, exc)
