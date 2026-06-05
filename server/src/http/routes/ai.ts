import { Router } from "express";
import { z } from "zod";

import { requireAuth } from "../../auth/requireAuth.js";
import { prisma } from "../../db/prisma.js";
import { asyncHandler } from "../asyncHandler.js";
import { ok, error } from "../response.js";
import { fetchAiService } from "../upstream.js";

export const aiRouter = Router();

const RunSchema = z.object({
  input: z.string().min(1),
  project_id: z.string().default("default-project"),
  task_id: z.string().optional(),
  agent_id: z.string().optional(),
  use_web_learning: z.boolean().default(false),
});

const ChatSchema = z.object({
  agent_id: z.string().min(1),
  message: z.string().min(1),
  conversation_history: z.array(z.object({ role: z.string(), content: z.string() })).default([]),
  project_id: z.string().default("knb-agents"),
  use_web_learning: z.boolean().default(false),
});

// POST /api/ai/run — full multi-agent workflow
aiRouter.post("/ai/run", requireAuth, asyncHandler(async (req, res) => {
  const userId = req.user?.sub ?? "system";
  const parsed = RunSchema.safeParse(req.body);
  if (!parsed.success) return error(res, "BAD_REQUEST", "Invalid payload", 400);

  const upstream = await fetchAiService("/api/agents/run", {
    method: "POST",
    body: JSON.stringify({
      input: parsed.data.input,
      project_id: parsed.data.project_id,
      task_id: parsed.data.task_id,
      user_id: userId,
      agent_id: parsed.data.agent_id ?? "default",
    }),
  });

  if (!upstream.ok) {
    const txt = await upstream.text().catch(() => "");
    return error(res, "UPSTREAM_ERROR", txt || `AI service error: ${upstream.status}`, 502);
  }

  const data = (await upstream.json()) as unknown;
  const result = data as {
    selected_agent?: string;
    selected_agents?: string[];
    response?: string;
    responses?: { summary?: string }[];
    workflow_id?: string;
  };

  await prisma.aiExecution.create({
    data: {
      projectId: parsed.data.project_id,
      taskId: parsed.data.task_id ?? null,
      prompt: parsed.data.input,
      selectedAgent: result.selected_agent ?? result.selected_agents?.join(",") ?? "unknown",
      result: result.response ?? result.responses?.map((x) => x.summary).filter(Boolean).join("\n") ?? JSON.stringify(data),
      metadata: { ...(result.workflow_id ? { workflowId: result.workflow_id } : {}), userId },
    },
  });

  return ok(res, data);
}));

// POST /api/ai/chat — direct agent chat (routes to /api/agents/chat)
aiRouter.post("/ai/chat", requireAuth, asyncHandler(async (req, res) => {
  const parsed = ChatSchema.safeParse(req.body);
  if (!parsed.success) return error(res, "BAD_REQUEST", "Invalid payload", 400);

  const upstream = await fetchAiService("/api/agents/chat", {
    method: "POST",
    body: JSON.stringify(parsed.data),
  });

  if (!upstream.ok) {
    const txt = await upstream.text().catch(() => "");
    return error(res, "UPSTREAM_ERROR", txt || `AI service error: ${upstream.status}`, 502);
  }

  const data = await upstream.json();
  return ok(res, data);
}));

// GET /api/agents — list KNB agents (proxy to AI service, no auth required for listing)
aiRouter.get("/agents", asyncHandler(async (_req, res) => {
  const upstream = await fetchAiService("/api/agents");
  if (!upstream.ok) return error(res, "UPSTREAM_ERROR", `AI service error: ${upstream.status}`, 502);
  const data = await upstream.json();
  return ok(res, data);
}));

// GET /api/ai/training-status — proxy to AI service
aiRouter.get("/ai/training-status", requireAuth, asyncHandler(async (_req, res) => {
  const upstream = await fetchAiService("/api/agents/training-status");
  if (!upstream.ok) return error(res, "UPSTREAM_ERROR", `AI service error: ${upstream.status}`, 502);
  const data = await upstream.json();
  return ok(res, data);
}));

// POST /api/ai/train — trigger agent self-training
aiRouter.post("/ai/train", requireAuth, asyncHandler(async (req, res) => {
  const body = z.object({
    agent_id: z.string().optional(),
    force: z.boolean().default(false),
  }).safeParse(req.body);
  if (!body.success) return error(res, "BAD_REQUEST", "Invalid payload", 400);
  const upstream = await fetchAiService("/api/agents/train", {
    method: "POST",
    body: JSON.stringify(body.data),
  });
  if (!upstream.ok) return error(res, "UPSTREAM_ERROR", `AI service error: ${upstream.status}`, 502);
  const data = await upstream.json();
  return ok(res, data);
}));

// POST /api/ai/learn-custom — assign a custom topic or URL to an agent
aiRouter.post("/ai/learn-custom", requireAuth, asyncHandler(async (req, res) => {
  const body = z.object({
    agent_id: z.string().min(1),
    topic: z.string().min(1),
  }).safeParse(req.body);
  if (!body.success) return error(res, "BAD_REQUEST", "Invalid payload", 400);
  const upstream = await fetchAiService("/api/agents/learn-custom", {
    method: "POST",
    body: JSON.stringify(body.data),
  });
  if (!upstream.ok) return error(res, "UPSTREAM_ERROR", `AI service error: ${upstream.status}`, 502);
  const data = await upstream.json();
  return ok(res, data);
}));

// POST /api/ai/generate-project
aiRouter.post("/ai/generate-project", requireAuth, asyncHandler(async (req, res) => {
  const body = z.object({
    request: z.string().min(10),
    project_id: z.string().default("generated-project"),
  }).safeParse(req.body);
  if (!body.success) return error(res, "BAD_REQUEST", "Invalid payload", 400);

  const userId = req.user?.sub ?? "system";
  const upstream = await fetchAiService("/api/agents/generate-project", {
    method: "POST",
    body: JSON.stringify({ request: body.data.request, project_id: body.data.project_id, user_id: userId }),
  });
  if (!upstream.ok) return error(res, "UPSTREAM_ERROR", `AI service error: ${upstream.status}`, 502);
  const data = await upstream.json();
  return ok(res, data);
}));
