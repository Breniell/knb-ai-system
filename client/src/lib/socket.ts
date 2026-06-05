import { io, type Socket } from "socket.io-client";

import { env } from "../config/env";

let socket: Socket | null = null;

export function getSocket(): Socket {
  if (!socket) {
    socket = io(env.wsUrl, {
      transports: ["websocket"],
      autoConnect: true,
    });
  }
  return socket;
}

