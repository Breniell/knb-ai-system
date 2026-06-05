import { nanoid } from "nanoid";
import type { NextFunction, Request, Response } from "express";

declare global {
  // eslint-disable-next-line no-var
  var __requestId: string | undefined;
}

export function requestContext(req: Request, res: Response, next: NextFunction) {
  const requestId = (req.header("x-request-id") || nanoid()) as string;
  res.setHeader("x-request-id", requestId);
  (req as Request & { requestId: string }).requestId = requestId;
  next();
}

