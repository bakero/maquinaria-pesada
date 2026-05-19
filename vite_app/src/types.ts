// Tipos compartidos para el cockpit · espejan el JSON que devuelve
// /api/bootstrap (ver web_server.py · bootstrap_payload).

export type Status = "ok" | "warn" | "alert" | "empty" | "run";

export interface Module {
  id: string;
  name: string;
  short: string;
  pct: number;
  status: Status;
}

export interface EpisodeState {
  pdf: Status;
  guion: Status;
  escaleta: Status;
  audio: Status;
  video: Status;
  logs: Status;
}

export interface Episode {
  id: string;
  mod: string;
  // M = episodio de módulo paraguas; T = tema; S = Short (píldora de glosario,
  // sin módulo padre, formato corto 60-90 s para Reels/Shorts/TikTok).
  kind: "M" | "T" | "S";
  title: string;
  dur: string;
  state: EpisodeState;
  term?: string;            // solo para Shorts: el término del glosario
}

export interface LiveProc {
  id: string;
  cmd: string;
  pid: number;
  t: string;
  cost: string;
}

export interface RecentFile {
  path: string;
  t: string;
  by: string;
}

export interface ModelUsage {
  model: string;
  tokens: number;
  cost: number;
  share: number;
}

export interface KindShare {
  kind: string;
  pct: number;
}

export interface UsageLogRow {
  t: string;
  model: string;
  kind: string;
  tok: number;
  cost: number;
}

export interface TokenData {
  total_30d: number;
  cost_30d: number;
  budget: number;
  byModel: ModelUsage[];
  byKind: KindShare[];
  log: UsageLogRow[];
}

export interface VersionInfo { branch: string; sha: string; }

export interface BootstrapPayload {
  MODULES: Module[];
  EPISODES: Episode[];
  SHORTS: Episode[];        // kind="S", sin módulo padre
  LIVE_PROC: LiveProc[];
  RECENT_FILES: RecentFile[];
  TOKEN_DATA: TokenData;
  ECONOMICS: unknown;
  VERSION?: VersionInfo;
}

export interface AIUsage {
  model: string;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  latency_ms: number;
}

export interface AIChatResponse {
  ok: boolean;
  text: string;
  usage: AIUsage | null;
}
