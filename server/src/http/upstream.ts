import { env } from "../config/env.js";

// 55s — laisse le temps au service de se réveiller (Render gratuit peut prendre 60s).
const AI_TIMEOUT_MS = 55_000;

export async function fetchAiService(path: string, init?: RequestInit) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), AI_TIMEOUT_MS);
  try {
    return await fetch(`${env.AI_SERVICE_PUBLIC_URL}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        "content-type": "application/json",
        ...(init?.headers ?? {}),
      },
    });
  } finally {
    clearTimeout(timer);
  }
}
