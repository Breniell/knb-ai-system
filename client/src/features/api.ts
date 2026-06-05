import { apiFetch } from "../lib/http";
import type { MemorySearchResult, Project, Task } from "../types";

export const runAi = (input: string, project_id: string, task_id?: string) =>
  apiFetch<{
    workflow_id: string;
    selected_agents: string[];
    plan: { id: string; title: string; assigned_agent: string; priority: number }[];
    responses: { agent: string; summary: string; score: number; artifacts?: unknown[] }[];
    timeline: { node: string; success?: boolean; started_at?: string; ended_at?: string }[];
  }>("/api/ai/run", {
    method: "POST",
    body: JSON.stringify({ input, project_id, task_id }),
  });

export const chatWithAgent = (
  agentId: string,
  message: string,
  history: { role: string; content: string }[],
  projectId = "knb-agents",
  useWebLearning = false
) =>
  apiFetch<{
    ok: boolean;
    agent_id: string;
    agent_name: string;
    response: {
      agent: string;
      summary: string;
      artifacts: unknown[];
      followups: string[];
      score: number;
    };
    learned_from: string[];
  }>("/api/ai/chat", {
    method: "POST",
    body: JSON.stringify({
      agent_id: agentId,
      message,
      conversation_history: history,
      project_id: projectId,
      use_web_learning: useWebLearning,
    }),
  });

export const getProjects = () =>
  apiFetch<{ ok: true; projects: Project[] }>("/api/projects");

export const createProject = (name: string, description?: string) =>
  apiFetch<{ ok: true; project: Project }>("/api/projects", {
    method: "POST",
    body: JSON.stringify({ name, description }),
  });

export const getTasks = (projectId?: string) =>
  apiFetch<{ ok: true; tasks: Task[] }>(`/api/tasks${projectId ? `?projectId=${projectId}` : ""}`);

export const createTask = (payload: {
  projectId: string;
  title: string;
  description?: string;
  assigneeId?: string;
}) =>
  apiFetch<{ ok: true; task: Task }>("/api/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const updateTaskStatus = (taskId: string, status: Task["status"]) =>
  apiFetch<{ ok: true; task: Task }>(`/api/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });

export const searchMemory = (query: string, limit = 8) =>
  apiFetch<{ ok: boolean; results?: MemorySearchResult[]; count?: number }>(
    `/api/memory/search?query=${encodeURIComponent(query)}&limit=${limit}`
  );

export const getServiceStatus = () =>
  apiFetch<{ ok: true; services: Record<string, string>; timestamp: string }>(
    "/api/monitoring/status"
  );

export const getAiMetrics = () =>
  apiFetch<{ ok: true; metrics: Record<string, number> }>("/api/monitoring/metrics");

export const getAnalytics = () =>
  apiFetch<{ ok: true; metrics: { projects: number; tasks: number; executions: number } }>(
    "/api/analytics/overview"
  );

export interface AgentTrainingStatus {
  agent: string;
  topics_learned: number;
  curriculum_size: number;
  completion_pct: number;
  last_trained: string | null;
  is_trained: boolean;
  error?: string;
}

export const getTrainingStatus = () =>
  apiFetch<{
    ok: boolean;
    agents: AgentTrainingStatus[];
    summary: { total_agents: number; trained_agents: number; total_topics_learned: number };
  }>("/api/ai/training-status");

export const triggerAgentTraining = (agentId?: string, force = false) =>
  apiFetch<{ ok: boolean; message: string; agents?: number; topics?: number }>(
    "/api/ai/train",
    { method: "POST", body: JSON.stringify({ agent_id: agentId, force }) }
  );

export const learnCustomTopic = (agentId: string, topic: string) =>
  apiFetch<{ ok: boolean; agent_name: string; topic: string; insights_count: number; insights: string[] }>(
    "/api/ai/learn-custom",
    { method: "POST", body: JSON.stringify({ agent_id: agentId, topic }) }
  );
