import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  // Load .env from the monorepo root (one level up from client/)
  envDir: "../",
  server: {
    port: 5173,
    strictPort: true,
    host: true,
  },
});
