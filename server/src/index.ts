import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

import dotenv from "dotenv";

import { logger } from "./lib/logger.js";

async function main() {
  // Load .env from repo root in local dev (docker compose injects env vars).
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = path.dirname(__filename);
  dotenv.config({ path: path.resolve(__dirname, "../../.env") });

  const [{ env }, { prisma }, { redis }, { createApp }, { createSocketServer }] =
    await Promise.all([
      import("./config/env.js"),
      import("./db/prisma.js"),
      import("./cache/redis.js"),
      import("./app.js"),
      import("./sockets/index.js"),
    ]);

  const app = createApp();
  const server = http.createServer(app);
  createSocketServer(server);

  // Redis: always works (in-memory implementation)
  await redis.ping();
  logger.info("cache ready (in-memory)");

  // Database: non-fatal in dev — app runs without PostgreSQL
  try {
    await prisma.$connect();
    logger.info("database connected");
  } catch (err) {
    logger.warn(
      { err },
      "database unavailable - running without PostgreSQL. " +
      "Some features (user sync, AI execution history) will be disabled. " +
      "Start PostgreSQL or use Docker profile 'full' to enable."
    );
  }

  server.on("error", (err: NodeJS.ErrnoException) => {
    if (err.code === "EADDRINUSE") {
      logger.error(
        { port: env.SERVER_PORT },
        `Port ${env.SERVER_PORT} is already in use. ` +
        "Stop the process using it (Apache, another server, etc.) or change SERVER_PORT in .env"
      );
    } else {
      logger.error({ err }, "server error");
    }
    process.exit(1);
  });

  server.listen(env.SERVER_PORT, "0.0.0.0", () => {
    logger.info({ port: env.SERVER_PORT }, `KNB Server listening on http://localhost:${env.SERVER_PORT}`);
  });

  // Keep-alive : ping le service IA toutes les 10 min pour éviter qu'il s'endorme
  // sur le plan Render gratuit (spin-down après 15 min d'inactivité).
  if (env.NODE_ENV === "production") {
    const AI_KEEPALIVE_MS = 10 * 60 * 1000;
    setInterval(() => {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), 10_000);
      fetch(`${env.AI_SERVICE_PUBLIC_URL}/healthz`, { signal: ctrl.signal })
        .then((res) => { clearTimeout(t); logger.debug({ status: res.status }, "[keep-alive] ping AI service"); })
        .catch(() => { clearTimeout(t); logger.warn("[keep-alive] AI service ne répond pas"); });
    }, AI_KEEPALIVE_MS);
    logger.info("[keep-alive] actif — ping AI service toutes les 10 min");
  }

  const shutdown = async (signal: string) => {
    logger.info({ signal }, "graceful shutdown started");
    server.close(async () => {
      await Promise.allSettled([
        prisma.$disconnect().catch(() => {}),
        redis.quit(),
      ]);
      logger.info("graceful shutdown complete");
      process.exit(0);
    });
  };

  process.on("SIGINT", () => void shutdown("SIGINT"));
  process.on("SIGTERM", () => void shutdown("SIGTERM"));
}

main().catch((err) => {
  logger.error({ err }, "fatal startup error");
  process.exit(1);
});
