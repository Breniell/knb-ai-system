import { env } from "../config/env";
import { auth } from "./firebase";

export type ApiErrorShape = {
  error: { code: string; message: string; requestId?: string };
};

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  // Get Firebase ID token if auth is available, otherwise proceed without token
  let token: string | undefined;
  try {
    token = auth?.currentUser ? await auth.currentUser.getIdToken() : undefined;
  } catch {
    token = undefined;
  }

  const res = await fetch(`${env.apiUrl}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(token ? { authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
    credentials: "include",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Request failed: ${res.status}`);
  }

  return (await res.json()) as T;
}
