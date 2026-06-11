import { env } from "../config/env.js";

// 90s — OpenRouter free tier peut prendre 60-80s sur un modèle lourd.
const AI_TIMEOUT_MS = 90_000;

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
