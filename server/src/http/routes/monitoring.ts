import { Router } from "express";

import { requireAuth } from "../../auth/requireAuth.js";
import { redis } from "../../cache/redis.js";
import { asyncHandler } from "../asyncHandler.js";
import { error, ok } from "../response.js";
import { fetchAiService } from "../upstream.js";

export const monitoringRouter = Router();

monitoringRouter.get("/monitoring/status", requireAuth, asyncHandler(async (_req, res) => {
  const redisPing = await redis.ping().catch(() => "DOWN");
  return ok(res, {
    ok: true,
    services: {
      api: "UP",
      redis: redisPing === "PONG" ? "UP" : "DOWN",
    },
    timestamp: new Date().toISOString(),
  });
}));

monitoringRouter.get("/monitoring/metrics", requireAuth, asyncHandler(async (_req, res) => {
  const upstream = await fetchAiService("/api/monitoring/metrics");
  if (!upstream.ok) return error(res, "UPSTREAM_ERROR", `AI service error: ${upstream.status}`, 502);
  return ok(res, await upstream.json());
}));

monitoringRouter.get("/monitoring/workflows/:workflowId", requireAuth, asyncHandler(async (req, res) => {
  const workflowId = req.params.workflowId;
  if (!workflowId) return error(res, "BAD_REQUEST", "Missing workflow id", 400);

  const upstream = await fetchAiService(`/api/monitoring/workflows/${encodeURIComponent(workflowId)}`);
  if (!upstream.ok) return error(res, "UPSTREAM_ERROR", `AI service error: ${upstream.status}`, 502);
  return ok(res, await upstream.json());
}));

