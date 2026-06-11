import { env } from "../config/env.js";
import { logger } from "../lib/logger.js";

const AI_TIMEOUT_MS = 120_000;
const WAKE_TIMEOUT_MS = 75_000;

function fetchWithTimeout(url: string, init: RequestInit | undefined, timeoutMs: number): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  return fetch(url, {
    ...init,
    signal: controller.signal,
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {}),
    },
  }).finally(() => clearTimeout(timer));
}

async function wakeAiService(): Promise<boolean> {
  const deadline = Date.now() + WAKE_TIMEOUT_MS;
  while (Date.now() < deadline) {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 15_000);
      const res = await fetch(`${env.AI_SERVICE_PUBLIC_URL}/healthz`, { signal: controller.signal })
        .finally(() => clearTimeout(timer));
      if (res.ok) return true;
    } catch {
      // service not yet up
    }
    await new Promise((resolve) => setTimeout(resolve, 5_000));
  }
  return false;
}

export async function fetchAiService(path: string, init?: RequestInit): Promise<Response> {
  const url = `${env.AI_SERVICE_PUBLIC_URL}${path}`;
  try {
    return await fetchWithTimeout(url, init, AI_TIMEOUT_MS);
  } catch (firstErr) {
    logger.warn({ err: firstErr }, "[upstream] AI service inaccessible — tentative de réveil (cold start Render)");
    const awake = await wakeAiService();
    if (!awake) {
      throw firstErr;
    }
    logger.info("[upstream] AI service réveillé — nouvelle tentative");
    return fetchWithTimeout(url, init, AI_TIMEOUT_MS);
  }
}
