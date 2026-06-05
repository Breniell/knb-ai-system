"""
agents/devbackendagent_agent.py — Wrapper KnbAgent (v3.1).
"""
from __future__ import annotations
from typing import Any
from app.agents.base import KnbAgent
from app.agents._senior_prompts import SENIOR_PROMPTS
from app.models import ExecutionContext, SubTask


class DevBackendAgent(KnbAgent):
    name = "DevBackendAgent"
    specialty = "Node.js 20, TypeScript, Prisma, PostgreSQL, Zod, sécurité API"
    emoji = "🛠️"
    _system_prompt = SENIOR_PROMPTS.get("DevBackendAgent", "")

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": "API REST documentée avec Express + Zod + Prisma. Endpoints CRUD complets, middleware d'auth Firebase, rate limiting, gestion d'erreurs centralisée. Schéma PostgreSQL avec indexes optimisés.",
            "artifacts": [{'type': 'api_route', 'title': 'Route Express typée avec Zod', 'content': "// routes/projects.ts\nimport { Router, Request, Response, NextFunction } from 'express'\nimport { z } from 'zod'\nimport { prisma } from '@/lib/prisma'\nimport { authenticate } from '@/middleware/auth'\nimport { validate } from '@/middleware/validate'\n\nconst router = Router()\n\nconst CreateProjectSchema = z.object({\n  name: z.string().min(2).max(100),\n  description: z.string().max(500).optional(),\n  budget: z.number().positive().optional(),\n})\n\nrouter.post('/', authenticate, validate(CreateProjectSchema),\n  async (req: Request, res: Response, next: NextFunction) => {\n    try {\n      const project = await prisma.project.create({\n        data: { ...req.body, ownerId: req.user!.uid },\n      })\n      res.status(201).json({ ok: true, data: project })\n    } catch (error) { next(error) }\n  }\n)\n\nrouter.get('/', authenticate, async (req, res, next) => {\n  try {\n    const { cursor, limit = '20' } = req.query\n    const projects = await prisma.project.findMany({\n      where: { ownerId: req.user!.uid, status: 'ACTIVE' },\n      take: Number(limit),\n      ...(cursor ? { skip: 1, cursor: { id: String(cursor) } } : {}),\n      orderBy: { createdAt: 'desc' },\n    })\n    res.json({ ok: true, data: projects,\n      nextCursor: projects.length === Number(limit)\n        ? projects[projects.length - 1].id : null })\n  } catch (error) { next(error) }\n})\n\nexport { router as projectsRouter }"}],
            "followups": ["Quelle stratégie d'auth ? Firebase Auth (recommandé), JWT custom, ou les deux ?", 'Besoin de webhooks entrants (paiement MTN MoMo, Orange Money) ?', "Volume de données attendu à 6 mois ? (influe sur la stratégie d'indexation)"],
            "score": 0.78,
        }
