import type { NextFunction, Request, Response } from "express";

import { logger } from "../lib/logger.js";

export function auditLog(req: Request, _res: Response, next: NextFunction) {
  logger.info(
    {
      requestId: req.requestId,
      method: req.method,
      path: req.path,
      user: req.user?.sub ?? null,
    },
    "audit.request"
  );
  next();
}

