export type AgentStatus = { name: string; specialty: string; status: string };

export type Project = {
  id: string;
  name: string;
  description?: string | null;
  createdAt: string;
};

export type Task = {
  id: string;
  title: string;
  description?: string | null;
  status: "TODO" | "IN_PROGRESS" | "DONE" | "BLOCKED";
  projectId: string;
  createdAt: string;
};

export type MemorySearchResult = {
  id: string;
  content: string;
  source?: string;
  score?: number;
  metadata?: Record<string, unknown>;
};

export type ServiceStatus = {
  name: string;
  status: "UP" | "DOWN" | "DEGRADED" | string;
  latencyMs?: number;
  message?: string;
};
