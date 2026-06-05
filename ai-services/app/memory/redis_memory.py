"""Short-term memory backed by Firestore (replaces Redis).

TTL is simulated via an `expiresAt` timestamp field.
Documents whose `expiresAt` has passed are treated as expired and deleted.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any

from app.core.firebase import get_firestore_client
from app.core.logging import get_logger

_COLLECTION = "shortTermMemory"
_logger = get_logger("redis-memory")


class RedisMemory:
    def __init__(self) -> None:
        self._client = get_firestore_client()

    def _enabled(self) -> bool:
        return self._client is not None

    async def save_short_term(
        self, key: str, payload: dict[str, Any], ttl_seconds: int = 3600
    ) -> None:
        if not self._enabled():
            return
        expires_at = datetime.now(timezone.utc).timestamp() + ttl_seconds
        doc = {"data": payload, "expiresAt": expires_at}
        await asyncio.to_thread(
            self._client.collection(_COLLECTION).document(key).set, doc
        )

    async def get_short_term(self, key: str) -> dict[str, Any] | None:
        if not self._enabled():
            return None
        try:
            snap = await asyncio.to_thread(
                self._client.collection(_COLLECTION).document(key).get
            )
            if not snap.exists:
                return None
            data = snap.to_dict()
            expires_at = data.get("expiresAt", 0)
            if datetime.now(timezone.utc).timestamp() > expires_at:
                await asyncio.to_thread(
                    self._client.collection(_COLLECTION).document(key).delete
                )
                return None
            return data.get("data")
        except Exception as exc:
            _logger.warning("short_term_get_failed key=%s reason=%s", key, exc)
            return None

    async def delete_expired(self) -> int:
        """Delete all documents whose expiresAt has passed. Returns count deleted."""
        if not self._enabled():
            return 0
        now = datetime.now(timezone.utc).timestamp()
        try:
            docs = await asyncio.to_thread(
                lambda: list(
                    self._client.collection(_COLLECTION)
                    .where("expiresAt", "<", now)
                    .stream()
                )
            )
            batch = self._client.batch()
            for doc in docs:
                batch.delete(doc.reference)
            await asyncio.to_thread(batch.commit)
            return len(docs)
        except Exception as exc:
            _logger.warning("delete_expired_failed reason=%s", exc)
            return 0
