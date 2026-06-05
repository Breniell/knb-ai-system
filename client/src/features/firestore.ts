import {
  collection,
  limit,
  onSnapshot,
  orderBy,
  query,
  type Timestamp,
  type Unsubscribe,
} from "firebase/firestore";

import { db } from "../lib/firebase";

export type WorkflowExecution = {
  workflowId: string;
  workflow_id?: string;
  userId: string;
  projectId: string;
  taskId?: string | null;
  input: string;
  status: "running" | "succeeded" | "failed";
  selectedAgents: string[];
  plan: { id: string; title: string; assigned_agent: string; priority: number }[];
  responses: { agent: string; summary: string; score: number }[];
  timeline: { node: string; success?: boolean; started_at?: string; ended_at?: string }[];
  errors: string[];
  metadata: Record<string, unknown>;
  createdAt?: Timestamp | null;
  updatedAt?: Timestamp | null;
};

export function subscribeWorkflowExecutions(
  userId: string,
  onChange: (items: WorkflowExecution[]) => void,
  onError?: (error: Error) => void
): Unsubscribe {
  // Firebase non configuré — retourne une no-op unsubscribe
  if (!db) {
    onChange([]);
    return () => {};
  }

  const workflowQuery = query(
    collection(db, "users", userId, "workflowExecutions"),
    orderBy("createdAt", "desc"),
    limit(25)
  );

  return onSnapshot(
    workflowQuery,
    (snapshot) => {
      onChange(
        snapshot.docs.map((item) => ({
          workflowId: item.id,
          ...(item.data() as Omit<WorkflowExecution, "workflowId">),
        }))
      );
    },
    onError
  );
}
