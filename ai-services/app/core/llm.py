"""
core/llm.py — Client LLM multi-provider robuste pour KNB AI System.

Améliorations clés vs version originale :
1. JSON mode activé pour Groq, Gemini, Mistral (pas seulement Groq).
2. Réparation JSON automatique (fences, commentaires, trailing commas, extraction
   du premier objet/tableau bien balancé d'un texte plus large).
3. Retry intelligent en cas de JSON invalide (rappelle le LLM avec un feedback
   d'erreur explicite avant de tomber en fallback).
4. Embeddings RÉELS via Gemini text-embedding-004 (768 dim, gratuit 1500/min).
   Plus jamais d'embeddings hashés qui polluent Qdrant.
5. Méthode generate_with_tools() pour la boucle ReAct (tool use).
6. Métriques internes pour debug : provider, calls_count, json_failures.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

from app.core.settings import settings

logger = logging.getLogger(__name__)

# Nombre de réessais sur erreurs transitoires (429, timeouts, 5xx) avant abandon.
_TRANSIENT_MAX_RETRIES = 3


def _retry_after_seconds(exc: Exception) -> float | None:
    """Extrait un délai Retry-After si le provider en fournit un (sinon None)."""
    # En-tête HTTP exposé par certains SDK (groq/openai exposent .response)
    resp = getattr(exc, "response", None)
    headers = getattr(resp, "headers", None)
    if headers:
        for key in ("retry-after", "Retry-After", "x-ratelimit-reset-tokens"):
            val = headers.get(key) if hasattr(headers, "get") else None
            if val:
                try:
                    return float(str(val).rstrip("s"))
                except (TypeError, ValueError):
                    pass
    # Repli : cherche un nombre de secondes dans le message ("try again in 2.5s")
    m = re.search(r"(\d+(?:\.\d+)?)\s*s", str(exc))
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Réparation JSON
# ═══════════════════════════════════════════════════════════════════════════════

_JSON_FENCE_RE = re.compile(r"^\s*```(?:json|JSON)?\s*|\s*```\s*$", re.MULTILINE)
_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")
_LINE_COMMENT_RE = re.compile(r"//[^\n]*")
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def _extract_first_json_blob(text: str) -> str | None:
    """Extrait le premier objet ou tableau JSON bien balancé du texte."""
    if not text:
        return None

    stack: list[str] = []
    start_idx: int | None = None
    in_string = False
    escape = False

    for i, ch in enumerate(text):
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in "{[":
            if not stack:
                start_idx = i
            stack.append(ch)
        elif ch in "}]" and stack:
            opener = stack.pop()
            if (opener == "{" and ch == "}") or (opener == "[" and ch == "]"):
                if not stack and start_idx is not None:
                    return text[start_idx : i + 1]
            else:
                # Mismatch — abort and let parsing fail
                return None
    return None


def repair_and_parse_json(raw: str) -> dict[str, Any] | None:
    """Plusieurs stratégies de récupération avant abandon. Public."""
    if not raw:
        return None

    text = raw.strip()
    text = _JSON_FENCE_RE.sub("", text).strip()

    # Tentative 1 : parsing direct
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {"data": parsed}
    except json.JSONDecodeError:
        pass

    # Tentative 2 : nettoyage agressif
    cleaned = _BLOCK_COMMENT_RE.sub("", text)
    cleaned = _LINE_COMMENT_RE.sub("", cleaned)
    cleaned = _TRAILING_COMMA_RE.sub(r"\1", cleaned)
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else {"data": parsed}
    except json.JSONDecodeError:
        pass

    # Tentative 3 : extraction du premier blob valide
    blob = _extract_first_json_blob(cleaned)
    if blob:
        try:
            parsed = json.loads(blob)
            return parsed if isinstance(parsed, dict) else {"data": parsed}
        except json.JSONDecodeError:
            pass

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Client LLM
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class LlmMetrics:
    """Compteurs pour debug et observabilité."""
    calls: int = 0
    json_calls: int = 0
    json_failures: int = 0
    retries: int = 0
    embed_calls: int = 0
    by_provider: dict[str, int] = field(default_factory=dict)


class LlmClient:
    """
    Priorité : Groq → Gemini → Mistral → OpenRouter → Anthropic → Fallback.
    Embeddings : Gemini text-embedding-004 (768 dim, gratuit).
    """

    def __init__(self) -> None:
        self._client: Any = None
        self._provider: str = "fallback"
        self._model: str = ""
        # Provider de secours (failover) — pris quand le principal sature (429).
        self._secondary: dict[str, Any] | None = None
        # Embedder peut être différent du provider principal (toujours Gemini si dispo)
        self._embedder: Any = None
        self._embed_dim: int = 768
        self.metrics = LlmMetrics()
        self._init_client()
        self._init_embedder()
        self._init_secondary()

    # ── Initialisation ──────────────────────────────────────────────────────

    def _init_client(self) -> None:
        if settings.groq_api_key:
            try:
                from groq import Groq
                self._client = Groq(api_key=settings.groq_api_key)
                self._provider = "groq"
                self._model = "llama-3.3-70b-versatile"
                # Étagement : modèle léger très rapide (limites + élevées) pour les
                # appels auxiliaires (planning de recherche, auto-critique), modèle
                # puissant réservé au raisonnement et aux livrables.
                self._groq_models = {
                    "heavy": "llama-3.3-70b-versatile",
                    "medium": "llama-3.3-70b-versatile",
                    "light": "llama-3.1-8b-instant",
                }
                logger.info("[LLM] Groq prêt (heavy: llama-3.3-70b / light: llama-3.1-8b-instant)")
                return
            except Exception as e:
                logger.warning("Groq indisponible: %s", e)

        if settings.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.gemini_api_key)
                self._client = genai
                self._provider = "gemini"
                self._model = "gemini-2.0-flash-exp"
                logger.info("[LLM] Google Gemini 2.0 Flash prêt")
                return
            except Exception as e:
                logger.warning("Gemini indisponible: %s", e)

        if settings.mistral_api_key:
            try:
                from mistralai import Mistral
                self._client = Mistral(api_key=settings.mistral_api_key)
                self._provider = "mistral"
                self._model = "mistral-small-latest"
                logger.info("[LLM] Mistral Small prêt")
                return
            except Exception as e:
                logger.warning("Mistral indisponible: %s", e)

        if settings.openrouter_api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=settings.openrouter_api_key,
                )
                self._provider = "openrouter"
                # Modèle par défaut (le plus capable gratuit disponible)
                self._model = "meta-llama/llama-3.3-70b-instruct:free"
                self._openrouter_models = {
                    "heavy":  "meta-llama/llama-3.3-70b-instruct:free",  # raisonnement complexe
                    "medium": "google/gemini-flash-1.5-8b:free",         # tâches intermédiaires
                    "light":  "mistralai/mistral-7b-instruct:free",      # classification, routing
                }
                logger.info("[LLM] OpenRouter prêt (heavy: llama-3.3-70b / medium: gemini-flash-8b / light: mistral-7b)")
                return
            except Exception as e:
                logger.warning("OpenRouter indisponible: %s", e)

        if settings.anthropic_api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
                self._provider = "anthropic"
                self._model = "claude-sonnet-4-20250514"
                logger.info("[LLM] Anthropic Claude Sonnet 4 prêt")
                return
            except Exception as e:
                logger.warning("Anthropic indisponible: %s", e)

        logger.warning(
            "[LLM] AUCUN provider configuré → fallbacks déterministes. "
            "Définissez GROQ_API_KEY ou GEMINI_API_KEY dans .env (gratuits)."
        )

    def _init_embedder(self) -> None:
        """Embeddings réels via Gemini si disponible, sinon désactivé."""
        if settings.gemini_api_key:
            try:
                import google.generativeai as genai
                # genai déjà configuré si provider principal == gemini, sinon configurer
                if self._provider != "gemini":
                    genai.configure(api_key=settings.gemini_api_key)
                self._embedder = genai
                self._embed_dim = 768  # text-embedding-004
                logger.info("[Embeddings] Gemini text-embedding-004 (768 dim) prêt")
                return
            except Exception as e:
                logger.warning("Embedder Gemini indisponible: %s", e)
        logger.info(
            "[Embeddings] Aucun embedder réel configuré. "
            "VectorMemory sera désactivée. Pour activer la mémoire sémantique, "
            "ajoutez GEMINI_API_KEY dans .env."
        )

    def _init_secondary(self) -> None:
        """Configure un provider de secours (failover) distinct du principal.

        But : sur plan gratuit, quand le provider principal (Groq) atteint sa
        limite req/min ou tokens/min, on bascule l'appel sur un second provider
        au lieu d'échouer. Cumule les quotas gratuits et garantit la continuité
        sur les gros projets. Priorité du secours : Gemini → Mistral → OpenRouter.
        """
        # Gemini en secours (idéal : déjà configuré pour les embeddings)
        if self._provider != "gemini" and settings.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.gemini_api_key)
                self._secondary = {"provider": "gemini", "client": genai, "model": "gemini-2.0-flash-exp"}
                logger.info("[LLM] Secours configuré : Gemini 2.0 Flash (failover si %s sature)", self._provider)
                return
            except Exception as e:
                logger.warning("Secours Gemini indisponible: %s", e)
        # Mistral en secours
        if self._provider != "mistral" and settings.mistral_api_key:
            try:
                from mistralai import Mistral
                self._secondary = {"provider": "mistral", "client": Mistral(api_key=settings.mistral_api_key), "model": "mistral-small-latest"}
                logger.info("[LLM] Secours configuré : Mistral Small")
                return
            except Exception as e:
                logger.warning("Secours Mistral indisponible: %s", e)
        # OpenRouter en secours
        if self._provider != "openrouter" and settings.openrouter_api_key:
            try:
                from openai import OpenAI
                self._secondary = {
                    "provider": "openrouter",
                    "client": OpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.openrouter_api_key),
                    "model": "meta-llama/llama-3.3-70b-instruct:free",
                }
                logger.info("[LLM] Secours configuré : OpenRouter llama-3.3-70b:free")
                return
            except Exception as e:
                logger.warning("Secours OpenRouter indisponible: %s", e)

    # ── API publique ────────────────────────────────────────────────────────

    def enabled(self) -> bool:
        return self._provider != "fallback"

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def embedder_available(self) -> bool:
        return self._embedder is not None

    @property
    def embedding_dim(self) -> int:
        return self._embed_dim

    def embed(self, text: str) -> list[float]:
        """
        Embeddings RÉELS via Gemini text-embedding-004.
        Lève NotImplementedError si aucun embedder configuré, pour éviter
        de polluer la mémoire vectorielle avec du bruit.
        """
        if self._embedder is None:
            raise NotImplementedError(
                "Aucun embedder configuré. Ajoutez GEMINI_API_KEY dans .env ou "
                "désactivez VectorMemory."
            )
        try:
            self.metrics.embed_calls += 1
            response = self._embedder.embed_content(
                model="models/text-embedding-004",
                content=text[:8000],  # 2048 tokens approx
                task_type="retrieval_document",
            )
            embedding = response.get("embedding") if isinstance(response, dict) else response.embedding
            if not embedding:
                raise ValueError("Embedding vide retourné par Gemini")
            return list(embedding)
        except Exception as e:
            logger.warning("Embedding échoué : %s", e)
            raise

    def json_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback: dict[str, Any],
        max_retries: int = 2,
        temperature: float | None = None,
        complexity: str = "heavy",
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """
        Complétion JSON robuste avec retry + réparation.
        """
        self.metrics.json_calls += 1
        if self._provider == "fallback" or self._client is None:
            return fallback

        # Renforce les instructions JSON dans le system prompt
        system_with_json = (
            system_prompt.rstrip()
            + "\n\n"
            "RÈGLE STRICTE DE SORTIE :\n"
            "- Réponds UNIQUEMENT avec un objet JSON valide (RFC 8259).\n"
            "- Aucun texte avant ou après. Aucun bloc markdown. Aucun backtick.\n"
            "- Pas de commentaires JS, pas de trailing commas.\n"
            "- Toutes les clés et chaînes : guillemets doubles."
        )

        last_raw = ""
        last_error = ""
        attempts = max_retries + 1

        for attempt in range(attempts):
            try:
                effective_user = user_prompt
                if attempt > 0 and last_error:
                    self.metrics.retries += 1
                    effective_user = (
                        f"{user_prompt}\n\n"
                        f"⚠ Ta réponse précédente n'était pas du JSON valide "
                        f"({last_error[:120]}). Renvoie strictement un objet JSON valide."
                    )

                raw = self._call_provider(
                    system_with_json, effective_user,
                    json_mode=True, temperature=temperature,
                    model_override=self.select_model(complexity),
                    max_tokens=max_tokens,
                )
                last_raw = raw or ""
                if not raw:
                    last_error = "réponse vide"
                    continue

                parsed = repair_and_parse_json(raw)
                if parsed is not None:
                    return parsed

                last_error = "JSON invalide après réparation"
                logger.warning(
                    "[LLM/%s] JSON invalide (tentative %d/%d). Début: %s",
                    self._provider, attempt + 1, attempts,
                    raw[:160].replace("\n", " "),
                )

            except Exception as e:
                last_error = str(e)[:200]
                logger.warning(
                    "[LLM/%s] erreur tentative %d/%d : %s",
                    self._provider, attempt + 1, attempts, last_error,
                )

        self.metrics.json_failures += 1
        logger.info(
            "[LLM/%s] fallback servi après %d tentatives. Dernière réponse: %s",
            self._provider, attempts, last_raw[:120].replace("\n", " "),
        )
        return fallback

    def text_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        complexity: str = "heavy",
        max_tokens: int = 4096,
    ) -> str:
        if self._provider == "fallback" or self._client is None:
            return f"[Mode fallback] Requête reçue : {user_prompt[:200]}"
        try:
            return self._call_provider(
                system_prompt, user_prompt, json_mode=False, temperature=temperature,
                model_override=self.select_model(complexity), max_tokens=max_tokens,
            )
        except Exception as e:
            logger.warning("LLM text_completion error: %s", e)
            return f"[Erreur LLM] {str(e)[:100]}"

    # ── Appels par provider ─────────────────────────────────────────────────

    def select_model(self, complexity: str = "heavy") -> str:
        """
        Sélectionne le modèle OpenRouter selon la complexité de la tâche.
        heavy  → tâches de raisonnement complexe (draft, revision)
        medium → tâches intermédiaires (critique, synthèse)
        light  → tâches simples (classification, routing, planning rapide)
        """
        if self._provider == "openrouter":
            models = getattr(self, "_openrouter_models", {})
            return models.get(complexity, self._model)
        if self._provider == "groq":
            models = getattr(self, "_groq_models", {})
            return models.get(complexity, self._model)
        return self._model

    def _call_provider(
        self, system: str, user: str, json_mode: bool, temperature: float | None = None,
        model_override: str | None = None, max_tokens: int = 4096,
    ) -> str:
        """Appel provider avec backoff exponentiel sur 429 / erreurs transitoires.

        Les plans gratuits (Groq surtout) imposent des limites req/min et
        tokens/min. Plutôt que d'échouer immédiatement, on réessaie avec un
        délai croissant (0.8s, 1.6s, 3.2s), en respectant Retry-After si fourni.
        """
        last_exc: Exception | None = None
        for attempt in range(_TRANSIENT_MAX_RETRIES + 1):
            try:
                return self._call_provider_once(
                    system, user, json_mode, temperature, model_override, max_tokens,
                )
            except Exception as exc:  # noqa: BLE001
                msg = str(exc).lower()
                transient = any(
                    s in msg for s in ("429", "rate", "limit", "quota", "timeout", "timed out", "503", "502", "overloaded", "unavailable")
                )
                if not transient or attempt >= _TRANSIENT_MAX_RETRIES:
                    # Avant d'abandonner sur une erreur transitoire : bascule sur le secours.
                    if transient and self._secondary is not None:
                        try:
                            logger.warning("[LLM] %s indisponible → bascule sur le secours %s",
                                           self._provider, self._secondary["provider"])
                            self.metrics.by_provider["failover→" + self._secondary["provider"]] = (
                                self.metrics.by_provider.get("failover→" + self._secondary["provider"], 0) + 1
                            )
                            return self._call_provider_once(
                                system, user, json_mode, temperature,
                                model_override=None, max_tokens=max_tokens,
                                provider=self._secondary["provider"],
                                client=self._secondary["client"],
                                model=self._secondary["model"],
                            )
                        except Exception as sec_exc:  # noqa: BLE001
                            logger.warning("[LLM] secours %s a aussi échoué : %s",
                                           self._secondary["provider"], str(sec_exc)[:120])
                    raise
                last_exc = exc
                delay = _retry_after_seconds(exc) or (0.8 * (2 ** attempt))
                logger.warning(
                    "[LLM/%s] erreur transitoire (tentative %d) : %s → attente %.1fs",
                    self._provider, attempt + 1, msg[:120], delay,
                )
                time.sleep(min(delay, 8.0))
        if last_exc:
            raise last_exc
        return ""

    def _call_provider_once(
        self, system: str, user: str, json_mode: bool, temperature: float | None = None,
        model_override: str | None = None, max_tokens: int = 4096,
        provider: str | None = None, client: Any = None, model: str | None = None,
    ) -> str:
        # Provider effectif : secondaire (failover) si fourni, sinon principal.
        prov = provider or self._provider
        cli = client if client is not None else self._client
        self.metrics.calls += 1
        self.metrics.by_provider[prov] = self.metrics.by_provider.get(prov, 0) + 1
        temp = temperature if temperature is not None else (0.2 if json_mode else 0.5)
        active_model = model or model_override or self._model

        if prov in ("groq", "openrouter"):
            kwargs: dict[str, Any] = {
                "model": active_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": temp,
                "max_tokens": max_tokens,
            }
            if json_mode and prov in ("groq", "openrouter"):
                kwargs["response_format"] = {"type": "json_object"}
            response = cli.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""

        if prov == "anthropic":
            response = cli.messages.create(
                model=active_model,
                max_tokens=max_tokens,
                temperature=temp,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return response.content[0].text if response.content else ""

        if prov == "gemini":
            genai = cli
            generation_config: dict[str, Any] = {
                "temperature": temp,
                "max_output_tokens": max_tokens,
            }
            if json_mode:
                generation_config["response_mime_type"] = "application/json"
            model_obj = genai.GenerativeModel(
                active_model,
                system_instruction=system,
                generation_config=generation_config,
            )
            response = model_obj.generate_content(user)
            return response.text or ""

        if prov == "mistral":
            kwargs = {
                "model": active_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": temp,
                "max_tokens": max_tokens,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            response = cli.chat.complete(**kwargs)
            return response.choices[0].message.content or ""

        return ""
