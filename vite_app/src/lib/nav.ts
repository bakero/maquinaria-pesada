// Navegación del cockpit + enlaces al repositorio.
//
// El cockpit v3 tiene 3 secciones en el top-nav (Producción · Datos ·
// Sistema). Los items con sub-tabs viven dentro de cada sección. Cada
// item lleva `src`: los archivos del repo que lo implementan, usados
// por el panel de "ver código en GitHub" desde el mapa de componentes.

export const REPO = "https://github.com/bakero/maquinaria-pesada";
export const REPO_REF = "master";
export const ghLink = (path: string): string => `${REPO}/blob/${REPO_REF}/${path}`;

export interface NavItem {
  id: string;
  label: string;
  icon: string;
  num: string;
  emph?: boolean;
  src?: string[];
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
  {
    label: "Producción",
    items: [
      { id: "produccion", label: "Producción", icon: "grid",   num: "01", emph: true,
        src: ["vite_app/src/pages/PageProduccion.tsx",
              "cockpit/core/episodes.py", "cockpit/core/state.py",
              "web_server.py"] },
      { id: "modulo",     label: "Módulo",     icon: "module", num: "02",
        src: ["vite_app/src/pages/PageModuloTema.tsx",
              "cockpit/core/episodes.py", "cockpit/core/paths.py",
              "web_server.py"] },
      { id: "tema",       label: "Tema",       icon: "episode", num: "03",
        src: ["vite_app/src/pages/PageModuloTema.tsx",
              "cockpit/core/verifications.py", "cockpit/core/log_parser.py",
              "web_server.py"] },
    ],
  },
  {
    label: "Datos",
    items: [
      { id: "consumo",   label: "Coste IA",     icon: "coin",  num: "04",
        src: ["vite_app/src/pages/PageConsumo.jsx",
              "cockpit/core/usage_tracker.py", "cockpit/core/economics.py"] },
      { id: "metricas",  label: "Difusión",     icon: "map",   num: "05",
        src: ["vite_app/src/pages/PageMetricas.jsx",
              "cockpit/connectors/analytics/spotify.py",
              "cockpit/connectors/analytics/ivoox.py",
              "cockpit/connectors/analytics/linkedin.py"] },
      { id: "optimizar", label: "Optimización", icon: "brain", num: "06",
        src: ["vite_app/src/pages/PageOptimizar.jsx",
              "cockpit/core/optimization_advisor.py"] },
      { id: "logs",      label: "Logs",         icon: "log",   num: "07",
        src: ["vite_app/src/pages/PageLogs.jsx",
              "cockpit/core/log_parser.py", "cockpit/core/monitor.py"] },
    ],
  },
  {
    label: "Sistema",
    items: [
      { id: "conectores", label: "Conectores",       icon: "plug",     num: "08",
        src: ["vite_app/src/pages/PageConectores.jsx",
              "cockpit/connectors/"] },
      { id: "lanzador",   label: "Lanzar pipeline",  icon: "prompt",   num: "09",
        src: ["vite_app/src/pages/PageLanzador.jsx",
              "cockpit/core/prompt_builder.py", "cockpit/core/runner.py"] },
      { id: "fuentes",    label: "Fuentes",          icon: "folder",   num: "10",
        src: ["vite_app/src/pages/PageFuentes.jsx",
              "PDFs/", "Guiones/", "escaletas/", "episodios/", "videopodcast/"] },
      { id: "mapa",       label: "Mapa",             icon: "map",      num: "11",
        src: ["vite_app/src/pages/PageMapa.jsx",
              "cockpit/core/components_map.py"] },
      { id: "ajustes",    label: "Ajustes",          icon: "settings", num: "12",
        src: ["vite_app/src/pages/PageAjustes.jsx",
              "cockpit/core/api_keys.py", "cockpit/core/sandbox.py"] },
    ],
  },
];

// Páginas válidas que el router del shell sabe renderizar.
export const WIRED = new Set<string>([
  // v3 — 3 destinos del top-nav industrial + drill-downs
  "produccion", "modulo", "tema", "datos", "sistema",
  // sub-pages alcanzables vía palette / deep-link (renderizadas dentro de
  // los wrappers Datos / Sistema)
  "consumo", "metricas", "optimizar", "logs",
  "conectores", "lanzador", "fuentes", "mapa", "ajustes",
]);

/** Archivos del repo que implementan una página de nav. */
export function srcFor(pageId: string): string[] {
  for (const g of NAV_GROUPS) {
    for (const it of g.items) if (it.id === pageId) return it.src || [];
  }
  return [];
}
