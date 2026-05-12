// data.jsx — Fixtures for Maquinaria Pesada cockpit
// 22 episodios = 15 M + 7 T

const MODULES = [
  { id: "M0",  name: "Cimientos",              short: "Qué es la IA, historia, panorámica",          pct: 100, status: "ok" },
  { id: "M1",  name: "Datos & ML clásico",     short: "Datasets, regresión, árboles, métricas",      pct: 100, status: "ok" },
  { id: "M2",  name: "Redes neuronales",       short: "Perceptrón, backprop, optimización",          pct: 100, status: "ok" },
  { id: "M3",  name: "Transformers",           short: "Atención, encoder/decoder, escalado",         pct:  72, status: "warn" },
  { id: "M4",  name: "LLMs y emergencia",      short: "Pretraining, leyes de escala, capacidades",   pct:  85, status: "ok" },
  { id: "M5",  name: "Fine-tuning & RLHF",     short: "SFT, DPO, RLHF, constitutional AI",           pct:  60, status: "warn" },
  { id: "M6",  name: "Prompting avanzado",     short: "CoT, few-shot, role, system design",          pct: 100, status: "ok" },
  { id: "M7",  name: "RAG & memoria",          short: "Embeddings, vector DBs, retrieval",           pct:  45, status: "warn" },
  { id: "M8",  name: "Agentes & herramientas", short: "Tool use, ReAct, planning, loops",            pct:  30, status: "alert" },
  { id: "M9",  name: "Evaluación",             short: "Benchmarks, evals, MMLU, humaneval",          pct:  10, status: "empty" },
  { id: "M10", name: "Alineamiento",           short: "Safety, interpretabilidad, riesgos",          pct:   0, status: "empty" },
  { id: "M11", name: "Multimodalidad",         short: "Vision, audio, video, generación",            pct:  20, status: "empty" },
  { id: "M12", name: "Inferencia y eficiencia",short: "Quantization, KV-cache, batching",            pct:   0, status: "empty" },
  { id: "M13", name: "Despliegue & MLOps",     short: "Serving, monitoring, drift",                  pct:   0, status: "empty" },
  { id: "M14", name: "Estado del arte",        short: "Frontier models, AGI debate, futuro",         pct:   5, status: "empty" },
];

// Tipos de contenido por episodio
const KINDS = ["pdf", "guion", "escaleta", "audio", "video", "logs"];

// Carpeta canónica por tipo de contenido (filesystem es la única fuente de verdad)
const SOURCES = {
  pdf:      { folder: "PDFs/",         ext: ".pdf",   label: "PDF",          icon: "doc" },
  guion:    { folder: "Guiones/",      ext: ".txt",   label: "Guion",        icon: "doc" },
  escaleta: { folder: "escaletas/",    ext: ".md",    label: "Escaleta",     icon: "doc" },
  audio:    { folder: "episodios/",    ext: ".mp3",   label: "Audio",        icon: "play" },
  video:    { folder: "videopodcast/", ext: ".mp4",   label: "Vídeo",        icon: "play" },
  logs:     { folder: "logs/",         ext: ".jsonl", label: "Logs",         icon: "log" },
  checks:   { folder: "(cualquiera)",  ext: "",       label: "Verificaciones", icon: "check" },
};

function pathOf(kind, epId) {
  const s = SOURCES[kind];
  if (!s) return "";
  return `${s.folder}${epId}${s.ext}`;
}

// Helper para construir estado por contenido
function st(p, g, e, a, v, l) { return { pdf: p, guion: g, escaleta: e, audio: a, video: v, logs: l }; }
// status values: "ok" "warn" "alert" "empty" "run"

// 22 episodios = 15 M + 7 T
const EPISODES = [
  // M0 — completo
  { id: "M0",    mod: "M0",  kind: "M", title: "Episodio M0 — Cimientos",                   dur: "47:12", state: st("ok","ok","ok","ok","ok","ok") },
  // M1 — completo
  { id: "M1",    mod: "M1",  kind: "M", title: "Episodio M1 — Datos y ML clásico",          dur: "52:08", state: st("ok","ok","ok","ok","ok","ok") },
  // M2 — completo
  { id: "M2",    mod: "M2",  kind: "M", title: "Episodio M2 — Redes neuronales",            dur: "61:24", state: st("ok","ok","ok","ok","ok","ok") },
  // M3 — episodio principal + 2 T
  { id: "M3",    mod: "M3",  kind: "M", title: "Episodio M3 — Transformers",                dur: "58:00", state: st("ok","ok","ok","ok","warn","ok") },
  { id: "M3_T1", mod: "M3",  kind: "T", title: "T1 — Mecanismo de atención",                dur: "14:32", state: st("ok","ok","ok","ok","ok","ok") },
  { id: "M3_T2", mod: "M3",  kind: "T", title: "T2 — Posicionales rotativos (RoPE)",        dur: "11:08", state: st("ok","ok","ok","alert","empty","alert") },
  // M4 — completo + 0 T
  { id: "M4",    mod: "M4",  kind: "M", title: "Episodio M4 — LLMs y emergencia",           dur: "63:45", state: st("ok","ok","ok","ok","warn","ok") },
  // M5 — en producción
  { id: "M5",    mod: "M5",  kind: "M", title: "Episodio M5 — Fine-tuning y RLHF",          dur: "54:00", state: st("ok","ok","ok","run","empty","ok") },
  // M6 — completo
  { id: "M6",    mod: "M6",  kind: "M", title: "Episodio M6 — Prompting avanzado",          dur: "41:18", state: st("ok","ok","ok","ok","ok","ok") },
  // M7 — bloqueado + 1 T
  { id: "M7",    mod: "M7",  kind: "M", title: "Episodio M7 — RAG y memoria",               dur: "—",     state: st("ok","ok","warn","empty","empty","warn") },
  { id: "M7_T1", mod: "M7",  kind: "T", title: "T1 — Estrategias de chunking",              dur: "—",     state: st("ok","ok","empty","empty","empty","empty") },
  // M8 — solo arranque + 2 T
  { id: "M8",    mod: "M8",  kind: "M", title: "Episodio M8 — Agentes y herramientas",      dur: "—",     state: st("ok","alert","empty","empty","empty","alert") },
  { id: "M8_T1", mod: "M8",  kind: "T", title: "T1 — ReAct y planning",                     dur: "—",     state: st("ok","warn","empty","empty","empty","empty") },
  { id: "M8_T2", mod: "M8",  kind: "T", title: "T2 — Tool calling en Claude",               dur: "—",     state: st("ok","empty","empty","empty","empty","empty") },
  // M9 — PDF solo
  { id: "M9",    mod: "M9",  kind: "M", title: "Episodio M9 — Evaluación y benchmarks",     dur: "—",     state: st("ok","empty","empty","empty","empty","empty") },
  // M10 — vacío
  { id: "M10",   mod: "M10", kind: "M", title: "Episodio M10 — Alineamiento",               dur: "—",     state: st("empty","empty","empty","empty","empty","empty") },
  // M11 — PDF + arranque + 1 T
  { id: "M11",   mod: "M11", kind: "M", title: "Episodio M11 — Multimodalidad",             dur: "—",     state: st("ok","warn","empty","empty","empty","empty") },
  { id: "M11_T1",mod: "M11", kind: "T", title: "T1 — Vision encoders",                      dur: "—",     state: st("ok","empty","empty","empty","empty","empty") },
  // M12 vacío
  { id: "M12",   mod: "M12", kind: "M", title: "Episodio M12 — Inferencia y eficiencia",    dur: "—",     state: st("empty","empty","empty","empty","empty","empty") },
  // M13 vacío
  { id: "M13",   mod: "M13", kind: "M", title: "Episodio M13 — Despliegue y MLOps",         dur: "—",     state: st("empty","empty","empty","empty","empty","empty") },
  // M14 + 1 T
  { id: "M14",   mod: "M14", kind: "M", title: "Episodio M14 — Estado del arte",            dur: "—",     state: st("warn","empty","empty","empty","empty","empty") },
  { id: "M14_T1",mod: "M14", kind: "T", title: "T1 — Frontier models 2026",                 dur: "—",     state: st("empty","empty","empty","empty","empty","empty") },
];

// Live producción
const LIVE_PROC = [
  { id: "p1", cmd: "generar_episodio_v2.py M5",   pid: 41207, t: "00:04:22", cost: "0.42€" },
  { id: "p2", cmd: "validar_episodio.py M3",       pid: 41318, t: "00:00:14", cost: "0.01€" },
];

const RECENT_FILES = [
  { path: "Guiones/M5_guion.txt",       t: "hace 12 s",  by: "Claude" },
  { path: "episodios/M3_T1_v4.mp3",     t: "hace 1 min", by: "ElevenLabs" },
  { path: "escaletas/M5.md",            t: "hace 3 min", by: "Claude" },
  { path: "logs/2026-05-12_M3.jsonl",   t: "hace 4 min", by: "runner" },
];

// Tokens consumption
const TOKEN_DATA = {
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
};

// Pipeline nodes (canónico)
const PIPELINE = [
  { id: "src",     label: "PDF temático",     kind: "input",  x:  60, y: 220, code: "PDFs/Mn.pdf" },
  { id: "claude1", label: "Claude · guion",   kind: "ai",     x: 240, y: 220, code: "generar_guion.py" },
  { id: "guion",   label: "Guion",            kind: "art",    x: 420, y: 220, code: "Guiones/Mn.txt" },
  { id: "claude2", label: "Claude · escaleta",kind: "ai",     x: 600, y: 120, code: "generate_escaleta.py" },
  { id: "esc",     label: "Escaleta",         kind: "art",    x: 780, y: 120, code: "escaletas/Mn.md" },
  { id: "gpt",     label: "GPT · debate",     kind: "ai",     x: 600, y: 320, code: "dual_debate.py" },
  { id: "val",     label: "Validación",       kind: "art",    x: 780, y: 320, code: "logs/dual_Mn.json" },
  { id: "eleven",  label: "ElevenLabs · TTS", kind: "ai",     x: 960, y: 220, code: "generar_episodio_v2.py" },
  { id: "mp3",     label: "Episodio",         kind: "out",    x:1140, y: 220, code: "episodios/Mn.mp3" },
  { id: "kling",   label: "Kling · vídeo",    kind: "ai",     x:1140, y:  80, code: "kling_runner.py" },
  { id: "mp4",     label: "Vídeo",            kind: "out",    x:1140, y: -20, code: "videopodcast/Mn.mp4" },
];

const EDGES = [
  ["src", "claude1"], ["claude1", "guion"],
  ["guion", "claude2"], ["claude2", "esc"],
  ["guion", "gpt"], ["gpt", "val"],
  ["esc", "eleven"], ["val", "eleven"],
  ["eleven", "mp3"], ["mp3", "kling"], ["kling", "mp4"],
];

// AI usage log (synthetic)
const AI_LOG = [
  { t: "12:42:18", model: "haiku-4.5",  kind: "Mejorar con IA",  tok:  1240, cost: 0.003 },
  { t: "12:41:50", model: "sonnet-4.6", kind: "Generar guion",   tok: 14820, cost: 0.198 },
  { t: "12:39:02", model: "haiku-4.5",  kind: "Asistente",       tok:   820, cost: 0.002 },
  { t: "12:36:11", model: "sonnet-4.6", kind: "Generar guion",   tok: 12100, cost: 0.162 },
  { t: "12:32:48", model: "gpt-4o-mini",kind: "Debate dual",      tok:  4400, cost: 0.001 },
];

// Speakers preview lines
const GUION_PREVIEW = [
  { who: "iago",  text: "Vale María, hoy nos metemos con los Transformers. Pero antes de la arquitectura, una pregunta: ¿qué era lo que NO funcionaba en las RNN?" },
  { who: "maria", text: "Buena entrada. El problema era el paralelismo. Las RNN procesaban tokens uno detrás de otro, en secuencia. No podías meterle 64 GPUs y que volaran." },
  { who: "iago",  text: "Y aparece el paper de 2017, “Attention is all you need”. Atención como mecanismo central." },
  { who: "maria", text: "Exacto. Lo bonito de la atención es que es una operación matricial, totalmente paralela. Cada token puede mirar a todos los otros en una sola pasada." },
  { who: "iago",  text: "Vamos a desglosarlo: query, key, value. ¿Qué es cada uno en intuición?" },
  { who: "maria", text: "Imagina una biblioteca. La query es la pregunta que llevas. Las keys son las etiquetas de los lomos. Los values, los libros. Atención = encontrar las etiquetas que matchean tu pregunta y devolverte los libros ponderados." },
];

// Verification checks
const CHECKS_M3 = [
  { id: "c1", name: "PDF presente y legible",            status: "ok",    detail: "PDFs/M3.pdf · 2.4 MB · 18 páginas" },
  { id: "c2", name: "Guion completo (no truncado)",      status: "ok",    detail: "9842 palabras · 142 turnos" },
  { id: "c3", name: "Diálogo balanceado Iago/María",     status: "ok",    detail: "Iago 48% · María 52%" },
  { id: "c4", name: "Escaleta sin secciones vacías",     status: "ok",    detail: "8/8 bloques con contenido" },
  { id: "c5", name: "Audio MP3 sin gaps",                status: "warn",  detail: "1 silencio de 4.2s @ 23:18" },
  { id: "c6", name: "Audio respeta SSML pauses",         status: "ok",    detail: "12/12 pauses correctos" },
  { id: "c7", name: "Loudness LUFS -16 ±1",              status: "ok",    detail: "-15.8 LUFS" },
  { id: "c8", name: "Vídeo escena→texto alineado",       status: "alert", detail: "Drift de 1.8s @ 41:22 — re-render" },
  { id: "c9", name: "Logs sin ERROR",                    status: "ok",    detail: "0 errors · 3 warnings" },
  { id: "c10",name: "Validación dual (Claude vs GPT)",   status: "ok",    detail: "Acuerdo 94% · 6 discrepancias menores" },
];

Object.assign(window, {
  MODULES, EPISODES, LIVE_PROC, RECENT_FILES, TOKEN_DATA,
  PIPELINE, EDGES, AI_LOG, GUION_PREVIEW, CHECKS_M3, KINDS,
  SOURCES, pathOf,
});

// ── Backend bootstrap ────────────────────────────────────────────────
// Si hay servidor (web_server.py) sobreescribimos los fixtures con datos
// reales del repo. Si la llamada falla (servidor parado, file://) los
// fixtures de arriba se quedan como degradación elegante.
window.__BOOTSTRAP__ = (async function bootstrap() {
  try {
    const res = await fetch("/api/bootstrap", { cache: "no-store" });
    if (!res.ok) throw new Error("bootstrap " + res.status);
    const d = await res.json();
    if (Array.isArray(d.MODULES) && d.MODULES.length)             window.MODULES = d.MODULES;
    if (Array.isArray(d.EPISODES) && d.EPISODES.length)           window.EPISODES = d.EPISODES;
    if (Array.isArray(d.LIVE_PROC))                                window.LIVE_PROC = d.LIVE_PROC;
    if (Array.isArray(d.RECENT_FILES) && d.RECENT_FILES.length)    window.RECENT_FILES = d.RECENT_FILES;
    if (d.TOKEN_DATA && Array.isArray(d.TOKEN_DATA.byModel) && d.TOKEN_DATA.byModel.length) {
      window.TOKEN_DATA = d.TOKEN_DATA;
      if (Array.isArray(d.TOKEN_DATA.log) && d.TOKEN_DATA.log.length) {
        window.AI_LOG = d.TOKEN_DATA.log;
      }
    }
    if (d.ECONOMICS) window.ECONOMICS = d.ECONOMICS;
    window.__BOOTSTRAP_OK__ = true;
    return d;
  } catch (e) {
    window.__BOOTSTRAP_OK__ = false;
    window.__BOOTSTRAP_ERR__ = String(e);
    return null;
  }
})();
