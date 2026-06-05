"""
memory/vector_memory.py — Mémoire sémantique v2.

Priorité :
  1. Qdrant (QDRANT_URL configuré) + Gemini embeddings 768 dim
     → Vraie recherche sémantique sur tous les artefacts passés
  2. Firestore + TF-IDF scikit-learn (fallback si Qdrant absent)
     → Recherche par similarité de mots (acceptable)

NOUVELLE FONCTIONNALITÉ : indexation des ARTEFACTS (pas seulement l'input).
Chaque livrable produit par un agent (code, devis, plan, design spec) est
indexé dans Qdrant. Les agents peuvent ensuite rechercher "travaux similaires
passés" via l'outil search_past_work pendant leur phase RESEARCH.

Exemple :
  DevFrontendAgent cherche "composant Button TypeScript" → trouve le Button.tsx
  produit il y a 3 semaines → l'adapte pour le nouveau client.

  CommercialAgent cherche "devis site vitrine PME" → trouve le devis de mars
  → l'adapte avec les nouvelles infos client.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

logger = logging.getLogger("vector-memory")

# ── Constantes Qdrant ──────────────────────────────────────────────────────────
_COLLECTION_ARTIFACTS = "knb_artifacts"   # livrables passés
_COLLECTION_KNOWLEDGE  = "knb_knowledge"  # connaissances d'apprentissage
_GEMINI_DIM = 768                         # text-embedding-004

# ── Fallback Firestore collection ──────────────────────────────────────────────
_FIRESTORE_COLLECTION = "semanticMemory"


# ═══════════════════════════════════════════════════════════════════════════════
# Similarité TF-IDF (fallback sans Qdrant)
# ═══════════════════════════════════════════════════════════════════════════════

def _jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as _cos
    import numpy as np

    def _tfidf_similarity(query: str, corpus: list[str]) -> list[float]:
        if not corpus:
            return []
        try:
            vec = TfidfVectorizer(analyzer="word", min_df=1, max_features=5000)
            mat = vec.fit_transform([query] + corpus)
            return _cos(mat[0:1], mat[1:])[0].tolist()
        except Exception:
            tq = query.lower().split()
            return [_jaccard(tq, c.lower().split()) for c in corpus]

except ImportError:
    def _tfidf_similarity(query: str, corpus: list[str]) -> list[float]:
        tq = query.lower().split()
        return [_jaccard(tq, c.lower().split()) for c in corpus]


# ═══════════════════════════════════════════════════════════════════════════════
# Client Qdrant
# ═══════════════════════════════════════════════════════════════════════════════

class _QdrantClient:
    """Wrapper léger autour du client Qdrant REST."""

    def __init__(self, url: str, api_key: str | None) -> None:
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import (
                Distance, VectorParams, PointStruct,
            )
            self._client = QdrantClient(url=url, api_key=api_key, timeout=10)
            self._PointStruct = PointStruct
            self._Distance = Distance
            self._VectorParams = VectorParams
            self._ok = True
            logger.info("Qdrant connecté : %s", url)
        except Exception as e:
            logger.warning("Qdrant indisponible : %s", e)
            self._ok = False

    def ready(self) -> bool:
        return self._ok

    def ensure_collection(self, name: str, size: int = _GEMINI_DIM) -> bool:
        if not self._ok:
            return False
        try:
            existing = [c.name for c in self._client.get_collections().collections]
            if name not in existing:
                self._client.create_collection(
                    collection_name=name,
                    vectors_config=self._VectorParams(
                        size=size, distance=self._Distance.COSINE,
                    ),
                )
                logger.info("Qdrant collection créée : %s (dim=%d)", name, size)
            return True
        except Exception as e:
            logger.warning("Qdrant ensure_collection failed : %s", e)
            return False

    def upsert(self, collection: str, point_id: str, vector: list[float],
               payload: dict[str, Any]) -> bool:
        if not self._ok:
            return False
        try:
            self._client.upsert(
                collection_name=collection,
                points=[self._PointStruct(id=self._hash_id(point_id),
                                          vector=vector, payload=payload)],
            )
            return True
        except Exception as e:
            logger.warning("Qdrant upsert failed : %s", e)
            return False

    def search(self, collection: str, vector: list[float], limit: int = 5,
               filter_dict: dict | None = None) -> list[dict[str, Any]]:
        if not self._ok:
            return []
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            qfilter = None
            if filter_dict:
                conditions = [
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filter_dict.items()
                ]
                qfilter = Filter(must=conditions)
            results = self._client.search(
                collection_name=collection,
                query_vector=vector,
                limit=limit,
                query_filter=qfilter,
                with_payload=True,
            )
            return [{"score": r.score, "payload": r.payload} for r in results]
        except Exception as e:
            logger.warning("Qdrant search failed : %s", e)
            return []

    @staticmethod
    def _hash_id(text: str) -> str:
        """Qdrant accepte des UUID ou des entiers. On hache en int 64-bit."""
        return str(int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**63))


# ═══════════════════════════════════════════════════════════════════════════════
# VectorMemory (interface publique)
# ═══════════════════════════════════════════════════════════════════════════════

class VectorMemory:
    """
    Mémoire sémantique unifiée.
    Tente Qdrant + Gemini embeddings en priorité, bascule sur Firestore + TF-IDF.
    """

    def __init__(self) -> None:
        self._qdrant: _QdrantClient | None = None
        self._firestore_client = None
        self._embedder = None
        self._init()

    def _init(self) -> None:
        # Qdrant
        try:
            from app.core.settings import settings
            qdrant_url = getattr(settings, "qdrant_url", None)
            qdrant_key = getattr(settings, "qdrant_api_key", None)
            if qdrant_url and "qdrant" in str(qdrant_url):
                q = _QdrantClient(qdrant_url, qdrant_key)
                if q.ready():
                    self._qdrant = q
                    self._qdrant.ensure_collection(_COLLECTION_ARTIFACTS)
                    self._qdrant.ensure_collection(_COLLECTION_KNOWLEDGE)
        except Exception as e:
            logger.debug("Qdrant init skipped : %s", e)

        # Gemini embeddings
        try:
            from app.core.settings import settings
            if settings.gemini_api_key:
                import google.generativeai as genai
                genai.configure(api_key=settings.gemini_api_key)
                self._embedder = genai
                logger.info("VectorMemory : Gemini embeddings activés")
        except Exception as e:
            logger.debug("Gemini embedder skipped : %s", e)

        # Firestore (fallback)
        try:
            from app.core.firebase import get_firestore_client
            self._firestore_client = get_firestore_client()
        except Exception:
            pass

    # ── Embeddings ──────────────────────────────────────────────────────────

    def _embed(self, text: str) -> list[float] | None:
        if self._embedder is None:
            return None
        try:
            resp = self._embedder.embed_content(
                model="models/text-embedding-004",
                content=text[:6000],
                task_type="retrieval_document",
            )
            emb = resp.get("embedding") if isinstance(resp, dict) else resp.embedding
            return list(emb) if emb else None
        except Exception as e:
            logger.debug("embed failed : %s", e)
            return None

    # ── Indexation des artefacts ────────────────────────────────────────────

    def index_artifact(
        self,
        *,
        artifact_id: str | None = None,
        agent: str,
        title: str,
        content: str,
        artifact_type: str,
        workflow_id: str,
        project_id: str,
        input_preview: str,
    ) -> str:
        """
        Indexe un livrable produit par un agent.
        Appelé automatiquement après chaque workflow réussi.
        """
        doc_id = artifact_id or str(uuid4())
        payload = {
            "id": doc_id,
            "agent": agent,
            "title": title,
            "content": content[:2000],   # tronqué pour le payload Qdrant
            "type": artifact_type,
            "workflow_id": workflow_id,
            "project_id": project_id,
            "input_preview": input_preview[:200],
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        }
        searchable_text = f"{title}\n{input_preview}\n{content[:500]}"

        # Qdrant path
        if self._qdrant:
            vector = self._embed(searchable_text)
            if vector:
                self._qdrant.upsert(_COLLECTION_ARTIFACTS, doc_id, vector, payload)
                return doc_id

        # Firestore fallback
        if self._firestore_client:
            try:
                self._firestore_client.collection("artifactMemory").document(doc_id).set(
                    {**payload, "text": searchable_text}
                )
            except Exception as e:
                logger.warning("index_artifact firestore failed : %s", e)
        return doc_id

    def search_past_work(
        self,
        query: str,
        limit: int = 5,
        agent: str | None = None,
        project_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Recherche dans les livrables passés. Utilisé par l'outil search_past_work.
        Retourne des dicts avec {score, agent, title, content, type, input_preview}.
        """
        filter_dict: dict[str, Any] = {}
        if agent:
            filter_dict["agent"] = agent
        if project_id:
            filter_dict["project_id"] = project_id

        # Qdrant path
        if self._qdrant:
            vector = self._embed(query)
            if vector:
                results = self._qdrant.search(
                    _COLLECTION_ARTIFACTS, vector, limit=limit,
                    filter_dict=filter_dict or None,
                )
                return [
                    {
                        "score": r["score"],
                        "agent": r["payload"].get("agent", ""),
                        "title": r["payload"].get("title", ""),
                        "content": r["payload"].get("content", ""),
                        "type": r["payload"].get("type", ""),
                        "input_preview": r["payload"].get("input_preview", ""),
                    }
                    for r in results
                ]

        # Firestore + TF-IDF fallback
        return self._firestore_search(query, limit, filter_dict)

    def _firestore_search(
        self, query: str, limit: int, filters: dict,
    ) -> list[dict[str, Any]]:
        if not self._firestore_client:
            return []
        try:
            ref = self._firestore_client.collection("artifactMemory")
            if filters.get("agent"):
                ref = ref.where("agent", "==", filters["agent"])
            docs = list(ref.limit(200).stream())
            if not docs:
                return []
            texts = [d.to_dict().get("text", "") for d in docs]
            scores = _tfidf_similarity(query, texts)
            ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)[:limit]
            return [
                {
                    "score": float(s),
                    "agent": d.to_dict().get("agent", ""),
                    "title": d.to_dict().get("title", ""),
                    "content": d.to_dict().get("content", ""),
                    "type": d.to_dict().get("type", ""),
                    "input_preview": d.to_dict().get("input_preview", ""),
                }
                for s, d in ranked
            ]
        except Exception as e:
            logger.warning("firestore_search failed : %s", e)
            return []

    # ── Compatibilité rétro (orchestrator/service.py existant) ─────────────

    def save_semantic_memory(self, text: str, payload: dict[str, Any]) -> str:
        """Compatibilité avec l'orchestrateur existant."""
        doc_id = str(uuid4())
        if self._qdrant:
            vector = self._embed(text)
            if vector:
                self._qdrant.upsert(
                    _COLLECTION_ARTIFACTS, doc_id, vector,
                    {"text": text[:2000], **payload},
                )
                return doc_id
        if self._firestore_client:
            try:
                self._firestore_client.collection(_FIRESTORE_COLLECTION).document(doc_id).set(
                    {"id": doc_id, "text": text, **payload}
                )
            except Exception:
                pass
        return doc_id

    def search(
        self, query: str, limit: int = 5, project_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Compatibilité avec l'orchestrateur existant."""
        results = self.search_past_work(query, limit=limit, project_id=project_id)
        return [{"score": r["score"], "payload": {"text": r.get("content", "")}}
                for r in results]

    async def search_async(
        self, query: str, limit: int = 5, project_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self.search, query, limit, project_id)
