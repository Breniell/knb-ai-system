import type { NextFunction, Request, Response } from "express";

import { error } from "../http/response.js";

export type UserRole = "ADMIN" | "MANAGER" | "MEMBER";

export function requireRole(roles: UserRole[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    const role = (req.user?.role ?? "MEMBER") as UserRole;
    if (!roles.includes(role)) return error(res, "FORBIDDEN", "Insufficient permissions", 403);
    next();
  };
}

