import request from "supertest";
import { describe, expect, it } from "vitest";

import { createApp } from "../app.js";

describe("health endpoint", () => {
  it("returns ok", async () => {
    const app = createApp();
    const res = await request(app).get("/healthz");
    expect(res.status).toBe(200);
  });
});

