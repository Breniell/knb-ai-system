import { Router } from "express";
import { z } from "zod";

import { requireAuth } from "../../auth/requireAuth.js";
import { prisma } from "../../db/prisma.js";
import { asyncHandler } from "../asyncHandler.js";
import { error, ok } from "../response.js";

export const tasksRouter = Router();

const CreateTaskSchema = z.object({
  projectId: z.string().min(1),
  title: z.string().min(2),
  description: z.string().optional(),
  assigneeId: z.string().optional(),
});

const UpdateTaskSchema = z.object({
  status: z.enum(["TODO", "IN_PROGRESS", "DONE", "BLOCKED"]),
});

tasksRouter.get("/tasks", requireAuth, asyncHandler(async (req, res) => {
  const projectId = req.query.projectId as string | undefined;
  const tasks = await prisma.task.findMany({
    where: projectId ? { projectId } : undefined,
    orderBy: { createdAt: "desc" },
  });
  return ok(res, { ok: true, tasks });
}));

tasksRouter.post("/tasks", requireAuth, asyncHandler(async (req, res) => {
  const parsed = CreateTaskSchema.safeParse(req.body);
  if (!parsed.success) return error(res, "BAD_REQUEST", "Invalid task payload", 400);
  const task = await prisma.task.create({ data: parsed.data });
  return ok(res, { ok: true, task });
}));

tasksRouter.patch("/tasks/:taskId/status", requireAuth, asyncHandler(async (req, res) => {
  const parsed = UpdateTaskSchema.safeParse(req.body);
  if (!parsed.success) return error(res, "BAD_REQUEST", "Invalid status payload", 400);
  const task = await prisma.task.update({
    where: { id: req.params.taskId },
    data: { status: parsed.data.status },
  });
  return ok(res, { ok: true, task });
}));

