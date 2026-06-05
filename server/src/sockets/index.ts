import type { Server as HttpServer } from "node:http";
import { Server } from "socket.io";

import { env } from "../config/env.js";
import { logger } from "../lib/logger.js";

export type SocketServer = ReturnType<typeof createSocketServer>;

export function createSocketServer(httpServer: HttpServer) {
  const io = new Server(httpServer, {
    cors: {
      origin: env.CORS_ORIGINS.split(",").map((s) => s.trim()),
      credentials: true
    }
  });

  io.on("connection", (socket) => {
    logger.info({ socketId: socket.id }, "socket connected");
    socket.emit("server:hello", { ok: true, time: new Date().toISOString() });

    socket.on("disconnect", (reason) => {
      logger.info({ socketId: socket.id, reason }, "socket disconnected");
    });
  });

  return io;
}

