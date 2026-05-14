// Carpeta canónica por tipo de contenido — el filesystem es la única fuente
// de verdad. Compartido por las páginas Master, Módulo y Episodio.

export const KINDS = ["pdf", "guion", "escaleta", "audio", "video", "logs"] as const;
export type Kind = (typeof KINDS)[number];

export interface SourceDef {
  folder: string;
  ext: string;
  label: string;
  icon: string;
}

export const SOURCES: Record<string, SourceDef> = {
  pdf:      { folder: "PDFs/",         ext: ".pdf",   label: "PDF",            icon: "doc" },
  guion:    { folder: "Guiones/",      ext: ".txt",   label: "Guion",          icon: "doc" },
  escaleta: { folder: "escaletas/",    ext: ".md",    label: "Escaleta",       icon: "doc" },
  audio:    { folder: "episodios/",    ext: ".mp3",   label: "Audio",          icon: "play" },
  video:    { folder: "videopodcast/", ext: ".mp4",   label: "Vídeo",          icon: "play" },
  logs:     { folder: "logs/",         ext: ".jsonl", label: "Logs",           icon: "log" },
  checks:   { folder: "(cualquiera)",  ext: "",       label: "Verificaciones", icon: "check" },
};

export function pathOf(kind: string, epId: string): string {
  const s = SOURCES[kind];
  if (!s) return "";
  return `${s.folder}${epId}${s.ext}`;
}
