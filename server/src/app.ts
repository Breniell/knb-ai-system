import cors from "cors";
import express from "express";
import helmet from "helmet";
import pinoHttp from "pino-http";

import { env } from "./config/env.js";
import { apiRouter } from "./http/routes/index.js";
import { error } from "./http/response.js";
import { logger } from "./lib/logger.js";
import { auditLog } from "./middlewares/auditLog.js";
import { apiRateLimit } from "./middlewares/rateLimit.js";
import { requestContext } from "./middlewares/requestContext.js";

export function createApp() {
  const app = express();

  app.disable("x-powered-by");
  app.use(helmet());
  app.use(requestContext);
  // pino-http types diverge from the runtime API in v10 — cast to any
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  app.use((pinoHttp as any)({
    logger,
    customProps: (req: express.Request) => ({ requestId: (req as any).requestId }),
  }));

  app.use(
    cors({
      origin: env.CORS_ORIGINS.split(",").map((s) => s.trim()),
      credentials: true
    })
  );
  app.use(express.json({ limit: "1mb" }));
  app.use(apiRateLimit);
  app.use(auditLog);

  app.get("/healthz", (_req, res) => res.status(200).send("ok"));

  app.use("/api", apiRouter);

  app.use((err: unknown, req: express.Request, res: express.Response, _next: express.NextFunction) => {
    logger.error({ err, requestId: req.requestId }, "request failed");
    return error(res, "INTERNAL_ERROR", "Internal server error", 500);
  });

  return app;
}

