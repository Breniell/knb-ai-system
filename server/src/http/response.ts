import type { Response } from "express";

export function ok<T>(res: Response, data: T) {
  return res.status(200).json(data);
}

export function error(res: Response, code: string, message: string, status = 400) {
  return res.status(status).json({
    error: {
      code,
      message,
      requestId: res.getHeader("x-request-id")
    }
  });
}

