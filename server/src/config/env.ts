import { z } from "zod";

// Coerce empty strings to undefined so .default() kicks in
function strOrDefault(defaultVal: string) {
  return z.string().transform(v => v || defaultVal).default(defaultVal);
}

const EnvSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  SERVER_PORT: z.coerce.number().default(3001),
  DATABASE_URL: strOrDefault("postgresql://knb:knb_password@localhost:5432/knb?schema=public"),
  REDIS_URL: strOrDefault("redis://localhost:6379"),
  QDRANT_URL: strOrDefault("http://qdrant:6333"),
  FIREBASE_PROJECT_ID: strOrDefault("knb-ai-system"),
  FIREBASE_STORAGE_BUCKET: strOrDefault("knb-ai-system.firebasestorage.app"),
  FIREBASE_SERVICE_ACCOUNT_JSON: z.string().optional(),
  FIREBASE_CLIENT_EMAIL: z.string().optional(),
  FIREBASE_PRIVATE_KEY: z.string().optional(),
  CORS_ORIGINS: strOrDefault("http://localhost:5173"),
  AI_SERVICE_PUBLIC_URL: strOrDefault("http://localhost:8000"),
  BOOTSTRAP_ADMIN_EMAILS: strOrDefault("admin@knb.local"),
  // When true, API routes accept requests without a Firebase token and inject a
  // local dev user. This matches the client's "no-auth mode" (empty
  // VITE_FIREBASE_API_KEY) so the whole stack is usable locally with zero
  // Firebase setup. MUST stay false in production.
  DEV_NO_AUTH: z
    .string()
    .optional()
    .transform((v) => v === "true" || v === "1")
    .default("false"),
});

export type Env = z.infer<typeof EnvSchema>;

export const env: Env = EnvSchema.parse(process.env);
