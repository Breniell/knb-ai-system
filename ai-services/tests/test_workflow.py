"""Tests for the multi-agent LangGraph workflow — fallback mode (no API key)."""

import asyncio
import os

import pytest

os.environ["GROQ_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["MISTRAL_API_KEY"] = ""
os.environ["OPENROUTER_API_KEY"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["WEB_LEARNING_ENABLED"] = "false"

import app.core.settings as _s

_s.settings.groq_api_key = ""
_s.settings.gemini_api_key = ""
_s.settings.mistral_api_key = ""
_s.settings.openrouter_api_key = ""
_s.settings.anthropic_api_key = ""
_s.settings.web_learning_enabled = False

from app.core.llm import LlmClient
from app.models import AgentResponse, ExecutionContext, SubTask
from app.workflows.langgraph_workflow import build_workflow


# ── Dummy registry for isolated workflow tests ────────────────────────────────

class _DummyAgent:
    def __init__(self, name: str):
        self.name = name
        self.specialty = "test"
        self.emoji = "🤖"

    async def execute(self, task: SubTask, context: ExecutionContext, llm: LlmClient) -> AgentResponse:
        return AgentResponse(agent=self.name, summary=f"done:{task.title}", score=1.0)


_ALL_AGENT_NAMES = [
    "FrontendAgent", "BackendAgent", "QAAgent", "DevOpsAgent", "ReviewerAgent",
    "CommercialAgent", "MarketingAgent", "CommunityManagerAgent",
    "ArchitecteAgent", "DevFrontendAgent", "DevBackendAgent", "DevMobileAgent",
    "DesignerUXUIAgent", "DesignerGraphiqueAgent", "RedacteurAgent",
    "ChefDeProjetAgent", "SupportClientAgent", "FinanceAgent",
]


class _Registry:
    def __init__(self):
        self.agents = {n: _DummyAgent(n) for n in _ALL_AGENT_NAMES}

    def get(self, name: str):
        return self.agents[name]

    def list_agents(self):
        return [{"id": n.lower(), "name": n, "specialty": "test", "emoji": "🤖", "status": "ready"}
                for n in self.agents]

    def list_knb_agents(self):
        return self.list_agents()


def _make_state(request: str):
    return {
        "request": request,
        "context": ExecutionContext(
            workflow_id="wf-test",
            project_id="p1",
            user_id="u1",
            memory_snippets=[],
            metadata={},
        ),
        "plan": [],
        "queue": [],
        "responses": [],
        "timeline": [],
        "retry_map": {},
        "errors": [],
    }


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_workflow_executes_nodes():
    workflow = build_workflow(_Registry(), LlmClient())
    state = await workflow.ainvoke(_make_state(
        "Crée un site web e-commerce pour une PME camerounaise avec frontend, backend et tests"
    ))
    assert len(state["plan"]) > 0
    assert len(state["responses"]) > 0
    assert len(state["timeline"]) > 0


@pytest.mark.asyncio
async def test_workflow_planner_node_in_timeline():
    workflow = build_workflow(_Registry(), LlmClient())
    state = await workflow.ainvoke(_make_state("Stratégie marketing pour KNB"))
    nodes = [t["node"] for t in state["timeline"]]
    assert "planner" in nodes


@pytest.mark.asyncio
async def test_workflow_all_responses_have_required_fields():
    workflow = build_workflow(_Registry(), LlmClient())
    state = await workflow.ainvoke(_make_state("Plan de projet mobile React Native"))
    for resp in state["responses"]:
        assert "agent" in resp
        assert "summary" in resp
        assert "score" in resp


@pytest.mark.asyncio
async def test_workflow_with_real_registry():
    """Run workflow with the real AgentRegistry (fallback LLM)."""
    from app.orchestrator.agent_registry import AgentRegistry
    registry = AgentRegistry()
    workflow = build_workflow(registry, LlmClient())
    state = await workflow.ainvoke(_make_state("Génère une facture pour un projet web KNB"))
    assert isinstance(state["responses"], list)
    assert len(state["responses"]) >= 1


@pytest.mark.asyncio
async def test_workflow_no_exception_on_unknown_request():
    """Workflow must not crash on arbitrary input."""
    workflow = build_workflow(_Registry(), LlmClient())
    try:
        state = await workflow.ainvoke(_make_state("??? %% 123 lorem ipsum dolor sit amet"))
    except Exception as exc:
        pytest.fail(f"Workflow raised unexpected exception: {exc}")
    assert "responses" in state
