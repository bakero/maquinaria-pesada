# Cockpit Vite + TS

Cockpit React del repo sobre stack moderno
**Vite 5 + React 18 + TypeScript 5**, con un sistema de componentes
propio (look industrial amarillo).

Es la **única** versión de la app visual. El antiguo bundle
Babel-standalone (`web/`) fue eliminado; `web_server.py` sirve el build
de Vite desde `vite_app/dist/`.

## Cómo correr

```bash
# Dev (hot reload) — el proxy reenvía /api/* a 127.0.0.1:8765
npm install
npm run dev          # http://localhost:5173/

# En otro terminal, el backend Python:
python web_server.py # http://127.0.0.1:8765/

# Build de producción → vite_app/dist/
npm run build
```

Con `vite_app/dist/index.html` presente, `python web_server.py` sirve la
app desde la raíz `/` y delega los `/api/*` a sus handlers Python.

## Estructura

```
vite_app/
├─ index.html                 — Vite entry HTML
├─ package.json               — react/react-dom + vite + typescript
├─ tsconfig.json              — strict, jsx: react-jsx
├─ vite.config.ts             — outDir → dist/, proxy /api
├─ public/assets/pdf/         — PDFs resumen servidos como estáticos
└─ src/
   ├─ main.tsx                — bootstrap React
   ├─ cockpit-bundle.jsx      — app completa (páginas, sidebar, drawers)
   ├─ api.ts                  — fetchBootstrap, aiChat, runPipeline,
   │                            generateGuion, fetchGenLog
   ├─ types.ts                — espejo del JSON del backend
   ├─ styles.css              — design tokens + look industrial
   └─ components/             — sistema de componentes tipado
      ├─ Btn.tsx
      ├─ Icon.tsx             — catálogo cerrado de 20 iconos
      ├─ Kpi.tsx
      ├─ Panel.tsx
      ├─ StatusDot.tsx
      └─ index.ts             — barrel export
```

## Generación de guion por episodio

Las páginas Módulo y Episodio incluyen `GenGuionPanel`: lanza
`generar_guion.py` / `generar_guion_t.py` para **un episodio concreto**
(`POST /api/episode/<id>/generate`) y muestra la traza de validación y
regeneración (`GET /api/episode/<id>/gen-log`): intentos, issues
hard/soft y veredicto. El mapeo episodio → PDF + script vive en
`cockpit/core/episode_sources.py`, compartido con `lanzar_guiones.py`.

## Por qué Vite

- Build pipeline real (tree-shaking, code-splitting, sourcemaps)
- TypeScript estricto en lugar de globals implícitos
- Hot module reload durante desarrollo
- Sin Babel-standalone en el navegador → carga inicial ~10× más rápida
