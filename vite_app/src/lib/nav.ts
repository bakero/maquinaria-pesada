// Navegación del cockpit + enlaces al repositorio.
// Cada item de nav lleva `src`: los archivos del repo que lo implementan.

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
      { id: "home",     label: "Inicio",   icon: "home",    num: "00",
        src: ["cockpit/app.py", "cockpit/theme.py"] },
      { id: "master",   label: "Master",   icon: "grid",    num: "01", emph: true,
        src: ["cockpit/pages/0_🎓_Master.py", "cockpit/core/state.py", "cockpit/core/episodes.py"] },
      { id: "modulo",   label: "Módulo",   icon: "module",  num: "02",
        src: ["cockpit/pages/13_🎬_Modulo.py", "cockpit/core/episodes.py", "cockpit/core/paths.py"] },
      { id: "episodio", label: "Episodio", icon: "episode", num: "03",
        src: ["cockpit/pages/14_📼_Episodio.py", "cockpit/core/verifications.py", "cockpit/core/log_parser.py"] },
    ],
  },
  {
    label: "Pipeline",
    items: [
      { id: "pizarra",   label: "Pizarra",    icon: "pipe",   num: "04",
        src: ["cockpit/pages/15_🎨_Pizarra.py", "cockpit/core/pizarra.py", "cockpit/core/components_map.py"] },
      { id: "mapa",      label: "Mapa",       icon: "map",    num: "05",
        src: ["cockpit/pages/12_🗺️_Mapa.py", "cockpit/core/components_map.py", "cockpit/ui_map.py"] },
      { id: "conectores",label: "Conectores", icon: "plug",   num: "06",
        src: ["cockpit/pages/2_🔌_Conectores.py", "cockpit/connectors/"] },
      { id: "lanzador",  label: "Lanzador",   icon: "prompt", num: "07",
        src: ["cockpit/pages/3_📝_Generar_Prompt.py", "cockpit/core/prompt_builder.py", "cockpit/core/runner.py"] },
    ],
  },
  {
    label: "Recursos",
    items: [
      { id: "fuentes", label: "Fuentes",       icon: "folder", num: "08",
        src: ["cockpit/pages/4_📚_Fuentes.py", "PDFs/", "Guiones/", "escaletas/", "episodios/", "videopodcast/"] },
      { id: "player",  label: "Previsualizar", icon: "play",   num: "09",
        src: ["cockpit/pages/8_🎧_Previsualizar.py"] },
    ],
  },
  {
    label: "Observabilidad",
    items: [
      { id: "logs",      label: "Logs",      icon: "log",   num: "10",
        src: ["cockpit/pages/5_📜_Logs.py", "cockpit/core/log_parser.py", "cockpit/core/logger.py", "cockpit/core/monitor.py"] },
      { id: "optimizar", label: "Optimizar", icon: "brain", num: "11",
        src: ["cockpit/pages/10_🧠_Optimizar.py", "cockpit/core/optimization_advisor.py"] },
    ],
  },
  {
    label: "Difusión",
    items: [
      { id: "metricas", label: "Métricas", icon: "map", num: "12", emph: true,
        src: ["cockpit/pages/16_📡_Metricas.py", "cockpit/connectors/services/spotify.py",
              "cockpit/connectors/services/ivoox.py", "cockpit/connectors/services/linkedin.py",
              "cockpit/core/metrics_aggregator.py"] },
    ],
  },
  {
    label: "Cuenta",
    items: [
      { id: "consumo", label: "Consumo", icon: "coin",     num: "13",
        src: ["cockpit/pages/7_💰_Tokens.py", "cockpit/pages/11_💳_Economics.py",
              "cockpit/core/usage_tracker.py", "cockpit/core/economics.py"] },
      { id: "ajustes", label: "Ajustes", icon: "settings", num: "14",
        src: ["cockpit/pages/6_🔑_API_Keys.py", "cockpit/core/api_keys.py", "cockpit/core/sandbox.py"] },
    ],
  },
];

// Todas las páginas están cableadas en este prototipo.
export const WIRED = new Set<string>([
  "home", "master", "modulo", "episodio",
  "pizarra", "mapa", "conectores", "lanzador",
  "fuentes", "player", "logs", "optimizar",
  "metricas", "consumo", "ajustes",
]);

/** Archivos del repo que implementan una página de nav. */
export function srcFor(pageId: string): string[] {
  for (const g of NAV_GROUPS) {
    for (const it of g.items) if (it.id === pageId) return it.src || [];
  }
  return [];
}
