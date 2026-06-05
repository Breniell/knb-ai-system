## KNB AI SYSTEM (Phase 3 Autonomous Platform)

This version upgrades the platform from orchestrator scaffolding into an autonomous multi-agent execution engine with real workflow state, semantic memory retrieval/injection, task decomposition, collaboration, retry handling, and observability APIs.

### New architecture

- **AI execution engine (`ai-services`)**
  - Typed execution contracts (`ExecutionContext`, `SubTask`, `AgentResponse`, timeline steps)
  - Real LangGraph workflow with nodes:
    - `planner`
    - `frontend`
    - `backend`
    - `qa`
    - `devops`
    - `reviewer`
  - Conditional routing and retry handling (up to 3 retries per failed subtask)
  - Workflow state persisted to Redis and PostgreSQL

- **Agent intelligence layer**
  - Agents now produce structured JSON outputs (summary, artifacts, followups, score)
  - LLM-backed reasoning via OpenAI JSON completions
  - Fallback deterministic behavior for local/no-key mode
  - Reviewer agent validates multi-agent output consistency

- **Semantic memory system**
  - OpenAI embeddings (`text-embedding-3-small`) via `app/core/llm.py`
  - Qdrant vector memory with project-based filtering
  - Redis short-term workflow cache (fast retrieval)
  - PostgreSQL long-term memory and workflow step history

- **Server hardening**
  - Rate limiting middleware
  - Audit logging middleware
  - Graceful shutdown (SIGINT/SIGTERM)
  - AI gateway updated for structured workflow outputs

- **Frontend intelligence dashboard**
  - AI Console now renders:
    - execution plan
    - agent response cards
    - workflow timeline
  - Monitoring page includes AI metrics counters

### Workflow execution

1. Request hits `POST /api/ai/run` (server) -> forwarded to `POST /api/agents/run` (ai-services).
2. Planner decomposes project/task request into prioritized subtasks.
3. LangGraph conditionally routes each subtask to the mapped specialist agent.
4. Each agent reasons with memory snippets injected from semantic retrieval.
5. Reviewer runs last to produce release/readiness verdict.
6. Timeline, responses, and errors are stored (Redis + Postgres).

### Agent collaboration model

- Shared `ExecutionContext` carries:
  - workflow id
  - project/task/user identity
  - semantic memory snippets
  - runtime metadata
- Planner-generated subtasks explicitly assign agent ownership.
- Reviewer consumes accumulated outputs and creates final cross-agent validation.

### Semantic memory flow

1. Query arrives -> vector search in Qdrant for relevant project memories.
2. Top semantic hits are injected into execution context.
3. Agent outputs + workflow traces are written back:
  - Redis (`workflow:{id}` state snapshot)
  - Qdrant (semantic recall corpus)
  - PostgreSQL (`ai_memory_history`, `ai_workflow_steps`)

### Key endpoints

- `POST /api/agents/run`
- `POST /api/agents/generate-project`
- `GET /api/agents`
- `GET /api/memory/search?query=...&project_id=...`
- `GET /api/monitoring/metrics`
- `GET /api/monitoring/workflows/{workflow_id}`
- `POST /api/ai/run` (server gateway)
- `POST /api/ai/generate-project` (server gateway)

### Run locally

```bash
cp .env.example .env
docker compose up --build
```

Open:
- `http://localhost` (nginx)
- `http://localhost:5173` (client direct)
- `http://localhost:8080/healthz`
- `http://localhost:8000/healthz`

### Deployment strategy

- Keep server + ai-services behind nginx/ingress.
- Enable production secrets:
  - `JWT_SECRET`
  - `OPENAI_API_KEY`
  - DB/Redis credentials
- Run Prisma migrations pre-deploy.
- Use rolling or blue/green for server/ai-services.
- Monitor `GET /api/monitoring/metrics` and `GET /api/analytics/executions` for execution health and drift.

