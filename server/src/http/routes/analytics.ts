import { Router } from "express";

import { requireAuth } from "../../auth/requireAuth.js";
import { prisma } from "../../db/prisma.js";
import { asyncHandler } from "../asyncHandler.js";
import { ok } from "../response.js";

export const analyticsRouter = Router();

analyticsRouter.get("/analytics/overview", requireAuth, asyncHandler(async (_req, res) => {
  const [projects, tasks, executions] = await Promise.all([
    prisma.project.count(),
    prisma.task.count(),
    prisma.aiExecution.count(),
  ]);

  return ok(res, {
    ok: true,
    metrics: { projects, tasks, executions },
  });
}));

analyticsRouter.get("/analytics/executions", requireAuth, asyncHandler(async (_req, res) => {
  const executions = await prisma.aiExecution.findMany({
    orderBy: { createdAt: "desc" },
    take: 100,
  });
  return ok(res, { ok: true, executions });
}));

