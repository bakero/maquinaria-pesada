// @ts-nocheck
// Fixtures de las páginas (datos de demo). Sliced del monolito legacy;
// se migrarán a la capa de datos / backend cuando esas páginas se cableen.

const MAP_NODES = [
  // generators (IA)
  { id: "claude_sonnet",  label: "Claude Sonnet 4.5", kind: "generator", x:  60, y:  40 },
  { id: "claude_haiku",   label: "Claude Haiku 4.5",  kind: "generator", x:  60, y: 160 },
  { id: "gpt4o",          label: "GPT-4o mini",       kind: "generator", x:  60, y: 280 },
  { id: "elevenlabs_gen", label: "ElevenLabs v3",     kind: "generator", x:  60, y: 400 },
  { id: "kling_gen",      label: "Kling 1.6 pro",     kind: "generator", x:  60, y: 520 },

  // systems (pipelines)
  { id: "gen_guion",  label: "generar_guion.py",       kind: "system", x: 320, y:  40 },
  { id: "dual",       label: "dual_debate.py",         kind: "system", x: 320, y: 160 },
  { id: "gen_ep",     label: "generar_episodio_v2.py", kind: "system", x: 320, y: 400 },
  { id: "kling_pipe", label: "kling_generator.py",     kind: "system", x: 320, y: 520 },
  { id: "validar",    label: "validar_episodio.py",    kind: "system", x: 320, y: 280 },

  // outputs (generated)
  { id: "guion_out", label: "Guiones/*.txt",       kind: "generated", x: 600, y:  40 },
  { id: "val_out",   label: "logs/dual_*.json",    kind: "generated", x: 600, y: 160 },
  { id: "checks",    label: "checks/*.json",       kind: "generated", x: 600, y: 280 },
  { id: "mp3_out",   label: "episodios/*.mp3",     kind: "generated", x: 600, y: 400 },
  { id: "mp4_out",   label: "videopodcast/*.mp4",  kind: "generated", x: 600, y: 520 },
];

const MAP_EDGES = [
  ["claude_sonnet",  "gen_guion"],
  ["gen_guion",      "guion_out"],
  ["claude_sonnet",  "dual"],
  ["gpt4o",          "dual"],
  ["dual",           "val_out"],
  ["claude_haiku",   "validar"],
  ["validar",        "checks"],
  ["elevenlabs_gen", "gen_ep"],
  ["gen_ep",         "mp3_out"],
  ["kling_gen",      "kling_pipe"],
  ["kling_pipe",     "mp4_out"],
];

const CONNECTORS = {
  service: [
    { id: "anthropic",  label: "Anthropic",  env: "ANTHROPIC_API_KEY",  status: "ok",    detail: "claude-sonnet-4.5 · claude-haiku-4.5", latency: 142 },
    { id: "openai",     label: "OpenAI",     env: "OPENAI_API_KEY",     status: "ok",    detail: "gpt-4o-mini · debate dual",            latency: 188 },
    { id: "elevenlabs", label: "ElevenLabs", env: "ELEVENLABS_API_KEY", status: "warn",  detail: "saldo 8.40€ · recargar",               latency: 232 },
    { id: "kling",      label: "Kling",      env: "KLING_API_KEY",      status: "ok",    detail: "kling-1.6-pro · JWT auth",             latency: 412 },
    { id: "whisper",    label: "Whisper",    env: "(local)",            status: "ok",    detail: "whisper-large-v3 · cpu",               latency:  18 },
    // ── distribución ──
    { id: "spotify",    label: "Spotify for Podcasters", env: "SPOTIFY_CLIENT_ID + SECRET", status: "ok",   detail: "OAuth · métricas de oyentes y reproducciones", latency: 218, kind: "distribution" },
    { id: "ivoox",      label: "iVoox",                  env: "IVOOX_API_KEY",             status: "ok",   detail: "RSS + scraping autenticado · descargas",       latency: 304, kind: "distribution" },
    { id: "linkedin",   label: "LinkedIn",               env: "LINKEDIN_ACCESS_TOKEN",     status: "warn", detail: "token expira en 11 días · refrescar",         latency: 162, kind: "distribution" },
  ],
  pipeline: [
    { id: "generar_guion",      label: "generar_guion.py",      script: "generar_guion.py",      icon: "prompt", description: "Genera guion M desde PDF + docs vivos." },
    { id: "generar_episodio",   label: "generar_episodio_v2.py",script: "generar_episodio_v2.py",icon: "play",   description: "Sintetiza audio dual con 2 voces." },
    { id: "validar_episodio",   label: "validar_episodio.py",   script: "validar_episodio.py",   icon: "check",  description: "QA del audio: gaps, duración, loudness." },
    { id: "dual_debate",        label: "dual_debate.py",        script: "dual_debate.py",        icon: "spark",  description: "Debate Claude vs GPT sobre el guion." },
    { id: "producir_episodio",  label: "producir_episodio.py",  script: "producir_episodio.py",  icon: "prompt", description: "Pipeline completo: guion → audio → validación." },
    { id: "lanzar_produccion",  label: "lanzar_produccion.py",  script: "lanzar_produccion.py",  icon: "prompt", description: "Cola de producción de varios episodios." },
    { id: "rebalance_blocks",   label: "rebalance_blocks.py",   script: "rebalance_blocks.py",   icon: "prompt", description: "Rebalancea bloques de un guion existente." },
    { id: "normalizar_guiones", label: "normalizar_guiones.py", script: "normalizar_guiones.py", icon: "prompt", description: "Normaliza formato Iago/María en guiones." },
  ],
  source: [
    { id: "pdfs",      label: "PDFs",        folder: "PDFs/",        ext: ".pdf",   count: 22, icon: "doc"    },
    { id: "guiones",   label: "Guiones",     folder: "Guiones/",     ext: ".txt",   count: 18, icon: "doc"    },
    { id: "escaletas", label: "Escaletas",   folder: "escaletas/",   ext: ".md",    count: 11, icon: "doc"    },
    { id: "episodios", label: "Audio",       folder: "episodios/",   ext: ".mp3",   count: 14, icon: "play"   },
    { id: "video",     label: "Vídeo",       folder: "videopodcast/",ext: ".mp4",   count:  4, icon: "play"   },
    { id: "logs",      label: "Logs",        folder: "logs/",        ext: ".jsonl", count: 38, icon: "log"    },
  ],
};

// Pipelines — formulario de cada script (lanzador)
const PIPELINE_FORMS = {
  generar_guion: {
    script: "generar_guion.py",
    description: "Genera el guion M de un módulo a partir del PDF temático y docs vivos.",
    fields: [
      { flag: "--modulo",   label: "Módulo",        kind: "select", options: ["M0","M1","M2","M3","M4","M5","M6","M7","M8","M9","M10","M11","M12","M13","M14"], default: "M5", required: true },
      { flag: "--modelo",   label: "Modelo",        kind: "select", options: ["claude-sonnet-4.5","claude-haiku-4.5","claude-opus-4.7"], default: "claude-sonnet-4.5" },
      { flag: "--temperature", label: "Temperatura", kind: "str",    default: "0.7" },
      { flag: "--dual-debate", label: "Debate dual", kind: "bool",   default: true,  help: "Validar con GPT-4o-mini" },
      { flag: "--force",    label: "Forzar regen",  kind: "bool",   default: false },
    ],
  },
  generar_episodio: {
    script: "generar_episodio_v2.py",
    description: "Sintetiza el audio del episodio con voces de Iago y María.",
    fields: [
      { flag: "--episodio", label: "Episodio",      kind: "str",    default: "M5",         required: true, placeholder: "M5 · M3_T2 · …" },
      { flag: "--voz-iago", label: "Voice Iago",    kind: "str",    default: "pNInz6obpgDQGcFmaJgB" },
      { flag: "--voz-maria",label: "Voice María",   kind: "str",    default: "EXAVITQu4vr4xnSDxMaL" },
      { flag: "--model",    label: "Modelo TTS",    kind: "select", options: ["eleven_v3","eleven_turbo_v2_5"], default: "eleven_v3" },
      { flag: "--bed",      label: "Música de fondo",kind: "bool",  default: true },
    ],
  },
  validar_episodio: {
    script: "validar_episodio.py",
    description: "Verifica audio (gaps, loudness, duración) y emite checks.json.",
    fields: [
      { flag: "--episodio", label: "Episodio",        kind: "str",    default: "M3",   required: true },
      { flag: "--lufs",     label: "Target LUFS",     kind: "str",    default: "-16" },
      { flag: "--max-gap",  label: "Gap máximo (s)",  kind: "str",    default: "3.0" },
      { flag: "--auto-fix", label: "Auto-fix",        kind: "bool",   default: false, help: "Corrige loudness y silencios sin preguntar" },
    ],
  },
  producir_episodio: {
    script: "producir_episodio.py",
    description: "Pipeline completo: guion → audio → validación → vídeo.",
    fields: [
      { flag: "--modulo",   label: "Módulo",          kind: "select", options: ["M0","M1","M2","M3","M4","M5","M6","M7","M8"], default: "M5", required: true },
      { flag: "--include-video", label: "Incluir vídeo", kind: "bool", default: false, help: "Lanza también Kling (+24€)" },
      { flag: "--dry-run",  label: "Dry-run",         kind: "bool",   default: false },
    ],
  },
};

// Fuentes — items por carpeta (más realista que listar uno por uno)
const SOURCE_ITEMS = {
  pdfs: [
    { name: "RESUMEN_M3.pdf", size: "1.2 MB", t: "2026-04-20", url: "assets/pdf/RESUMEN_M3.pdf" },
    { name: "RESUMEN_M5.pdf", size: "1.1 MB", t: "2026-05-02", url: "assets/pdf/RESUMEN_M5.pdf" },
    { name: "RESUMEN_M7.pdf", size: "0.9 MB", t: "2026-05-04", url: "assets/pdf/RESUMEN_M7.pdf" },
    { name: "M0.pdf",         size: "1.8 MB", t: "2026-04-12" },
    { name: "M1.pdf",         size: "2.1 MB", t: "2026-04-13" },
    { name: "M2.pdf",         size: "2.4 MB", t: "2026-04-15" },
    { name: "M3.pdf",         size: "2.4 MB", t: "2026-04-20" },
    { name: "M4.pdf",         size: "2.8 MB", t: "2026-04-28" },
    { name: "M6.pdf",         size: "1.9 MB", t: "2026-05-04" },
  ],
  guiones: [
    { name: "M0_guion.txt", size: "38 KB", t: "2026-04-12" },
    { name: "M3_guion.txt", size: "39 KB", t: "2026-05-08" },
    { name: "M3_T1.txt",    size: "12 KB", t: "2026-05-09" },
    { name: "M3_T2.txt",    size: "11 KB", t: "2026-05-11" },
    { name: "M5_guion.txt", size: "41 KB", t: "2026-05-12" },
  ],
  escaletas: [
    { name: "M0.md", size: "8 KB",  t: "2026-04-12" },
    { name: "M3.md", size: "11 KB", t: "2026-05-08" },
    { name: "M3_T2.md", size: "11 KB", t: "2026-05-11" },
    { name: "M5.md", size: "9 KB",  t: "2026-05-12" },
  ],
  episodios: [
    { name: "M7_T1.mp3",    size: "13 MB",  t: "2026-05-12", url: "assets/audio/M7_T1.mp3"  },
    { name: "M10_T5.mp3",   size: "11 MB",  t: "2026-05-09", url: "assets/audio/M10_T5.mp3" },
    { name: "M12_T2.mp3",   size: "9 MB",   t: "2026-05-08", url: "assets/audio/M12_T2.mp3" },
    { name: "M0.mp3",       size: "44 MB",  t: "2026-04-13" },
    { name: "M3.mp3",       size: "52 MB",  t: "2026-05-09" },
    { name: "M3_T2.mp3",    size: "4.8 MB", t: "2026-05-12", err: "truncado @ 03:14" },
  ],
  video: [
    { name: "intro.mp4", size: "8 MB",   t: "2026-04-01", url: "assets/video/intro.mp4" },
    { name: "M0.mp4",    size: "412 MB", t: "2026-04-15" },
    { name: "M3.mp4",    size: "488 MB", t: "2026-05-10", err: "drift @ 41:22" },
  ],
  logs: [
    { name: "2026-05-12_M3.jsonl",   size: "184 KB", t: "hoy" },
    { name: "2026-05-12_M3_T2.jsonl",size:  "28 KB", t: "hoy" },
    { name: "2026-05-11_M5.jsonl",   size: "212 KB", t: "ayer" },
    { name: "2026-05-10_M4.jsonl",   size:  "92 KB", t: "hace 2d" },
    { name: "ai_usage.jsonl",        size: "4.2 MB", t: "auto" },
  ],
};

// Optimizar — recomendaciones (heurísticas sobre ai_usage.jsonl)
const OPT_RECS = [
  { id: "T01",         severity: "critical", title: "Modelo caro para output corto",
    evidence: "84 llamadas a sonnet-4.6 con output <300 tokens (12% del gasto)",
    action: "Cambiar a haiku-4.5 para validaciones y prompts cortos.",
    savings: 8.42 },
  { id: "HOT-SOURCE",  severity: "warning",  title: "Una sola fuente concentra >40% del gasto",
    evidence: "generar_guion.py representa el 52% del coste (74.84€)",
    action: "Cachear PDFs ya procesados; reusar prompts del system.",
    savings: 4.18 },
  { id: "FAILS",       severity: "warning",  title: "Reintentos sin backoff",
    evidence: "11 fallos consecutivos en eleven_v3 (502) sin pausa exponencial",
    action: "Implementar exponential backoff con jitter en el adapter.",
    savings: 1.32 },
  { id: "VERBOSE",     severity: "info",     title: "Prompts demasiado verbosos",
    evidence: "Media de 4.2k tokens de input por llamada (vs benchmark 1.8k)",
    action: "Mover boilerplate al system; usar few-shot solo cuando aporte.",
    savings: 2.04 },
  { id: "CACHE",       severity: "info",     title: "Falta caché de prompts repetidos",
    evidence: "Misma intro de Iago/María enviada 142 veces este mes",
    action: "Activar prompt-caching de Anthropic en la generación de bloques.",
    savings: 3.66 },
];

// Consumo — saldo por proveedor
const PROVIDER_BALANCE = [
  { id: "anthropic",  topped: 200.00, spent: 133.40, calls:  428 },
  { id: "openai",     topped:  40.00, spent:   4.80, calls:   92 },
  { id: "elevenlabs", topped:  60.00, spent:  51.60, calls: 1840 },
  { id: "kling",      topped: 100.00, spent:  72.00, calls:    3 },
];
const TOPUPS = [
  { t: "2026-05-01 09:12", provider: "anthropic",  amount: 100, note: "Recarga mensual" },
  { t: "2026-04-22 14:38", provider: "elevenlabs", amount:  30, note: "Saldo bajo" },
  { t: "2026-04-15 10:05", provider: "anthropic",  amount: 100, note: "—" },
  { t: "2026-04-01 11:00", provider: "kling",      amount: 100, note: "Setup inicial" },
  { t: "2026-03-28 16:24", provider: "openai",     amount:  40, note: "Recarga" },
  { t: "2026-03-15 09:00", provider: "elevenlabs", amount:  30, note: "Recarga" },
];

// Log JSONL realista
const LOG_LINES = [
  `{"t":"12:42:18","lvl":"INFO", "src":"runner","msg":"M5 pipeline start","mode":"v2"}`,
  `{"t":"12:42:22","lvl":"INFO", "src":"guion","msg":"PDF parsed","pages":18,"chars":42018}`,
  `{"t":"12:42:31","lvl":"INFO", "src":"claude","msg":"generation started","model":"sonnet-4.5","in":3804}`,
  `{"t":"12:43:14","lvl":"INFO", "src":"claude","msg":"block 1 done","tokens":1240,"cost":0.018}`,
  `{"t":"12:43:48","lvl":"INFO", "src":"claude","msg":"block 2 done","tokens":1880,"cost":0.024}`,
  `{"t":"12:44:22","lvl":"WARN", "src":"claude","msg":"rate limit hit","retry_in":8}`,
  `{"t":"12:44:30","lvl":"INFO", "src":"claude","msg":"resuming"}`,
  `{"t":"12:45:18","lvl":"INFO", "src":"claude","msg":"block 3 done","tokens":2104,"cost":0.026}`,
  `{"t":"12:46:02","lvl":"INFO", "src":"dual","msg":"debate convergence","agreement":0.94}`,
  `{"t":"12:46:48","lvl":"INFO", "src":"guion","msg":"saved","path":"Guiones/M5_guion.txt"}`,
  `{"t":"12:47:12","lvl":"INFO", "src":"eleven","msg":"synthesis start","blocks":7}`,
  `{"t":"12:47:38","lvl":"INFO", "src":"eleven","msg":"block synthesized","blk":1,"dur":0.42,"cost":0.008}`,
  `{"t":"12:48:14","lvl":"INFO", "src":"eleven","msg":"block synthesized","blk":2,"dur":1.88,"cost":0.032}`,
];

// ════════════════════════════════════════════════════════════
// PAGE · MAPA
// ════════════════════════════════════════════════════════════

export {
  MAP_NODES, MAP_EDGES, CONNECTORS, PIPELINE_FORMS, SOURCE_ITEMS,
  OPT_RECS, PROVIDER_BALANCE, TOPUPS, LOG_LINES,
};
