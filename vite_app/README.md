# Cockpit Vite + TS

Migración progresiva del cockpit React del repo al stack moderno
**Vite 5 + React 18 + TypeScript 5**, conservando el sistema de
componentes propio (look industrial amarillo).

El bundle anterior (Babel-standalone, sin build) sigue funcionando en
`web/` como fallback — `web_server.py` prefiere `web/dist/` cuando
existe.

## Cómo correr

```bash
# Dev (hot reload) — el proxy reenvía /api/* a 127.0.0.1:8765
npm install
npm run dev          # http://localhost:5173/

# En otro terminal, el backend Python:
python web_server.py # http://127.0.0.1:8765/

# Build de producción → ../web/dist/
npm run build
```

Con `web/dist/index.html` presente, `python web_server.py` sirve la
versión moderna desde la raíz `/` y delega los `/api/*` a sus handlers
Python como hasta ahora.

## Estructura

```
vite_app/
├─ index.html                 — Vite entry HTML
├─ package.json               — react/react-dom + vite + typescript
├─ tsconfig.json              — strict, jsx: react-jsx
├─ vite.config.ts             — outDir → ../web/dist, proxy /api
└─ src/
   ├─ main.tsx                — bootstrap React
   ├─ App.tsx                 — landing con datos reales de /api/bootstrap
   ├─ api.ts                  — fetchBootstrap, aiChat, runPipeline
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

## Plan de migración

El bundle `web/` legacy tiene ~250 KB de JSX en 7 archivos que comparten
globals (`Sidebar`, `Btn`, …) por concatenación de scripts. La migración
a ESM se hace **por componente**, no en bloque:

1. **Identificar** un componente del legacy (`ui.jsx`, `shell.jsx`, …).
2. **Tipar** sus props en `src/components/<Name>.tsx` con TypeScript.
3. **Reexportar** desde `src/components/index.ts`.
4. **Borrar** el original del legacy cuando todas las páginas que lo
   usaban estén también migradas.

Componentes ya migrados: `Btn`, `Icon`, `Panel`, `Kpi`, `StatusDot`.

Pendientes (orden sugerido): `SourcePills`, `PageHeader`, `Sidebar`,
`Topbar`, `AIDrawer`, `TweaksPanel`, y luego cada `PageX`.

## Por qué Vite

- Build pipeline real (tree-shaking, code-splitting, sourcemaps)
- TypeScript estricto en lugar de globals implícitos
- Hot module reload durante desarrollo
- Babel-standalone fuera del navegador → carga inicial ~10× más rápida
