/**
 * In-memory cache with TTL — replaces Redis for Firebase-only mode.
 * Expired entries are cleaned up automatically every 60 seconds.
 */

type CacheEntry = { value: unknown; expiresAt: number };

const store = new Map<string, CacheEntry>();

setInterval(() => {
  const now = Date.now();
  for (const [key, entry] of store) {
    if (entry.expiresAt > 0 && now > entry.expiresAt) {
      store.delete(key);
    }
  }
}, 60_000);

export const redis = {
  async set(key: string, value: string, mode?: string, ttl?: number): Promise<void> {
    const expiresAt = ttl && ttl > 0 ? Date.now() + ttl * 1000 : 0;
    store.set(key, { value, expiresAt });
  },

  async get(key: string): Promise<string | null> {
    const entry = store.get(key);
    if (!entry) return null;
    if (entry.expiresAt > 0 && Date.now() > entry.expiresAt) {
      store.delete(key);
      return null;
    }
    return String(entry.value);
  },

  async del(key: string): Promise<void> {
    store.delete(key);
  },

  async ping(): Promise<string> {
    return "PONG";
  },

  async quit(): Promise<void> {
    store.clear();
  },

  size(): number {
    return store.size;
  },
};
