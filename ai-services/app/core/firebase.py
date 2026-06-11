import logging
import os

logger = logging.getLogger(__name__)

_db = None
_initialized = False


def _init_firebase():
    global _db, _initialized
    if _initialized:
        return _db

    _initialized = True

    if os.environ.get("FIREBASE_DISABLED", "").lower() in {"1", "true", "yes", "on"}:
        logger.info("Firebase: désactivé par FIREBASE_DISABLED")
        return None

    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

    # Resolve relative paths against the project root (3 levels up from this file)
    if cred_path and not os.path.isabs(cred_path):
        base = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        cred_path = os.path.join(base, cred_path)

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if firebase_admin._apps:
            _db = firestore.client()
            logger.info("Firebase: réutilisation de l'app existante")
            return _db

        # Initialisation par variables d'environnement (prioritaire sur les fichiers)
        svc_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "")
        client_email = os.environ.get("FIREBASE_CLIENT_EMAIL", "")
        private_key = os.environ.get("FIREBASE_PRIVATE_KEY", "")
        project_id = os.environ.get("FIREBASE_PROJECT_ID", "")

        if svc_json:
            try:
                import json as _json
                cred = credentials.Certificate(_json.loads(svc_json))
                firebase_admin.initialize_app(cred)
                _db = firestore.client()
                logger.info("Firebase: connecté via FIREBASE_SERVICE_ACCOUNT_JSON")
                return _db
            except Exception as e:
                logger.warning("Firebase: FIREBASE_SERVICE_ACCOUNT_JSON invalide (%s)", e)

        elif client_email and private_key and project_id:
            try:
                # Render stocke souvent les \n en littéral — on normalise
                normalized_key = private_key.strip('"').strip("'").replace("\\n", "\n")
                svc_dict = {
                    "type": "service_account",
                    "project_id": project_id,
                    "client_email": client_email,
                    "private_key": normalized_key,
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
                cred = credentials.Certificate(svc_dict)
                firebase_admin.initialize_app(cred)
                _db = firestore.client()
                logger.info("Firebase: connecté via FIREBASE_CLIENT_EMAIL + FIREBASE_PRIVATE_KEY")
                return _db
            except Exception as e:
                logger.warning("Firebase: initialisation par variables d'env échouée (%s)", e)

        if cred_path and os.path.isfile(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            _db = firestore.client()
            logger.info("Firebase: connecté via JSON → %s", cred_path)
            return _db

        # Fallback: look for firebase-service-account.json in common locations
        fallback_paths = [
            os.path.join(os.getcwd(), "firebase-service-account.json"),
            os.path.join(os.path.dirname(os.getcwd()), "firebase-service-account.json"),
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "firebase-service-account.json",
            ),
        ]
        for path in fallback_paths:
            if os.path.isfile(path):
                cred = credentials.Certificate(path)
                firebase_admin.initialize_app(cred)
                _db = firestore.client()
                logger.info("Firebase: connecté via fallback → %s", path)
                return _db

        logger.warning(
            "Firebase: credentials non trouvées — mode sans persistance. "
            "Définissez GOOGLE_APPLICATION_CREDENTIALS dans .env"
        )
        return None

    except Exception as e:
        logger.warning("Firebase: erreur d'initialisation (%s) — mode sans persistance", e)
        return None


def get_firestore_client():
    return _init_firebase()
