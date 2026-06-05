from app.agents.architecte_agent import ArchitecteAgent
from app.agents.backend_agent import BackendAgent
from app.agents.chef_projet_agent import ChefDeProjetAgent
from app.agents.commercial_agent import CommercialAgent
from app.agents.community_manager_agent import CommunityManagerAgent
from app.agents.designer_graphique_agent import DesignerGraphiqueAgent
from app.agents.designer_ux_ui_agent import DesignerUXUIAgent
from app.agents.dev_backend_agent import DevBackendAgent
from app.agents.dev_frontend_agent import DevFrontendAgent
from app.agents.dev_mobile_agent import DevMobileAgent
from app.agents.devops_agent import DevOpsAgent
from app.agents.finance_agent import FinanceAgent
from app.agents.frontend_agent import FrontendAgent
from app.agents.marketing_agent import MarketingAgent
from app.agents.master_orchestrator_agent import MasterOrchestratorAgent
from app.agents.qa_agent import QAAgent
from app.agents.redacteur_agent import RedacteurAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.agents.support_client_agent import SupportClientAgent


class AgentRegistry:
    def __init__(self) -> None:
        self._agents = {
            # Workflow agents (original + legacy)
            "MasterOrchestratorAgent": MasterOrchestratorAgent(),
            "FrontendAgent": FrontendAgent(),
            "BackendAgent": BackendAgent(),
            "QAAgent": QAAgent(),
            "DevOpsAgent": DevOpsAgent(),
            "ReviewerAgent": ReviewerAgent(),
            # KNB Business
            "CommercialAgent": CommercialAgent(),
            "MarketingAgent": MarketingAgent(),
            "CommunityManagerAgent": CommunityManagerAgent(),
            # KNB Technique
            "ArchitecteAgent": ArchitecteAgent(),
            "DevFrontendAgent": DevFrontendAgent(),
            "DevBackendAgent": DevBackendAgent(),
            "DevMobileAgent": DevMobileAgent(),
            # KNB Créatif
            "DesignerUXUIAgent": DesignerUXUIAgent(),
            "DesignerGraphiqueAgent": DesignerGraphiqueAgent(),
            "RedacteurAgent": RedacteurAgent(),
            # KNB Coordination
            "ChefDeProjetAgent": ChefDeProjetAgent(),
            "SupportClientAgent": SupportClientAgent(),
            "FinanceAgent": FinanceAgent(),
        }

    def get(self, name: str):
        return self._agents[name]

    def list_agents(self):
        results = []
        for a in self._agents.values():
            results.append({
                "id": _to_snake(a.name),
                "name": a.name,
                "specialty": a.specialty,
                "emoji": getattr(a, "emoji", "🤖"),
                "status": "ready",
            })
        return results

    def list_knb_agents(self):
        """Return only user-facing KNB agents (excluding internal workflow agents)."""
        excluded = {"MasterOrchestratorAgent", "FrontendAgent", "BackendAgent"}
        return [a for a in self.list_agents() if a["name"] not in excluded]


def _to_snake(name: str) -> str:
    import re
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
