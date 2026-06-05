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
