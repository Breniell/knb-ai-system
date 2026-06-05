from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Providers (gratuits en priorité)
    groq_api_key: str = ""          # groq.com  — gratuit 14400 req/jour
    gemini_api_key: str = ""        # aistudio.google.com — gratuit 1500 req/jour
    mistral_api_key: str = ""       # console.mistral.ai — tier gratuit
    openrouter_api_key: str = ""    # openrouter.ai — modeles gratuits disponibles
    anthropic_api_key: str = ""     # payant — optionnel

    # Firebase Admin SDK
    google_application_credentials: str = ""
    firebase_project_id: str = "knb-ai-system"
    firebase_client_email: str = ""
    firebase_storage_bucket: str = "knb-ai-system.firebasestorage.app"
    firebase_auth_domain: str = "knb-ai-system.firebaseapp.com"
    firestore_workflow_collection: str = "workflowExecutions"

    # Web learning
    brave_api_key: str = ""
    web_learning_enabled: bool = True
    web_cache_ttl_hours: int = 24
    knowledge_cache_ttl_days: int = 7

    # Server
    ai_service_port: int = 8000
    server_port: int = 8080
    node_env: str = "development"

    # Legacy / Docker full-stack (not used in Firebase-only mode)
    embedding_size: int = 1536
    qdrant_url: str = "http://qdrant:6333"
    qdrant_api_key: str = ""
    redis_url: str = "redis://redis:6379"
    database_url: str = "postgresql://knb:knb_password@postgres:5432/knb"


settings = Settings()
