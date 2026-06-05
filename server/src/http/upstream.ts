import { env } from "../config/env.js";

export async function fetchAiService(path: string, init?: RequestInit) {
  return fetch(`${env.AI_SERVICE_PUBLIC_URL}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {})
    }
  });
}
