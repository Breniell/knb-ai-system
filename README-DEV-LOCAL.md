# KNB AI System — Démarrage local sans Docker

## Prérequis

| Outil | Version minimale | Vérification |
|-------|-----------------|--------------|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |

## Configuration (une seule fois)

```bash
cp .env.example .env
```

Ouvrez `.env` et renseignez :

| Variable | Description | Obligatoire |
|----------|-------------|-------------|
| `ANTHROPIC_API_KEY` | Clé API Claude — [console.anthropic.com](https://console.anthropic.com) | ✅ |
| `FIREBASE_PROJECT_ID` | ID de votre projet Firebase | ✅ |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | JSON du compte de service Firebase | ✅ |
| `VITE_FIREBASE_API_KEY` | Clé API Firebase (client) | ✅ |
| `BRAVE_API_KEY` | Clé Brave Search (recherche web) | ❌ optionnel |
| `WEB_LEARNING_ENABLED` | Activer l'apprentissage web auto | ❌ optionnel |

### Firebase — Créer un compte de service

1. [console.firebase.google.com](https://console.firebase.google.com) → votre projet
2. Paramètres du projet → Comptes de service → Générer une nouvelle clé privée
3. Copiez le contenu JSON dans `FIREBASE_SERVICE_ACCOUNT_JSON`

## Démarrage

### Linux / macOS / WSL

```bash
chmod +x start-dev.sh
./start-dev.sh
```

### Windows PowerShell

```powershell
.\start-dev.ps1
```

Le script :
1. Vérifie Python 3.11+ et Node 18+
2. Crée un virtualenv Python dans `ai-services/.venv`
3. Installe toutes les dépendances Python et Node
4. Lance les 3 services en parallèle

## URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Client React** | http://localhost:5173 | Interface principale KNB |
| **Server API** | http://localhost:8080 | Gateway Node.js |
| **AI Service** | http://localhost:8000 | Moteur IA Python |
| Health server | http://localhost:8080/healthz | Statut serveur |
| Health AI | http://localhost:8000/healthz | Statut service IA |
| Docs API IA | http://localhost:8000/docs | Swagger auto-généré |

## Architecture Firebase-only

Ce mode **ne requiert aucune base de données locale**.
Toute la persistance passe par Firestore :

| Ancienne stack | Firebase-only |
|----------------|---------------|
| Redis | Firestore `shortTermMemory` (TTL simulé) |
| Qdrant | Firestore `semanticMemory` (similarité TF-IDF locale) |
| PostgreSQL | Firestore `aiMemoryHistory` + `aiWorkflowSteps` |
| OpenAI | Anthropic Claude `claude-sonnet-4-20250514` |

## Agents KNB disponibles

L'interface "Agents KNB" donne accès à **16 agents spécialisés** :

### Pôle Business
- 💼 **CommercialAgent** — Devis, propositions, closing
- 📈 **MarketingAgent** — Stratégie digitale, campagnes FCFA
- 📱 **CommunityManagerAgent** — Réseaux sociaux, contenu

### Pôle Technique
- 🏗️ **ArchitecteAgent** — Architecture, choix tech, ADR
- 🖥️ **DevFrontendAgent** — React/Next.js/TypeScript
- ⚙️ **DevBackendAgent** — Node.js/Prisma/PostgreSQL
- 📲 **DevMobileAgent** — React Native/Expo, offline-first
- 🚀 **DevOpsAgent** — CI/CD, Vercel, Railway, Docker
- 🧪 **QAAgent** — Tests, recette client, automatisation

### Pôle Créatif
- 🎨 **DesignerUXUIAgent** — Wireframes, design system KNB
- ✏️ **DesignerGraphiqueAgent** — Logo, charte graphique
- 📝 **RedacteurAgent** — Copywriting SEO, blog, TikTok

### Pôle Coordination
- 📋 **ChefDeProjetAgent** — Roadmap Agile, cahier des charges
- 🤝 **SupportClientAgent** — Relation client, onboarding
- 💰 **FinanceAgent** — Facturation FCFA, TVA, trésorerie

### Pôle Veille
- 🔍 **ReviewerAgent** — Revue finale, go/no-go, cohérence

## Apprentissage web autonome

Activez `WEB_LEARNING_ENABLED=true` dans `.env` pour que les agents
apprennent automatiquement depuis le web (Brave Search ou DuckDuckGo).

Les connaissances apprises sont stockées dans Firestore `learnedKnowledge`
et réutilisées dans les conversations suivantes (cache 48h).

## Commandes utiles

```bash
# Lancer uniquement le service IA
cd ai-services && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Lancer uniquement le serveur
cd server && npm run dev

# Lancer uniquement le client
cd client && npm run dev

# Tester les agents (sans clé API, mode fallback)
cd ai-services && source .venv/bin/activate && python -m pytest tests/ -v

# Mode Docker complet (avec Postgres, Redis, Qdrant)
docker compose --profile full up
```

---

*KNB Dev Solutions — Yaoundé, Cameroun*  
*Kouda Njogab Breniell | knbdevsolutions@gmail.com | +237 691 586 701*  
*[knbdev.cm](https://knbdev.cm) — Votre vision. Notre code.*
