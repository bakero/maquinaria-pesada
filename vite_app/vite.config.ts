import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  // Build output: ../web/dist — el servidor (web_server.py) lo detecta y lo
  // sirve preferentemente sobre el bundle babel-standalone heredado.
  build: {
    outDir: path.resolve(__dirname, "../web/dist"),
    emptyOutDir: true,
    sourcemap: true,
  },
  server: {
    port: 5173,
    // Durante el dev (`npm run dev`) las llamadas a /api/* las atiende
    // web_server.py en :8765
    proxy: {
      "/api": "http://127.0.0.1:8765",
    },
  },
});
