// Tipos de los handlers que App inyecta a las páginas.
export type NavFn = (page: string, payload?: string) => void;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type OpenAIFn = (ctx: any) => void;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type OpenFixFn = (ctx: any) => void;

// Rutas reales (relativas al repo) de los contenidos de un episodio.
export interface EpisodePaths {
  pdf: string | null;
  guion: string | null;
  escaleta: string | null;
  audio: string | null;
  video: string | null;
  logs: string[];
}

// Detalle del episodio desde GET /api/episode/<id>.
export interface EpisodeDetail {
  id: string;
  mod: string;
  kind: string;
  number: number | null;
  slug: string;
  title: string;
  dur: string;
  state: Record<string, string>;
  paths: EpisodePaths;
}
