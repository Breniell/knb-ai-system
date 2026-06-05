import { PrismaClient } from "@prisma/client";

// Use a singleton to avoid multiple connections during hot-reload
const globalForPrisma = globalThis as unknown as { prisma?: PrismaClient };

let prisma: PrismaClient;
try {
  prisma = globalForPrisma.prisma ?? new PrismaClient({ log: [] });
  if (process.env.NODE_ENV !== "production") {
    globalForPrisma.prisma = prisma;
  }
} catch {
  // Prisma unavailable — create a no-op stub so the server still boots
  prisma = new Proxy({} as PrismaClient, {
    get: (_target, prop) => {
      if (prop === "$connect" || prop === "$disconnect") {
        return () => Promise.resolve();
      }
      return () => Promise.reject(new Error("Database not available"));
    },
  });
}

export { prisma };
