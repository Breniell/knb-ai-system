from pydantic import BaseModel, Field


class ExecutionContext(BaseModel):
    workflow_id: str
    project_id: str
    task_id: str | None = None
    user_id: str
    memory_snippets: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class SubTask(BaseModel):
    id: str
    title: str
    description: str
    assigned_agent: str
    priority: int = 1


class AgentRunRequest(BaseModel):
    input: str = Field(..., description="User prompt/task")
    project_id: str = Field("default-project", description="Project context")
    task_id: str | None = Field(default=None, description="Task identifier")
    user_id: str = Field("system", description="Caller identity")
    mode: str = Field("autonomous", description="Execution mode")


class AgentResponse(BaseModel):
    agent: str
    summary: str
    artifacts: list[dict] = Field(default_factory=list)
    followups: list[str] = Field(default_factory=list)
    score: float = 0.0


class WorkflowStepResult(BaseModel):
    node: str
    success: bool
    started_at: str
    ended_at: str
    details: dict = Field(default_factory=dict)


class AgentExecutionResult(BaseModel):
    ok: bool = True
    workflow_id: str
    selected_agents: list[str]
    plan: list[SubTask] = Field(default_factory=list)
    responses: list[AgentResponse] = Field(default_factory=list)
    review: AgentResponse | None = None
    timeline: list[WorkflowStepResult] = Field(default_factory=list)
    context: ExecutionContext

