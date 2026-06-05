import { Router } from "express";

import { healthRouter } from "./health.js";
import { authRouter } from "./auth.js";
import { aiRouter } from "./ai.js";
import { tasksRouter } from "./tasks.js";
import { projectsRouter } from "./projects.js";
import { analyticsRouter } from "./analytics.js";
import { monitoringRouter } from "./monitoring.js";
import { memoryRouter } from "./memory.js";
import { learningRouter } from "./learning.js";

export const apiRouter = Router();

apiRouter.use(healthRouter);
apiRouter.use(authRouter);
apiRouter.use(aiRouter);
apiRouter.use(projectsRouter);
apiRouter.use(tasksRouter);
apiRouter.use(analyticsRouter);
apiRouter.use(monitoringRouter);
apiRouter.use(memoryRouter);
apiRouter.use(learningRouter);
