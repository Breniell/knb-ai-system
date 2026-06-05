import { Router } from "express";

import { requireAuth } from "../../auth/requireAuth.js";
import { asyncHandler } from "../asyncHandler.js";
import { error, ok } from "../response.js";
import { fetchAiService } from "../upstream.js";

export const memoryRouter = Router();

memoryRouter.get("/memory/search", requireAuth, asyncHandler(async (req, res) => {
  const query = typeof req.query.query === "string" ? req.query.query : "";
  const limit = typeof req.query.limit === "string" ? req.query.limit : "5";
  const projectId = typeof req.query.project_id === "string" ? req.query.project_id : undefined;

  const params = new URLSearchParams({ query, limit });
  if (projectId) params.set("project_id", projectId);

  const upstream = await fetchAiService(`/api/memory/search?${params.toString()}`);
  if (!upstream.ok) return error(res, "UPSTREAM_ERROR", `AI service error: ${upstream.status}`, 502);
  return ok(res, await upstream.json());
}));
