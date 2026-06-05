import type { NextFunction, Request, Response } from "express";
import type { DecodedIdToken } from "firebase-admin/auth";

import { env } from "../config/env.js";
import { prisma } from "../db/prisma.js";
import { error } from "../http/response.js";
import { firebaseAuth, verifyFirebaseToken } from "./firebase.js";
import type { UserRole } from "./rbac.js";

const validRoles = new Set<UserRole>(["ADMIN", "MANAGER", "MEMBER"]);

// Dev no-auth mode is active when explicitly enabled, OR (in non-production)
// when the Firebase Admin SDK could not initialize — meaning token
// verification is impossible and demanding one would lock the user out.
const devNoAuth = env.DEV_NO_AUTH || (env.NODE_ENV !== "production" && firebaseAuth === null);

function bootstrapAdminEmails() {
  return env.BOOTSTRAP_ADMIN_EMAILS.split(",").map((e) => e.trim().toLowerCase()).filter(Boolean);
}

function roleFromToken(claims: DecodedIdToken): UserRole {
  const roleClaim = typeof claims.role === "string" ? claims.role.toUpperCase() : undefined;
  if (roleClaim && validRoles.has(roleClaim as UserRole)) {
    return roleClaim as UserRole;
  }
  const email = claims.email?.toLowerCase();
  if (email && bootstrapAdminEmails().includes(email)) {
    return "ADMIN";
  }
  return "MEMBER";
}

async function syncFirebaseUser(claims: DecodedIdToken, role: UserRole) {
  const email = claims.email ?? `${claims.uid}@firebase.local`;
  try {
    const existingById = await prisma.user.findUnique({ where: { id: claims.uid } });
    if (existingById) {
      await prisma.user.update({ where: { id: claims.uid }, data: { email, name: claims.name ?? null, role } });
      return;
    }
    const existingByEmail = await prisma.user.findUnique({ where: { email } });
    if (existingByEmail) {
      await prisma.user.update({ where: { email }, data: { id: claims.uid, name: claims.name ?? null, role } });
      return;
    }
    await prisma.user.create({ data: { id: claims.uid, email, name: claims.name ?? null, role } });
  } catch {
    // DB unavailable — user is authenticated via Firebase, continue without DB sync
  }
}

export function requireAuth(req: Request, res: Response, next: NextFunction) {
  const header = req.header("authorization");
  const token = header?.startsWith("Bearer ") ? header.slice("Bearer ".length) : null;

  if (!token) {
    // No token: in dev no-auth mode, proceed with a local dev identity so the
    // client's no-auth mode works end-to-end. Otherwise reject.
    if (devNoAuth) {
      req.user = { sub: "dev-user", email: "dev@knb.local", role: "ADMIN" };
      return next();
    }
    return error(res, "UNAUTHORIZED", "Missing bearer token", 401);
  }

  void verifyFirebaseToken(token)
    .then(async (claims) => {
      const role = roleFromToken(claims);
      // Best-effort DB sync — does not block auth if DB is unavailable
      await syncFirebaseUser(claims, role);
      req.user = { sub: claims.uid, email: claims.email, role };
      next();
    })
    .catch(() => error(res, "UNAUTHORIZED", "Invalid Firebase token", 401));
}
