import { applicationDefault, cert, getApps, initializeApp, type ServiceAccount } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";

import { env } from "../config/env.js";
import { logger } from "../lib/logger.js";

function normalizePrivateKey(value: string) {
  return value.replace(/\\n/g, "\n");
}

function serviceAccountFromJson(value: string): ServiceAccount {
  const parsed = JSON.parse(value) as {
    project_id?: string;
    projectId?: string;
    client_email?: string;
    clientEmail?: string;
    private_key?: string;
    privateKey?: string;
  };
  return {
    projectId: parsed.projectId ?? parsed.project_id ?? env.FIREBASE_PROJECT_ID,
    clientEmail: parsed.clientEmail ?? parsed.client_email,
    privateKey: normalizePrivateKey(parsed.privateKey ?? parsed.private_key ?? ""),
  };
}

function getCredential() {
  if (env.FIREBASE_SERVICE_ACCOUNT_JSON) {
    return cert(serviceAccountFromJson(env.FIREBASE_SERVICE_ACCOUNT_JSON));
  }
  if (env.FIREBASE_CLIENT_EMAIL && env.FIREBASE_PRIVATE_KEY) {
    return cert({
      projectId: env.FIREBASE_PROJECT_ID,
      clientEmail: env.FIREBASE_CLIENT_EMAIL,
      privateKey: normalizePrivateKey(env.FIREBASE_PRIVATE_KEY),
    });
  }
  // Reads GOOGLE_APPLICATION_CREDENTIALS from process.env (set by dotenv)
  return applicationDefault();
}

let _firebaseAuth: ReturnType<typeof getAuth> | null = null;
let _initError: Error | null = null;

try {
  const firebaseApp = getApps()[0] ?? initializeApp({
    credential: getCredential(),
    projectId: env.FIREBASE_PROJECT_ID,
    storageBucket: env.FIREBASE_STORAGE_BUCKET,
  });
  _firebaseAuth = getAuth(firebaseApp);
  logger.info("Firebase Admin SDK initialized");
} catch (err) {
  _initError = err instanceof Error ? err : new Error(String(err));
  logger.warn({ err }, "Firebase Admin SDK failed to initialize — token verification disabled");
}

export const firebaseAuth = _firebaseAuth;

export function verifyFirebaseToken(token: string) {
  if (!_firebaseAuth) {
    return Promise.reject(_initError ?? new Error("Firebase Admin not initialized"));
  }
  return _firebaseAuth.verifyIdToken(token);
}
