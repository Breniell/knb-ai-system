"""Tests for all 16 KNB agents — runs without API key (fallback mode)."""

import asyncio
import pytest

from app.core.llm import LlmClient
from app.models import AgentResponse, ExecutionContext, SubTask

# Force disabled LLM (no API key) to test fallback paths
import app.core.settings as _s
_s.settings.anthropic_api_key = None  # type: ignore[assignment]


def _make_task(agent_name: str) -> SubTask:
    return SubTask(
        id="test-001",
        title=f"Test task for {agent_name}",
        description="Teste les capacités de l'agent en mode fallback",
        assigned_agent=agent_name,
        priority=1,
    )


def _make_context() -> ExecutionContext:
    return ExecutionContext(
        workflow_id="test-workflow",
        project_id="test-project",
        task_id="test-task",
        user_id="test-user",
        memory_snippets=["KNB est une agence web à Yaoundé"],
        metadata={},
    )


def _make_llm() -> LlmClient:
    return LlmClient()


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def assert_valid_response(resp: AgentResponse, agent_name: str) -> None:
    assert isinstance(resp, AgentResponse), f"{agent_name}: not an AgentResponse"
    assert resp.agent == agent_name, f"{agent_name}: wrong agent name"
    assert isinstance(resp.summary, str) and len(resp.summary) > 10, f"{agent_name}: summary too short"
    assert isinstance(resp.score, float) and 0.0 <= resp.score <= 1.0, f"{agent_name}: invalid score"
    assert isinstance(resp.followups, list), f"{agent_name}: followups must be list"


# ── Business agents ───────────────────────────────────────────────────────────

def test_commercial_agent():
    from app.agents.commercial_agent import CommercialAgent
    agent = CommercialAgent()
    resp = _run(agent.execute(_make_task(agent.name), _make_context(), _make_llm()))
    assert_valid_response(resp, "CommercialAgent")
    assert isinstance(resp.artifacts, list)
    assert len(resp.artifacts) >= 1


def test_marketing_agent():
    from app.agents.marketing_agent import MarketingAgent
    agent = MarketingAgent()
    resp = _run(agent.execute(_make_task(agent.name), _make_context(), _make_llm()))
    assert_valid_response(resp, "MarketingAgent")


def test_community_manager_agent():
    from app.agents.community_manager_agent import CommunityManagerAgent
    agent = CommunityManagerAgent()
    resp = _run(agent.execute(_make_task(agent.name), _make_context(), _make_llm()))
    assert_valid_response(resp, "CommunityManagerAgent")
    artifacts = resp.artifacts
    assert isinstance(artifacts, list) and len(artifacts) >= 1


# ── Technique agents ──────────────────────────────────────────────────────────

def test_architecte_agent():
    from app.agents.architecte_agent import ArchitecteAgent
    agent = ArchitecteAgent()
    resp = _run(agent.execute(_make_task(agent.name), _make_context(), _make_llm()))
    assert_valid_response(resp, "ArchitecteAgent")


def test_dev_frontend_agent():
    from app.agents.dev_frontend_agent import DevFrontendAgent
    agent = DevFrontendAgent()
    resp = _run(agent.execute(_make_task(agent.name), _make_context(), _make_llm()))
    assert_valid_response(resp, "DevFrontendAgent")


def test_dev_backend_agent():
    from app.agents.dev_backend_agent import DevBackendAgent
    agent = DevBackendAgent()
    resp = _run(agent.execute(_make_task(agent.name), _make_context(), _make_llm()))
    assert_valid_response(resp, "DevBackendAgent")


def test_dev_mobile_agent():
    from app.agents.dev_mobile_agent import DevMobileAgent
    agent = DevMobileAgent()
    resp = _run(agent.execute(_make_task(agent.name), _make_context(), _make_llm()))
    assert_valid_response(resp, "DevMobileAgent")


def test_devops_agent():
    from app.agents.devops_agent import DevOpsAgent
    agent = DevOpsAgent()
    resp = _run(agent.execute(_make_task(agent.name), _make_context(), _make_llm()))
    assert_valid_response(resp, "DevOpsAgent")
    artifacts = resp.artifacts
    assert isinstance(artifacts, list)


def test_qa_agent():
    from app.agents.qa_agent import QAAgent
    agent = QAAgent()
    resp = _run(agent.execute(_make_task(agent.name), _make_context(), _make_llm()))
    assert_valid_response(resp, "QAAgent")


# ── Créatif agents ────────────────────────────────────────────────────────────

def test_designer_ux_ui_agent():
    from app.agents.designer_ux_ui_agent import DesignerUXUIAgent
    agent = DesignerUXUIAgent()
    resp = _run(agent.execute(_make_task(agent.name), _make_context(), _make_llm()))
    assert_valid_response(resp, "DesignerUXUIAgent")


def test_designer_graphique_agent():
    from app.agents.designer_graphique_agent import DesignerGraphiqueAgent
    agent = DesignerGraphiqueAgent()
    resp = _run(agent.execute(_make_task(agent.name), _make_context(), _make_llm()))
    assert_valid_response(resp, "DesignerGraphiqueAgent")


def test_redacteur_agent():
    from app.agents.redacteur_agent import RedacteurAgent
    agent = RedacteurAgent()
    resp = _run(agent.execute(_make_task(agent.name), _make_context(), _make_llm()))
    assert_valid_response(resp, "RedacteurAgent")
    artifacts = resp.artifacts
    assert isinstance(artifacts, list) and len(artifacts) >= 1


# ── Coordination agents ───────────────────────────────────────────────────────

def test_chef_projet_agent():
    from app.agents.chef_projet_agent import ChefDeProjetAgent
    agent = ChefDeProjetAgent()
    resp = _run(agent.execute(_make_task(agent.name), _make_context(), _make_llm()))
    assert_valid_response(resp, "ChefDeProjetAgent")


def test_support_client_agent():
    from app.agents.support_client_agent import SupportClientAgent
    agent = SupportClientAgent()
    resp = _run(agent.execute(_make_task(agent.name), _make_context(), _make_llm()))
    assert_valid_response(resp, "SupportClientAgent")


def test_finance_agent():
    from app.agents.finance_agent import FinanceAgent
    agent = FinanceAgent()
    resp = _run(agent.execute(_make_task(agent.name), _make_context(), _make_llm()))
    assert_valid_response(resp, "FinanceAgent")
    artifacts = resp.artifacts
    # Finance doit livrer au moins une facture
    assert isinstance(artifacts, list) and len(artifacts) >= 1
    titles = [a.get("title", "") for a in artifacts if isinstance(a, dict)]
    assert any("Facture" in t or "facture" in t or "Trésorerie" in t or "Rentabilité" in t for t in titles)


def test_reviewer_agent():
    from app.agents.reviewer_agent import ReviewerAgent
    agent = ReviewerAgent()
    resp = _run(agent.execute(_make_task(agent.name), _make_context(), _make_llm()))
    assert_valid_response(resp, "ReviewerAgent")


# ── Registry ──────────────────────────────────────────────────────────────────

def test_agent_registry_has_all_knb_agents():
    from app.orchestrator.agent_registry import AgentRegistry
    registry = AgentRegistry()
    agents = registry.list_knb_agents()
    names = [a["name"] for a in agents]
    expected = [
        "CommercialAgent", "MarketingAgent", "CommunityManagerAgent",
        "ArchitecteAgent", "DevFrontendAgent", "DevBackendAgent", "DevMobileAgent",
        "DevOpsAgent", "QAAgent",
        "DesignerUXUIAgent", "DesignerGraphiqueAgent", "RedacteurAgent",
        "ChefDeProjetAgent", "SupportClientAgent", "FinanceAgent",
        "ReviewerAgent",
    ]
    for name in expected:
        assert name in names, f"Agent {name} manquant dans le registre"


def test_agent_registry_has_emoji():
    from app.orchestrator.agent_registry import AgentRegistry
    registry = AgentRegistry()
    for agent_info in registry.list_knb_agents():
        assert "emoji" in agent_info, f"Emoji manquant pour {agent_info['name']}"
        assert agent_info["emoji"], f"Emoji vide pour {agent_info['name']}"


def test_agent_registry_has_snake_id():
    from app.orchestrator.agent_registry import AgentRegistry
    registry = AgentRegistry()
    for agent_info in registry.list_knb_agents():
        assert "_" in agent_info["id"] or agent_info["id"].islower(), \
            f"ID non snake_case pour {agent_info['name']}: {agent_info['id']}"
