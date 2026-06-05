import { Router } from "express";

import { ok } from "../response.js";

export const healthRouter = Router();

healthRouter.get("/health", (req, res) => {
  ok(res, {
    ok: true,
    service: "server" as const,
    time: new Date().toISOString(),
    requestId: req.requestId ?? null
  });
});

