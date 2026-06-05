import { Router } from "express";
import { z } from "zod";

import { requireAuth } from "../../auth/requireAuth.js";
import { asyncHandler } from "../asyncHandler.js";
import { ok, error } from "../response.js";
import { fetchAiService } from "../upstream.js";

export const learningRouter = Router();

// GET /api/learning/knowledge?topic=...
learningRouter.get("/learning/knowledge", requireAuth, asyncHandler(async (req, res) => {
  const topic = String(req.query.topic ?? "").trim();
  if (!topic) return error(res, "BAD_REQUEST", "topic query param required", 400);

  const upstream = await fetchAiService(`/api/learning/knowledge?topic=${encodeURIComponent(topic)}`);
  if (!upstream.ok) return error(res, "UPSTREAM_ERROR", `AI service error: ${upstream.status}`, 502);
  return ok(res, await upstream.json());
}));

// GET /api/learning/top
learningRouter.get("/learning/top", requireAuth, asyncHandler(async (req, res) => {
  const limit = Math.min(Number(req.query.limit ?? 10), 50);
  const upstream = await fetchAiService(`/api/learning/top?limit=${limit}`);
  if (!upstream.ok) return error(res, "UPSTREAM_ERROR", `AI service error: ${upstream.status}`, 502);
  return ok(res, await upstream.json());
}));

// POST /api/learning/trigger
learningRouter.post("/learning/trigger", requireAuth, asyncHandler(async (req, res) => {
  const body = z.object({
    topic: z.string().min(1),
    context_hint: z.string().default(""),
  }).safeParse(req.body);
  if (!body.success) return error(res, "BAD_REQUEST", "topic required", 400);

  const upstream = await fetchAiService("/api/learning/trigger", {
    method: "POST",
    body: JSON.stringify(body.data),
  });
  if (!upstream.ok) return error(res, "UPSTREAM_ERROR", `AI service error: ${upstream.status}`, 502);
  return ok(res, await upstream.json());
}));

// DELETE /api/learning/cache?topic=...
learningRouter.delete("/learning/cache", requireAuth, asyncHandler(async (req, res) => {
  const topic = String(req.query.topic ?? "").trim();
  if (!topic) return error(res, "BAD_REQUEST", "topic query param required", 400);

  const upstream = await fetchAiService(
    `/api/learning/cache?topic=${encodeURIComponent(topic)}`,
    { method: "DELETE" }
  );
  if (!upstream.ok) return error(res, "UPSTREAM_ERROR", `AI service error: ${upstream.status}`, 502);
  return ok(res, await upstream.json());
}));
