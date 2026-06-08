import { Router } from "express";

import { requireAuth } from "../../auth/requireAuth.js";
import { prisma } from "../../db/prisma.js";
import { asyncHandler } from "../asyncHandler.js";
import { ok } from "../response.js";

export const analyticsRouter = Router();

analyticsRouter.get("/analytics/overview", requireAuth, asyncHandler(async (_req, res) => {
  try {
    const [projects, tasks, executions] = await Promise.all([
      prisma.project.count(),
      prisma.task.count(),
      prisma.aiExecution.count(),
    ]);
    return ok(res, { ok: true, metrics: { projects, tasks, executions }, dbAvailable: true });
  } catch {
    return ok(res, { ok: true, metrics: { projects: 0, tasks: 0, executions: 0 }, dbAvailable: false });
  }
}));

analyticsRouter.get("/analytics/executions", requireAuth, asyncHandler(async (_req, res) => {
  try {
    const executions = await prisma.aiExecution.findMany({
      orderBy: { createdAt: "desc" },
      take: 100,
    });
    return ok(res, { ok: true, executions });
  } catch {
    return ok(res, { ok: true, executions: [] });
  }
}));

