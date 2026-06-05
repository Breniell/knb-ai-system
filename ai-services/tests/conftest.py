import os


def _disable_external_services() -> None:
    for key in (
        "GROQ_API_KEY",
        "GEMINI_API_KEY",
        "MISTRAL_API_KEY",
        "OPENROUTER_API_KEY",
        "ANTHROPIC_API_KEY",
        "BRAVE_API_KEY",
        "QDRANT_URL",
        "QDRANT_API_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS",
    ):
        os.environ[key] = ""

    os.environ["WEB_LEARNING_ENABLED"] = "false"
    os.environ["FIREBASE_DISABLED"] = "true"


_disable_external_services()

