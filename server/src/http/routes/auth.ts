import { Router } from "express";

import { requireAuth } from "../../auth/requireAuth.js";
import { asyncHandler } from "../asyncHandler.js";
import { ok } from "../response.js";

export const authRouter = Router();

authRouter.get("/auth/me", requireAuth, asyncHandler(async (req, res) => {
  return ok(res, { ok: true, user: req.user });
}));

