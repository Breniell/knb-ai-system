#!/bin/bash
# KNB AI System — Démarrage local sans Docker
# Usage : chmod +x start-dev.sh && ./start-dev.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Vérification des prérequis ────────────────────────────────────────────────
check_version() {
  local cmd="$1" min_major="$2" label="$3"
  if ! command -v "$cmd" &>/dev/null; then
    echo "❌  $label introuvable. Installez-le depuis https://nodejs.org (Node) ou https://python.org (Python)"
    exit 1
  fi
  local ver
  ver=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
  local major="${ver%%.*}"
  if [[ "$major" -lt "$min_major" ]]; then
    echo "❌  $label $ver détecté, version $min_major+ requise."
    exit 1
  fi
  echo "✅  $label $ver"
}

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   KNB AI System — Démarrage local   ║"
echo "╚══════════════════════════════════════╝"
echo ""

check_version python3 3 "Python"
check_version node   18 "Node.js"

# ── Variables d'environnement ─────────────────────────────────────────────────
if [[ ! -f "$REPO_ROOT/.env" ]]; then
  if [[ -f "$REPO_ROOT/.env.example" ]]; then
    cp "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
    echo "⚠️   .env créé depuis .env.example — remplissez vos clés API avant de continuer."
    echo "    Fichier : $REPO_ROOT/.env"
    echo ""
  else
    echo "⚠️   Aucun fichier .env trouvé. Les clés API seront vides."
  fi
fi

# ── Virtualenv Python ─────────────────────────────────────────────────────────
AI_DIR="$REPO_ROOT/ai-services"
VENV="$AI_DIR/.venv"

echo "📦  Installation des dépendances Python…"
if [[ ! -d "$VENV" ]]; then
  python3 -m venv "$VENV"
fi
# shellcheck disable=SC1090
source "$VENV/bin/activate"
pip install -r "$AI_DIR/requirements.txt" --quiet --upgrade

# ── Node dependencies ─────────────────────────────────────────────────────────
echo "📦  Installation des dépendances Node.js…"
(cd "$REPO_ROOT/server" && npm install --silent)
(cd "$REPO_ROOT/client" && npm install --silent)

# ── Lancement des services ───────────────────────────────────────────────────
echo ""
echo "🚀  Démarrage des services…"
echo "   AI Service : http://localhost:8000"
echo "   Server API : http://localhost:8080"
echo "   Client     : http://localhost:5173"
echo ""
echo "   Arrêter : Ctrl+C"
echo ""

# Trap pour arrêter tous les processus fils
cleanup() {
  echo ""
  echo "🛑  Arrêt des services…"
  kill 0
  wait
  echo "✅  Tous les services sont arrêtés."
}
trap cleanup INT TERM EXIT

# Lancer en arrière-plan
(
  source "$VENV/bin/activate"
  cd "$AI_DIR"
  uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
) &

(
  cd "$REPO_ROOT/server"
  npm run dev
) &

(
  cd "$REPO_ROOT/client"
  npm run dev
) &

# Attendre tous les processus
wait
