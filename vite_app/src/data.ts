// Capa de datos del cockpit.
//
// Los fixtures de abajo son la degradación elegante cuando no hay servidor.
// Cuando /api/bootstrap responde, `applyBootstrap()` sustituye los datos y
// los componentes los leen vía `getModules()` / `getEpisodes()`.
//
// Esto reemplaza el patrón anterior `window.MODULES = …`: nada de globals,
// una sola fuente de verdad importable.

import type {
  BootstrapPayload, Episode, EpisodeState, LiveProc, Module,
  RecentFile, Status, TokenData, UsageLogRow,
} from "./types";

// Helper para construir el estado por contenido de un episodio.
const st = (
  p: Status, g: Status, e: Status, a: Status, v: Status, l: Status,
): EpisodeState => ({ pdf: p, guion: g, escaleta: e, audio: a, video: v, logs: l });

export const FIXTURE_MODULES: Module[] = [
  { id: "M0",  name: "Cimientos",               short: "Qué es la IA, historia, panorámica",         pct: 100, status: "ok" },
  { id: "M1",  name: "Datos & ML clásico",      short: "Datasets, regresión, árboles, métricas",     pct: 100, status: "ok" },
  { id: "M2",  name: "Redes neuronales",        short: "Perceptrón, backprop, optimización",         pct: 100, status: "ok" },
  { id: "M3",  name: "Transformers",            short: "Atención, encoder/decoder, escalado",        pct:  72, status: "warn" },
  { id: "M4",  name: "LLMs y emergencia",       short: "Pretraining, leyes de escala, capacidades",  pct:  85, status: "ok" },
  { id: "M5",  name: "Fine-tuning & RLHF",      short: "SFT, DPO, RLHF, constitutional AI",          pct:  60, status: "warn" },
  { id: "M6",  name: "Prompting avanzado",      short: "CoT, few-shot, role, system design",         pct: 100, status: "ok" },
  { id: "M7",  name: "RAG & memoria",           short: "Embeddings, vector DBs, retrieval",          pct:  45, status: "warn" },
  { id: "M8",  name: "Agentes & herramientas",  short: "Tool use, ReAct, planning, loops",           pct:  30, status: "alert" },
  { id: "M9",  name: "Evaluación",              short: "Benchmarks, evals, MMLU, humaneval",         pct:  10, status: "empty" },
  { id: "M10", name: "Alineamiento",            short: "Safety, interpretabilidad, riesgos",         pct:   0, status: "empty" },
  { id: "M11", name: "Multimodalidad",          short: "Vision, audio, video, generación",           pct:  20, status: "empty" },
  { id: "M12", name: "Inferencia y eficiencia", short: "Quantization, KV-cache, batching",           pct:   0, status: "empty" },
  { id: "M13", name: "Despliegue & MLOps",      short: "Serving, monitoring, drift",                 pct:   0, status: "empty" },
  { id: "M14", name: "Estado del arte",         short: "Frontier models, AGI debate, futuro",        pct:   5, status: "empty" },
];

export const FIXTURE_EPISODES: Episode[] = [
  { id: "M0",    mod: "M0",  kind: "M", title: "Episodio M0 — Cimientos",              dur: "47:12", state: st("ok","ok","ok","ok","ok","ok") },
  { id: "M1",    mod: "M1",  kind: "M", title: "Episodio M1 — Datos y ML clásico",     dur: "52:08", state: st("ok","ok","ok","ok","ok","ok") },
  { id: "M2",    mod: "M2",  kind: "M", title: "Episodio M2 — Redes neuronales",       dur: "61:24", state: st("ok","ok","ok","ok","ok","ok") },
  { id: "M3",    mod: "M3",  kind: "M", title: "Episodio M3 — Transformers",           dur: "58:00", state: st("ok","ok","ok","ok","warn","ok") },
  { id: "M3_T1", mod: "M3",  kind: "T", title: "T1 — Mecanismo de atención",           dur: "14:32", state: st("ok","ok","ok","ok","ok","ok") },
  { id: "M3_T2", mod: "M3",  kind: "T", title: "T2 — Posicionales rotativos (RoPE)",   dur: "11:08", state: st("ok","ok","ok","alert","empty","alert") },
  { id: "M4",    mod: "M4",  kind: "M", title: "Episodio M4 — LLMs y emergencia",      dur: "63:45", state: st("ok","ok","ok","ok","warn","ok") },
  { id: "M5",    mod: "M5",  kind: "M", title: "Episodio M5 — Fine-tuning y RLHF",     dur: "54:00", state: st("ok","ok","ok","run","empty","ok") },
  { id: "M6",    mod: "M6",  kind: "M", title: "Episodio M6 — Prompting avanzado",     dur: "41:18", state: st("ok","ok","ok","ok","ok","ok") },
  { id: "M7",    mod: "M7",  kind: "M", title: "Episodio M7 — RAG y memoria",          dur: "—",     state: st("ok","ok","warn","empty","empty","warn") },
  { id: "M7_T1", mod: "M7",  kind: "T", title: "T1 — Estrategias de chunking",         dur: "—",     state: st("ok","ok","empty","empty","empty","empty") },
  { id: "M8",    mod: "M8",  kind: "M", title: "Episodio M8 — Agentes y herramientas", dur: "—",     state: st("ok","alert","empty","empty","empty","alert") },
  { id: "M8_T1", mod: "M8",  kind: "T", title: "T1 — ReAct y planning",                dur: "—",     state: st("ok","warn","empty","empty","empty","empty") },
  { id: "M8_T2", mod: "M8",  kind: "T", title: "T2 — Tool calling en Claude",          dur: "—",     state: st("ok","empty","empty","empty","empty","empty") },
  { id: "M9",    mod: "M9",  kind: "M", title: "Episodio M9 — Evaluación y benchmarks",dur: "—",     state: st("ok","empty","empty","empty","empty","empty") },
  { id: "M10",   mod: "M10", kind: "M", title: "Episodio M10 — Alineamiento",          dur: "—",     state: st("empty","empty","empty","empty","empty","empty") },
  { id: "M11",   mod: "M11", kind: "M", title: "Episodio M11 — Multimodalidad",        dur: "—",     state: st("ok","warn","empty","empty","empty","empty") },
  { id: "M11_T1",mod: "M11", kind: "T", title: "T1 — Vision encoders",                 dur: "—",     state: st("ok","empty","empty","empty","empty","empty") },
  { id: "M12",   mod: "M12", kind: "M", title: "Episodio M12 — Inferencia y eficiencia",dur: "—",    state: st("empty","empty","empty","empty","empty","empty") },
  { id: "M13",   mod: "M13", kind: "M", title: "Episodio M13 — Despliegue y MLOps",    dur: "—",     state: st("empty","empty","empty","empty","empty","empty") },
  { id: "M14",   mod: "M14", kind: "M", title: "Episodio M14 — Estado del arte",       dur: "—",     state: st("warn","empty","empty","empty","empty","empty") },
  { id: "M14_T1",mod: "M14", kind: "T", title: "T1 — Frontier models 2026",            dur: "—",     state: st("empty","empty","empty","empty","empty","empty") },
];

export interface GuionLine { who: "iago" | "maria"; text: string; }

export const GUION_PREVIEW: GuionLine[] = [
  { who: "iago",  text: "Vale María, hoy nos metemos con los Transformers. Pero antes de la arquitectura, una pregunta: ¿qué era lo que NO funcionaba en las RNN?" },
  { who: "maria", text: "Buena entrada. El problema era el paralelismo. Las RNN procesaban tokens uno detrás de otro, en secuencia. No podías meterle 64 GPUs y que volaran." },
  { who: "iago",  text: "Y aparece el paper de 2017, “Attention is all you need”. Atención como mecanismo central." },
  { who: "maria", text: "Exacto. Lo bonito de la atención es que es una operación matricial, totalmente paralela. Cada token puede mirar a todos los otros en una sola pasada." },
  { who: "iago",  text: "Vamos a desglosarlo: query, key, value. ¿Qué es cada uno en intuición?" },
  { who: "maria", text: "Imagina una biblioteca. La query es la pregunta que llevas. Las keys son las etiquetas de los lomos. Los values, los libros. Atención = encontrar las etiquetas que matchean tu pregunta y devolverte los libros ponderados." },
];

export interface Check { id: string; name: string; status: Status; detail: string; }

export const CHECKS_M3: Check[] = [
  { id: "c1", name: "PDF presente y legible",           status: "ok",    detail: "PDFs/M3.pdf · 2.4 MB · 18 páginas" },
  { id: "c2", name: "Guion completo (no truncado)",     status: "ok",    detail: "9842 palabras · 142 turnos" },
  { id: "c3", name: "Diálogo balanceado Iago/María",    status: "ok",    detail: "Iago 48% · María 52%" },
  { id: "c4", name: "Escaleta sin secciones vacías",    status: "ok",    detail: "8/8 bloques con contenido" },
  { id: "c5", name: "Audio MP3 sin gaps",               status: "warn",  detail: "1 silencio de 4.2s @ 23:18" },
  { id: "c6", name: "Audio respeta SSML pauses",        status: "ok",    detail: "12/12 pauses correctos" },
  { id: "c7", name: "Loudness LUFS -16 ±1",             status: "ok",    detail: "-15.8 LUFS" },
  { id: "c8", name: "Vídeo escena→texto alineado",      status: "alert", detail: "Drift de 1.8s @ 41:22 — re-render" },
  { id: "c9", name: "Logs sin ERROR",                   status: "ok",    detail: "0 errors · 3 warnings" },
  { id: "c10",name: "Validación dual (Claude vs GPT)",  status: "ok",    detail: "Acuerdo 94% · 6 discrepancias menores" },
];

export const FIXTURE_LIVE_PROC: LiveProc[] = [
  { id: "p1", cmd: "generar_episodio_v2.py M5", pid: 41207, t: "00:04:22", cost: "0.42€" },
  { id: "p2", cmd: "validar_episodio.py M3",    pid: 41318, t: "00:00:14", cost: "0.01€" },
];

export const FIXTURE_RECENT_FILES: RecentFile[] = [
  { path: "Guiones/M5_guion.txt",     t: "hace 12 s",  by: "Claude" },
  { path: "episodios/M3_T1_v4.mp3",   t: "hace 1 min", by: "ElevenLabs" },
  { path: "escaletas/M5.md",          t: "hace 3 min", by: "Claude" },
  { path: "logs/2026-05-12_M3.jsonl", t: "hace 4 min", by: "runner" },
];

export const FIXTURE_AI_LOG: UsageLogRow[] = [
  { t: "12:42:18", model: "haiku-4.5",   kind: "Mejorar con IA", tok:  1240, cost: 0.003 },
  { t: "12:41:50", model: "sonnet-4.6",  kind: "Generar guion",  tok: 14820, cost: 0.198 },
  { t: "12:39:02", model: "haiku-4.5",   kind: "Asistente",      tok:   820, cost: 0.002 },
  { t: "12:36:11", model: "sonnet-4.6",  kind: "Generar guion",  tok: 12100, cost: 0.162 },
  { t: "12:32:48", model: "gpt-4o-mini", kind: "Debate dual",    tok:  4400, cost: 0.001 },
];

export const FIXTURE_TOKEN_DATA: TokenData = {
  total_30d: 18_420_000,
  cost_30d: 142.18,
  budget: 250,
  byModel: [
    { model: "claude-haiku-4.5",  tokens: 8_120_000, cost: 18.40, share: 44 },
    { model: "claude-sonnet-4.6", tokens: 5_840_000, cost: 78.20, share: 32 },
    { model: "claude-opus-4.7",   tokens:   780_000, cost: 36.80, share:  4 },
    { model: "gpt-4o-mini",       tokens: 2_960_000, cost:  4.80, share: 16 },
    { model: "whisper-local",     tokens:   720_000, cost:  0.00, share:  4 },
  ],
  byKind: [
    { kind: "Generación de guiones", pct: 52 },
    { kind: "Validación dual",       pct: 28 },
    { kind: "Mejorar con IA",        pct: 12 },
    { kind: "Asistente",             pct:  5 },
    { kind: "Otros",                 pct:  3 },
  ],
  log: FIXTURE_AI_LOG,
};

// ── Estado mutable: fixtures por defecto, sustituidos por el bootstrap ──
let _modules: Module[] = FIXTURE_MODULES;
let _episodes: Episode[] = FIXTURE_EPISODES;
let _liveProc: LiveProc[] = FIXTURE_LIVE_PROC;
let _recentFiles: RecentFile[] = FIXTURE_RECENT_FILES;
let _tokenData: TokenData = FIXTURE_TOKEN_DATA;
let _aiLog: UsageLogRow[] = FIXTURE_AI_LOG;

/** Sustituye los datos con la respuesta real de /api/bootstrap. */
export function applyBootstrap(d: Partial<BootstrapPayload> | null): void {
  if (!d) return;
  if (Array.isArray(d.MODULES) && d.MODULES.length) _modules = d.MODULES;
  if (Array.isArray(d.EPISODES) && d.EPISODES.length) _episodes = d.EPISODES;
  if (Array.isArray(d.LIVE_PROC)) _liveProc = d.LIVE_PROC;
  if (Array.isArray(d.RECENT_FILES) && d.RECENT_FILES.length) _recentFiles = d.RECENT_FILES;
  if (d.TOKEN_DATA && Array.isArray(d.TOKEN_DATA.byModel) && d.TOKEN_DATA.byModel.length) {
    _tokenData = d.TOKEN_DATA;
    if (Array.isArray(d.TOKEN_DATA.log) && d.TOKEN_DATA.log.length) _aiLog = d.TOKEN_DATA.log;
  }
}

export function getModules(): Module[] { return _modules; }
export function getEpisodes(): Episode[] { return _episodes; }
export function getModule(id: string | null | undefined): Module | undefined {
  return _modules.find((m) => m.id === id);
}
export function getEpisode(id: string | null | undefined): Episode | undefined {
  return _episodes.find((e) => e.id === id);
}
export function getLiveProc(): LiveProc[] { return _liveProc; }
export function getRecentFiles(): RecentFile[] { return _recentFiles; }
export function getTokenData(): TokenData { return _tokenData; }
export function getAILog(): UsageLogRow[] { return _aiLog; }
