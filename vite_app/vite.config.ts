import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  // Build output: vite_app/dist — el servidor (web_server.py) lo sirve como
  // estático. Es la única versión de la app visual (ya no hay legacy babel).
  build: {
    outDir: path.resolve(__dirname, "dist"),
    emptyOutDir: true,
    sourcemap: true,
  },
  server: {
    port: 5173,
    // Durante el dev (`npm run dev`) las rutas que sirve web_server.py
    // las reenviamos a :8765. Si falta alguna entrada aquí, el dev server
    // hace fallback al index.html (SPA) y produce el bug clásico de
    // "el PDF/guion/audio devuelve <!doctype html>".
    proxy: {
      "/api":   "http://127.0.0.1:8765",   // JSON + SSE /api/stream
      "/files": "http://127.0.0.1:8765",   // PDFs, guiones, audios, vídeos
    },
  },
});
