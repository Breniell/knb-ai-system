import { Router } from "express";
import { z } from "zod";

import { requireAuth } from "../../auth/requireAuth.js";
import { requireRole } from "../../auth/rbac.js";
import { prisma } from "../../db/prisma.js";
import { asyncHandler } from "../asyncHandler.js";
import { error, ok } from "../response.js";

export const projectsRouter = Router();

const CreateProjectSchema = z.object({
  name: z.string().min(2),
  description: z.string().optional(),
  ownerId: z.string().optional(),
});

projectsRouter.get("/projects", requireAuth, asyncHandler(async (_req, res) => {
  const projects = await prisma.project.findMany({
    include: { tasks: true, owner: { select: { id: true, email: true, role: true } } },
    orderBy: { createdAt: "desc" },
  });
  return ok(res, { ok: true, projects });
}));

projectsRouter.post("/projects", requireAuth, requireRole(["ADMIN", "MANAGER"]), asyncHandler(async (req, res) => {
  const parsed = CreateProjectSchema.safeParse(req.body);
  if (!parsed.success) return error(res, "BAD_REQUEST", "Invalid project payload", 400);
  const ownerId = parsed.data.ownerId ?? req.user?.sub;
  if (!ownerId) return error(res, "BAD_REQUEST", "Missing ownerId", 400);

  const project = await prisma.project.create({
    data: { name: parsed.data.name, description: parsed.data.description, ownerId },
  });
  return ok(res, { ok: true, project });
}));

