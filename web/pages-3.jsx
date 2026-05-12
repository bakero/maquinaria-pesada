// pages-3.jsx — Mapa, Conectores, Lanzador, Fuentes, Previsualizar,
//                Logs, Optimizar, Consumo, Ajustes
// ────────────────────────────────────────────────────────────────

// ════════════════════════════════════════════════════════════
// SHARED FIXTURES (local to these pages)
// ════════════════════════════════════════════════════════════
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
function PageMapa({ onNav, onOpenAI }) {
  const [hover, setHover] = React.useState(null);
  const [view, setView]   = React.useState("grafo"); // grafo | tabla

  const KIND_COLOR = { generator: "var(--info)", system: "var(--y)", generated: "var(--ok)" };
  const KIND_LABEL = { generator: "GENERATOR · IA", system: "SYSTEM · pipeline", generated: "GENERATED · output" };

  const CW = 760, CH = 600;

  return (
    <div className="content">
      <PageHeader
        title="Mapa de componentes"
        sub="Grafo del cockpit · 3 tipos de nodo · persistido en components_map.json"
        actions={
          <React.Fragment>
            <Btn sm kind="ghost" icon={<Icon name="refresh" size={11}/>}
                 onClick={() => window.location.reload()}>Reescanear</Btn>
            <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Mapa de componentes", purpose: "improve" })}
                 icon={<Icon name="spark" size={11}/>}>Mejorar con IA</Btn>
          </React.Fragment>
        }
      />
      <SourcePills files={srcFor("mapa")}/>

      <div className="row mb-8" style={{ justifyContent: "space-between" }}>
        <div className="row gap-3">
          {["grafo", "tabla"].map((v) => (
            <div key={v} className={`btn sm ${view === v ? "primary" : ""}`}
                 onClick={() => setView(v)} style={{ cursor: "pointer" }}>
              {v.toUpperCase()}
            </div>
          ))}
        </div>
        <div className="mono dim" style={{ fontSize: 11, letterSpacing: "0.08em" }}>
          {MAP_NODES.length} nodos · {MAP_EDGES.length} aristas
        </div>
      </div>

      {view === "grafo" ? (
        <Panel
          title={<span><Icon name="map" size={12}/> &nbsp;Grafo de componentes</span>}
          meta="cockpit/components_map.json"
          noPad
        >
          <div style={{
            background: "#0A0A0A",
            backgroundImage:
              "linear-gradient(rgba(245,196,0,0.04) 1px, transparent 1px)," +
              "linear-gradient(90deg, rgba(245,196,0,0.04) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
            position: "relative",
            height: CH,
            overflow: "hidden",
          }}>
            {/* Column labels */}
            {[
              { x: 60,  label: "GENERATORS" },
              { x: 320, label: "SYSTEMS" },
              { x: 600, label: "GENERATED" },
            ].map((c) => (
              <div key={c.label} style={{
                position: "absolute", left: c.x, top: 10,
                fontFamily: "var(--f-display)", fontSize: 10, color: "var(--y)",
                letterSpacing: "0.2em", opacity: 0.7,
              }}>{c.label}</div>
            ))}

            <svg viewBox={`0 0 ${CW} ${CH}`} preserveAspectRatio="none"
                 style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }}>
              <defs>
                <marker id="mp-arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto">
                  <path d="M0 0 L10 5 L0 10 z" fill="var(--y)"/>
                </marker>
              </defs>
              {MAP_EDGES.map(([a, b], i) => {
                const na = MAP_NODES.find(n => n.id === a);
                const nb = MAP_NODES.find(n => n.id === b);
                if (!na || !nb) return null;
                const x1 = na.x + 140, y1 = na.y + 26;
                const x2 = nb.x - 4,  y2 = nb.y + 26;
                const sel = hover && (a === hover || b === hover);
                return (
                  <line key={i} x1={x1} y1={y1} x2={x2} y2={y2}
                        stroke="var(--y)" strokeOpacity={sel ? 0.95 : 0.35}
                        strokeWidth={sel ? 2 : 1.2} markerEnd="url(#mp-arr)"/>
                );
              })}
            </svg>

            {MAP_NODES.map((n) => (
              <div key={n.id}
                   onMouseEnter={() => setHover(n.id)}
                   onMouseLeave={() => setHover(null)}
                   style={{
                     position: "absolute", left: n.x, top: n.y,
                     width: 140, padding: "8px 10px",
                     background: "var(--panel-2)",
                     border: "1px solid var(--border-2)",
                     borderLeft: `3px solid ${KIND_COLOR[n.kind]}`,
                     boxShadow: hover === n.id ? `0 0 0 1px ${KIND_COLOR[n.kind]}` : "none",
                     cursor: "pointer",
                   }}>
                <div className="mono" style={{
                  fontSize: 8, letterSpacing: "0.16em",
                  color: KIND_COLOR[n.kind], marginBottom: 2,
                }}>{n.kind.toUpperCase()}</div>
                <div className="display" style={{
                  fontSize: 11, letterSpacing: "0.04em",
                  color: "var(--text)", lineHeight: 1.2,
                }}>{n.label}</div>
              </div>
            ))}

            <div style={{
              position: "absolute", left: 12, bottom: 12,
              background: "rgba(0,0,0,0.7)",
              border: "1px solid var(--border)",
              padding: "8px 12px",
              fontFamily: "var(--f-mono)",
              fontSize: 10,
              color: "var(--text-dim)",
              display: "flex", flexDirection: "column", gap: 4,
              letterSpacing: "0.08em",
            }}>
              {["generator","system","generated"].map((k) => (
                <div key={k} className="row gap-3">
                  <span style={{ width: 12, height: 12, background: "var(--panel-2)", borderLeft: `3px solid ${KIND_COLOR[k]}` }}/>
                  {KIND_LABEL[k]}
                </div>
              ))}
            </div>
          </div>
        </Panel>
      ) : (
        <Panel noPad>
          <table className="tbl">
            <thead>
              <tr>
                <th style={{ width: 200 }}>ID</th>
                <th>Label</th>
                <th style={{ width: 140 }}>Tipo</th>
                <th style={{ width: 70, textAlign: "right" }}>Aristas</th>
              </tr>
            </thead>
            <tbody>
              {MAP_NODES.map((n) => {
                const ins = MAP_EDGES.filter(([_, b]) => b === n.id).length;
                const outs = MAP_EDGES.filter(([a, _]) => a === n.id).length;
                return (
                  <tr key={n.id}>
                    <td><span className="mono" style={{ fontSize: 11, color: "var(--y)" }}>{n.id}</span></td>
                    <td className="display" style={{ fontSize: 13 }}>{n.label}</td>
                    <td>
                      <span className="badge" style={{ color: KIND_COLOR[n.kind], borderColor: KIND_COLOR[n.kind] }}>
                        {n.kind}
                      </span>
                    </td>
                    <td className="mono dim" style={{ textAlign: "right", fontSize: 11 }}>{ins} ← · {outs} →</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Panel>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · CONECTORES
// ════════════════════════════════════════════════════════════
function PageConectores({ onNav, onOpenAI }) {
  return (
    <div className="content">
      <PageHeader
        title="Conectores"
        sub="Servicios externos · pipelines del repo · fuentes de contenido"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Conectores", purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Mejorar con IA</Btn>
        }
      />
      <SourcePills files={srcFor("conectores")}/>

      {/* Servicios IA */}
      <div className="h2">
        <Icon name="plug" size={14}/> Servicios IA
        <span className="mono dim" style={{ fontSize: 10, marginLeft: "auto", letterSpacing: "0.08em" }}>
          {CONNECTORS.service.filter(s => s.kind !== "distribution").length} servicios
        </span>
      </div>
      <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
        {CONNECTORS.service.filter(s => s.kind !== "distribution").map((c) => (
          <div key={c.id} className="panel" style={{ padding: "14px 16px" }}>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
              <div className="display" style={{ fontSize: 13, letterSpacing: "0.06em" }}>{c.label}</div>
              <StatusDot status={c.status}/>
            </div>
            <div className="mono dim" style={{ fontSize: 11, marginBottom: 6 }}>{c.detail}</div>
            <div className="row" style={{ justifyContent: "space-between", marginTop: 8 }}>
              <span className="badge">{c.env}</span>
              <span className="mono" style={{ fontSize: 10, color: "var(--text-mute)" }}>
                {c.latency}ms
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Distribución — Spotify / iVoox / LinkedIn */}
      <div className="h2">
        <Icon name="map" size={14}/> Distribución y métricas
        <Btn sm kind="ghost" onClick={() => onNav("metricas")} icon={<Icon name="arrow" size={10}/>}>
          Ver métricas
        </Btn>
      </div>
      <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
        {CONNECTORS.service.filter(s => s.kind === "distribution").map((c) => (
          <div key={c.id} className="panel"
               style={{ padding: "14px 16px", cursor: "pointer", borderLeft: "3px solid var(--info)" }}
               onClick={() => onNav("metricas")}>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
              <div className="display" style={{ fontSize: 13, letterSpacing: "0.06em" }}>{c.label}</div>
              <StatusDot status={c.status}/>
            </div>
            <div className="mono dim" style={{ fontSize: 11, marginBottom: 6 }}>{c.detail}</div>
            <div className="row" style={{ justifyContent: "space-between", marginTop: 8 }}>
              <span className="badge">{c.env}</span>
              <span className="mono" style={{ fontSize: 10, color: "var(--text-mute)" }}>
                {c.latency}ms
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Pipelines */}
      <div className="h2">
        <Icon name="prompt" size={14}/> Pipelines del repo
        <span className="mono dim" style={{ fontSize: 10, marginLeft: "auto", letterSpacing: "0.08em" }}>
          {CONNECTORS.pipeline.length} scripts
        </span>
      </div>
      <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))" }}>
        {CONNECTORS.pipeline.map((c) => (
          <div key={c.id} className="panel" style={{ padding: "14px 16px" }}>
            <div className="row gap-3" style={{ marginBottom: 6 }}>
              <Icon name={c.icon} size={12}/>
              <span className="display" style={{ fontSize: 13, letterSpacing: "0.04em" }}>{c.label}</span>
            </div>
            <div className="mono" style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 8, minHeight: 32 }}>
              {c.description}
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="mono" style={{ fontSize: 10, color: "var(--y)" }}>{c.script}</span>
              {PIPELINE_FORMS[c.id]
                ? <Btn sm onClick={() => onNav("lanzador")}>Lanzar →</Btn>
                : <span className="mono" style={{ fontSize: 9, color: "var(--text-mute)" }}>sin form</span>}
            </div>
          </div>
        ))}
      </div>

      {/* Fuentes */}
      <div className="h2">
        <Icon name="folder" size={14}/> Fuentes de contenido
        <span className="mono dim" style={{ fontSize: 10, marginLeft: "auto", letterSpacing: "0.08em" }}>
          {CONNECTORS.source.length} tipos
        </span>
      </div>
      <div className="grid gap-8" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
        {CONNECTORS.source.map((c) => (
          <div key={c.id} className="panel"
               style={{ padding: "14px 16px", cursor: "pointer" }}
               onClick={() => onNav("fuentes")}>
            <div className="row gap-3" style={{ marginBottom: 6 }}>
              <Icon name={c.icon} size={12}/>
              <span className="display" style={{ fontSize: 13, letterSpacing: "0.04em" }}>{c.label}</span>
              <span style={{ marginLeft: "auto", color: "var(--y)", fontFamily: "var(--f-mono)", fontSize: 13 }}>
                {c.count}
              </span>
            </div>
            <div className="mono" style={{ fontSize: 10, color: "var(--y)" }}>{c.folder}<span className="dim">{c.ext}</span></div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · LANZADOR (Generar prompt para Codex)
// ════════════════════════════════════════════════════════════
function PageLanzador({ onNav, onOpenAI }) {
  const ids = Object.keys(PIPELINE_FORMS);
  const [sel, setSel] = React.useState(ids[0]);
  const [vals, setVals] = React.useState({});
  const [copied, setCopied] = React.useState(false);
  const [running, setRunning] = React.useState(false);
  const [output, setOutput] = React.useState([]);

  const form = PIPELINE_FORMS[sel];

  // Reset values when changing pipeline
  React.useEffect(() => {
    const init = {};
    form.fields.forEach(f => { init[f.flag] = f.default; });
    setVals(init);
    setOutput([]);
  }, [sel]);

  const update = (flag, v) => setVals((s) => ({ ...s, [flag]: v }));

  const cmd = (() => {
    const parts = [`python ${form.script}`];
    form.fields.forEach(f => {
      const v = vals[f.flag];
      if (f.kind === "bool") { if (v) parts.push(f.flag); }
      else if (v != null && v !== "") parts.push(`${f.flag} ${JSON.stringify(v).replace(/"/g, "")}`);
    });
    return parts.join(" \\\n  ");
  })();

  const copy = () => {
    navigator.clipboard?.writeText(cmd.replace(/\\\n  /g, " "));
    setCopied(true);
    setTimeout(() => setCopied(false), 1400);
  };

  const run = async () => {
    setRunning(true);
    setOutput([`$ ${cmd.replace(/\\\n  /g, " ")}`]);
    // Construye flags como pares [flag, value] para el backend
    const flags = [];
    form.fields.forEach(f => {
      const v = vals[f.flag];
      if (f.kind === "bool") { if (v) flags.push([f.flag, true]); }
      else if (v != null && v !== "") flags.push([f.flag, v]);
    });
    try {
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ script: form.script, flags }),
      });
      const data = await res.json();
      if (data.ok) {
        setOutput((o) => [...o,
          `[${new Date().toLocaleTimeString()}] INFO  runner: lanzado en background`,
          `[${new Date().toLocaleTimeString()}] INFO  pid=${data.pid} log=${data.log}`,
          `[${new Date().toLocaleTimeString()}] INFO  consulta el log en logs/${data.log}`,
        ]);
      } else {
        setOutput((o) => [...o, `[error] ${data.error || "no se pudo lanzar"}`]);
      }
    } catch (e) {
      setOutput((o) => [...o, `[offline] ${e.message || e} — usa la cabina Streamlit`]);
    }
    setRunning(false);
  };

  return (
    <div className="content">
      <PageHeader
        title="Lanzador de pipelines"
        sub="Rellena el formulario y genera el comando · ejecuta localmente o copia a Codex"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: `Pipeline · ${form.script}`, purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Mejorar con IA</Btn>
        }
      />
      <SourcePills files={srcFor("lanzador")}/>

      <div className="grid gap-8" style={{ gridTemplateColumns: "1fr 1.2fr" }}>
        {/* LEFT — pipeline selector + form */}
        <div className="col gap-8">
          <Panel title={<span><Icon name="prompt" size={12}/> &nbsp;Pipeline</span>}>
            <div className="col gap-3">
              {ids.map((id) => (
                <div key={id}
                     onClick={() => setSel(id)}
                     style={{
                       padding: "8px 10px",
                       border: "1px solid",
                       borderColor: sel === id ? "var(--y)" : "var(--border)",
                       background: sel === id ? "var(--y-soft)" : "var(--panel-2)",
                       cursor: "pointer",
                     }}>
                  <div className="display" style={{
                    fontSize: 12, letterSpacing: "0.06em",
                    color: sel === id ? "var(--y)" : "var(--text)",
                  }}>{id}</div>
                  <div className="mono dim" style={{ fontSize: 10, marginTop: 2 }}>
                    {PIPELINE_FORMS[id].script}
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel
            title={<span><Icon name="settings" size={12}/> &nbsp;Parámetros</span>}
            meta={form.script}
          >
            <div className="mono dim mb-12" style={{ fontSize: 11, lineHeight: 1.5 }}>
              {form.description}
            </div>
            <div className="col gap-4">
              {form.fields.map((f) => (
                <div key={f.flag}>
                  <div className="row" style={{ justifyContent: "space-between", marginBottom: 4 }}>
                    <span className="display" style={{ fontSize: 11, letterSpacing: "0.08em", color: "var(--text-dim)" }}>
                      {f.label}{f.required && <span style={{ color: "var(--alert)" }}> *</span>}
                    </span>
                    <span className="mono" style={{ fontSize: 10, color: "var(--y)" }}>{f.flag}</span>
                  </div>
                  {f.kind === "bool" ? (
                    <div className="row gap-3">
                      {[true, false].map((b) => (
                        <button key={String(b)}
                                className={`btn sm ${vals[f.flag] === b ? "primary" : ""}`}
                                onClick={() => update(f.flag, b)}
                                style={{ flex: 1 }}>
                          {b ? "Sí" : "No"}
                        </button>
                      ))}
                    </div>
                  ) : f.kind === "select" ? (
                    <select className="ai-input" value={vals[f.flag] ?? ""}
                            onChange={(e) => update(f.flag, e.target.value)}
                            style={{ width: "100%" }}>
                      {f.options.map(o => <option key={o} value={o}>{o}</option>)}
                    </select>
                  ) : (
                    <input className="ai-input" value={vals[f.flag] ?? ""}
                           onChange={(e) => update(f.flag, e.target.value)}
                           placeholder={f.placeholder}
                           style={{ width: "100%" }}/>
                  )}
                  {f.help && <div className="mono" style={{ fontSize: 10, color: "var(--text-mute)", marginTop: 3 }}>{f.help}</div>}
                </div>
              ))}
            </div>
          </Panel>
        </div>

        {/* RIGHT — generated command + run */}
        <div className="col gap-8">
          <Panel
            title={<span><Icon name="doc" size={12}/> &nbsp;Comando generado</span>}
            meta="bash · listo para pegar"
            actions={
              <React.Fragment>
                <Btn sm kind="ghost" onClick={copy}>
                  {copied ? "Copiado ✓" : "Copiar"}
                </Btn>
                <Btn sm kind="primary" onClick={run} icon={<Icon name="play" size={10}/>}>
                  {running ? "Ejecutando…" : "Ejecutar"}
                </Btn>
              </React.Fragment>
            }
          >
            <pre className="code" style={{ borderLeftColor: "var(--y)", fontSize: 12.5, padding: "12px 14px" }}>
{cmd}
            </pre>
            <div className="row gap-4 mt-8 mono" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.08em" }}>
              <span>cwd: <span style={{ color: "var(--y)" }}>~/maquinaria-pesada</span></span>
              <span>·</span>
              <span>sandbox: workspace-write</span>
              <span>·</span>
              <span>timeout: 30m</span>
            </div>
          </Panel>

          <Panel
            title={<span><Icon name="log" size={12}/> &nbsp;Salida</span>}
            meta={running ? "streaming…" : output.length ? "finalizado" : "sin ejecutar"}
          >
            {output.length === 0 ? (
              <div className="mono dim" style={{ fontSize: 11, padding: "20px 0", textAlign: "center" }}>
                Pulsa <b style={{ color: "var(--y)" }}>Ejecutar</b> para lanzar el pipeline aquí.
              </div>
            ) : (
              <pre className="code" style={{ borderLeftColor: running ? "var(--info)" : "var(--ok)", maxHeight: 320, overflow: "auto" }}>
                {output.join("\n")}
                {running && <span className="ai-cursor"/>}
              </pre>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · FUENTES
// ════════════════════════════════════════════════════════════
function PageFuentes({ onNav, onOpenAI }) {
  const [src, setSrc] = React.useState("pdfs");
  const [filter, setFilter] = React.useState("");
  const [picked, setPicked] = React.useState(null);

  const source = CONNECTORS.source.find(s => s.id === src);
  const items = (SOURCE_ITEMS[src] || []).filter(it => it.name.toLowerCase().includes(filter.toLowerCase()));

  React.useEffect(() => { setPicked(items[0] || null); }, [src]);

  return (
    <div className="content">
      <PageHeader
        title="Fuentes de contenido"
        sub="Filesystem como única fuente de verdad · PDFs, guiones, escaletas, audio, vídeo, logs"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: `Fuentes · ${picked?.name}`, purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Analizar con IA</Btn>
        }
      />
      <SourcePills files={srcFor("fuentes")}/>

      {/* Source-type picker */}
      <div className="row gap-3 mb-12" style={{ flexWrap: "wrap" }}>
        {CONNECTORS.source.map((s) => (
          <div key={s.id}
               className={`btn sm ${src === s.id ? "primary" : ""}`}
               onClick={() => setSrc(s.id)}
               style={{ cursor: "pointer" }}>
            <Icon name={s.icon} size={10}/>
            {s.label}
            <span className="mono" style={{
              fontSize: 9, padding: "1px 5px",
              background: src === s.id ? "rgba(0,0,0,0.2)" : "var(--panel-2)",
              color: src === s.id ? "#0D0D0D" : "var(--text-mute)",
              borderRadius: 2,
            }}>{(SOURCE_ITEMS[s.id] || []).length}</span>
          </div>
        ))}
      </div>

      <div className="grid gap-8" style={{ gridTemplateColumns: "360px 1fr" }}>
        {/* LEFT — file list */}
        <Panel
          title={<span><Icon name="folder" size={12}/> &nbsp;{source.folder}</span>}
          meta={`${items.length}/${(SOURCE_ITEMS[src] || []).length}`}
        >
          <input className="ai-input mb-8" placeholder="Filtrar por nombre…"
                 value={filter} onChange={(e) => setFilter(e.target.value)}
                 style={{ width: "100%" }}/>
          <div className="col gap-2" style={{ maxHeight: 480, overflowY: "auto" }}>
            {items.map((it) => (
              <div key={it.name}
                   onClick={() => setPicked(it)}
                   style={{
                     padding: "8px 10px",
                     borderTop:    `1px solid ${picked?.name === it.name ? "var(--y)" : "var(--border)"}`,
                     borderRight:  `1px solid ${picked?.name === it.name ? "var(--y)" : "var(--border)"}`,
                     borderBottom: `1px solid ${picked?.name === it.name ? "var(--y)" : "var(--border)"}`,
                     borderLeft:   it.err ? "3px solid var(--alert)"
                                : picked?.name === it.name ? "3px solid var(--y)"
                                : "1px solid var(--border)",
                     background: picked?.name === it.name ? "var(--y-soft)" : "var(--panel-2)",
                     cursor: "pointer",
                   }}>
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <span className="mono" style={{
                    fontSize: 12,
                    color: picked?.name === it.name ? "var(--y)" : "var(--text)",
                    wordBreak: "break-all",
                  }}>{it.name}</span>
                </div>
                <div className="row gap-3 mt-2 mono" style={{ fontSize: 10, color: "var(--text-mute)" }}>
                  <span>{it.size}</span>
                  <span>·</span>
                  <span>{it.t}</span>
                  {it.err && <span style={{ color: "var(--alert)", marginLeft: "auto" }}>{it.err}</span>}
                </div>
              </div>
            ))}
            {!items.length && <div className="mono dim" style={{ fontSize: 11, padding: 16, textAlign: "center" }}>
              Sin items que coincidan.
            </div>}
          </div>
        </Panel>

        {/* RIGHT — viewer */}
        <Panel
          title={picked ? <span><Icon name={source.icon} size={12}/> &nbsp;{picked.name}</span>
                        : <span>Selecciona un archivo</span>}
          meta={picked ? `${picked.size} · ${picked.t}` : ""}
        >
          {picked ? (
            <div className="col gap-8">
              <div className="row gap-4">
                <div style={{ flex: 1 }}>
                  <div className="display" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.16em" }}>RUTA</div>
                  <div className="mono" style={{ fontSize: 12, color: "var(--y)", marginTop: 4 }}>{source.folder}{picked.name}</div>
                </div>
                <Btn sm kind="ghost" icon={<Icon name="folder" size={10}/>}
                     onClick={() => fetch("/api/reveal", {
                       method: "POST",
                       headers: { "Content-Type": "application/json" },
                       body: JSON.stringify({ path: source.folder + picked.name }),
                     }).catch(() => {})}>
                  Revelar
                </Btn>
                <Btn sm icon={<Icon name="doc" size={10}/>}
                     onClick={() => window.open(`/files/${source.folder}${picked.name}`, "_blank")}>
                  Descargar
                </Btn>
              </div>

              {/* Preview placeholder per source type */}
              {src === "pdfs" && (
                picked.url ? (
                  <div style={{ background: "#525659", border: "1px solid var(--border)" }}>
                    <iframe
                      key={picked.url}
                      src={picked.url + "#view=FitH&toolbar=1"}
                      style={{ width: "100%", height: 600, border: 0, display: "block" }}
                      title={picked.name}
                    />
                  </div>
                ) : (
                  <div style={{
                    background: "#F4EFE3", color: "#2A2620", padding: "40px 56px",
                    fontFamily: "Georgia, serif", fontSize: 13, lineHeight: 1.6, minHeight: 280,
                    position: "relative",
                  }}>
                    <div style={{ fontWeight: 700, textTransform: "uppercase", marginBottom: 14, letterSpacing: "0.02em" }}>
                      {picked.name.replace(".pdf", "")} · Resumen temático
                    </div>
                    <div style={{ opacity: 0.7 }}>
                      Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor
                      incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
                      nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
                    </div>
                    <div style={{
                      position: "absolute", top: 10, right: 14,
                      fontFamily: "var(--f-mono)", fontSize: 10, color: "rgba(0,0,0,0.4)",
                      letterSpacing: "0.1em",
                    }}>
                      preview · archivo no disponible localmente
                    </div>
                  </div>
                )
              )}
              {(src === "guiones" || src === "escaletas") && (
                <pre className="code" style={{ maxHeight: 320, overflow: "auto" }}>
{src === "guiones"
? `# ${picked.name}
# generado: ${picked.t}
# encoding: utf-8

[IAGO] Vale María, hoy nos metemos con...
[MARIA] Buena pregunta. Lo bonito es que...
[IAGO] Vamos a desglosarlo: query, key, value.
...`
: `# ${picked.name.replace(".md","")}
> ${picked.size} · ${picked.t}

## 01 · Apertura
- tiempo: \`0:00 → 0:42\`
- palabras: 320
- contenido: saludo, contexto, conexión con módulo anterior.

## 02 · El problema
- tiempo: \`0:42 → 2:10\`
- palabras: 680
...`}
                </pre>
              )}
              {src === "episodios" && (
                <div className="col gap-4">
                  {picked.url ? (
                    <div style={{ background: "#0A0A0A", padding: 16, border: "1px solid var(--border)" }}>
                      <audio
                        key={picked.url}
                        src={picked.url}
                        controls
                        preload="metadata"
                        style={{ width: "100%", filter: "invert(0.92) hue-rotate(180deg)" }}
                      />
                    </div>
                  ) : (
                    <React.Fragment>
                      <div style={{ background: "#0A0A0A", padding: "20px 16px", height: 100, display: "flex", alignItems: "center", gap: 1 }}>
                        {Array.from({ length: 80 }).map((_, i) => (
                          <div key={i} style={{
                            flex: 1,
                            height: `${20 + Math.abs(Math.sin(i * 0.4)) * 50}px`,
                            background: picked.err && i > 50 ? "var(--alert)" : "var(--y)",
                            opacity: 0.8,
                          }}/>
                        ))}
                      </div>
                      <div className="row gap-3">
                        <Btn sm onClick={() => window.open(`/files/${source.folder}${picked.name}`, "_blank")}>
                          <Icon name="play" size={11}/> Play
                        </Btn>
                        <span className="mono dim" style={{ fontSize: 11 }}>{picked.name}</span>
                      </div>
                    </React.Fragment>
                  )}
                </div>
              )}
              {src === "video" && (
                picked.url ? (
                  <div style={{ background: "#000", border: "1px solid var(--border)" }}>
                    <video
                      key={picked.url}
                      src={picked.url}
                      controls
                      preload="metadata"
                      style={{ width: "100%", aspectRatio: "16/9", display: "block" }}
                    />
                  </div>
                ) : (
                  <div style={{
                    background: "#0A0A0A", aspectRatio: "16/9",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    border: "1px dashed var(--border-2)",
                  }}>
                    <div className="col gap-3" style={{ textAlign: "center" }}>
                      <Icon name="play" size={28}/>
                      <div className="mono dim" style={{ fontSize: 11 }}>{picked.size} · archivo no cacheado</div>
                    </div>
                  </div>
                )
              )}
              {src === "logs" && (
                <pre className="code" style={{ maxHeight: 320, overflow: "auto", fontSize: 11 }}>
{LOG_LINES.slice(0, 8).join("\n")}
...
                </pre>
              )}
            </div>
          ) : (
            <div className="mono dim" style={{ textAlign: "center", padding: 40, fontSize: 12 }}>
              Sin selección.
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · PREVISUALIZAR (Player)
// ════════════════════════════════════════════════════════════
function PagePlayer({ onNav, onOpenAI }) {
  const [tab, setTab] = React.useState("audio");
  const items = tab === "audio" ? SOURCE_ITEMS.episodios : SOURCE_ITEMS.video;
  const [pick, setPick] = React.useState(items[0]?.name);
  React.useEffect(() => { setPick((tab === "audio" ? SOURCE_ITEMS.episodios : SOURCE_ITEMS.video)[0]?.name); }, [tab]);

  const sel = items.find(i => i.name === pick) || items[0];

  return (
    <div className="content">
      <PageHeader
        title="Previsualizar"
        sub="Audio y vídeo generados · escucha y revisa antes de publicar"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: `Preview · ${sel?.name}`, purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Sugerir checks</Btn>
        }
      />
      <SourcePills files={srcFor("player")}/>

      <div className="tabs mb-12">
        {[{ id: "audio", icon: "play", label: "Audio" }, { id: "video", icon: "play", label: "Vídeo" }].map((t) => (
          <div key={t.id} className={`tab ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
            <Icon name={t.icon} size={11}/>
            {t.label}
            <span className="badge" style={{ marginLeft: 4 }}>{tab === "audio" ? SOURCE_ITEMS.episodios.length : SOURCE_ITEMS.video.length}</span>
          </div>
        ))}
      </div>

      <div className="grid gap-8" style={{ gridTemplateColumns: "280px 1fr" }}>
        <Panel title={<span><Icon name="folder" size={12}/> &nbsp;Cola</span>} noPad>
          <div className="col gap-2" style={{ padding: 10 }}>
            {items.map((it) => (
              <div key={it.name}
                   onClick={() => setPick(it.name)}
                   style={{
                     padding: "8px 10px",
                     borderTop:    `1px solid ${pick === it.name ? "var(--y)" : "var(--border)"}`,
                     borderRight:  `1px solid ${pick === it.name ? "var(--y)" : "var(--border)"}`,
                     borderBottom: `1px solid ${pick === it.name ? "var(--y)" : "var(--border)"}`,
                     borderLeft:   it.err ? "3px solid var(--alert)"
                                : pick === it.name ? "3px solid var(--y)"
                                : "1px solid var(--border)",
                     background: pick === it.name ? "var(--y-soft)" : "var(--panel-2)",
                     cursor: "pointer",
                   }}>
                <div className="mono" style={{ fontSize: 12, color: pick === it.name ? "var(--y)" : "var(--text)" }}>{it.name}</div>
                <div className="mono dim" style={{ fontSize: 10, marginTop: 2 }}>{it.size} · {it.t}</div>
                {it.err && <div className="mono" style={{ fontSize: 10, color: "var(--alert)", marginTop: 2 }}>{it.err}</div>}
              </div>
            ))}
          </div>
        </Panel>

        <Panel
          title={<span><Icon name="play" size={12}/> &nbsp;{sel?.name}</span>}
          meta={`${sel?.size} · ${sel?.t}`}
        >
          {tab === "audio" ? (
            <div className="col gap-8">
              {sel?.url ? (
                <div style={{
                  background: "#0A0A0A", padding: "24px 20px", border: "1px solid var(--border)",
                  borderLeft: "3px solid var(--y)",
                }}>
                  {/* Waveform decorative */}
                  <div style={{ position: "relative", height: 80, display: "flex", alignItems: "center", gap: 1, marginBottom: 16 }}>
                    {Array.from({ length: 120 }).map((_, i) => {
                      const h = 12 + Math.abs(Math.sin(i * 0.32)) * 60 + (i % 3) * 6;
                      return (
                        <div key={i} style={{
                          flex: 1, height: `${h}px`,
                          background: "var(--y)", opacity: 0.6,
                        }}/>
                      );
                    })}
                  </div>
                  <audio
                    key={sel.url}
                    src={sel.url}
                    controls
                    preload="metadata"
                    style={{ width: "100%", filter: "invert(0.92) hue-rotate(180deg)" }}
                  />
                </div>
              ) : (
                <div style={{
                  background: "#0A0A0A", padding: "24px 16px", position: "relative",
                  height: 160, display: "flex", alignItems: "center", gap: 1,
                }}>
                  {Array.from({ length: 120 }).map((_, i) => {
                    const fail = sel?.err && i > 80;
                    const h = fail ? 6 : 16 + Math.abs(Math.sin(i * 0.32)) * 80 + (i % 3) * 8;
                    return (
                      <div key={i} style={{
                        flex: 1, height: `${h}px`,
                        background: fail ? "var(--alert)" : "var(--y)",
                        opacity: fail ? 0.5 : 0.85,
                      }}/>
                    );
                  })}
                  <div style={{ position: "absolute", left: "30%", top: 0, bottom: 0, width: 1, background: "var(--y)" }}/>
                  <div style={{
                    position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center",
                    background: "rgba(13,13,13,0.7)",
                  }}>
                    <div className="mono" style={{ fontSize: 11, color: "var(--text-mute)", letterSpacing: "0.16em" }}>
                      ARCHIVO NO CACHEADO LOCALMENTE
                    </div>
                  </div>
                </div>
              )}

              <div className="row" style={{ justifyContent: "space-between" }}>
                <div className="row gap-4">
                  <span className="mono dim" style={{ fontSize: 12 }}>
                    {sel?.url ? "▶ controles HTML5 nativos" : (sel?.err ? "03:14 (truncado)" : "—")}
                  </span>
                </div>
                {sel?.url && (
                  <a href={sel.url} download={sel.name} className="btn sm ghost" style={{ textDecoration: "none" }}>
                    <Icon name="folder" size={11}/> Descargar MP3
                  </a>
                )}
              </div>

              {/* Spec checks */}
              <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
                {[
                  { label: "LUFS",      v: "-15.8", ok: true },
                  { label: "Duración",  v: sel?.err ? "03:14" : "11:08", ok: !sel?.err },
                  { label: "Silencios", v: sel?.err ? "1 (4.2s)" : "0", ok: !sel?.err },
                ].map((s) => (
                  <div key={s.label} className="panel" style={{ padding: "10px 12px", borderLeft: `3px solid ${s.ok ? "var(--ok)" : "var(--alert)"}` }}>
                    <div className="display" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.14em" }}>{s.label}</div>
                    <div className="mono" style={{ fontSize: 18, color: s.ok ? "var(--ok)" : "var(--alert)", marginTop: 4 }}>{s.v}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="col gap-8">
              {sel?.url ? (
                <div style={{ background: "#000", border: "1px solid var(--border)", borderLeft: "3px solid var(--y)" }}>
                  <video
                    key={sel.url}
                    src={sel.url}
                    controls
                    preload="metadata"
                    style={{ width: "100%", aspectRatio: "16/9", display: "block", background: "#000" }}
                  />
                </div>
              ) : (
                <div style={{
                  background: "#0A0A0A", aspectRatio: "16/9",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  position: "relative", border: "1px dashed var(--border-2)",
                }}>
                  <div style={{ position: "absolute", inset: 12, border: "1px solid var(--border)", opacity: 0.4 }}/>
                  <div className="col gap-3" style={{ textAlign: "center" }}>
                    <div style={{ width: 64, height: 64, borderRadius: "50%", background: "var(--y)",
                                  display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto" }}>
                      <span style={{ color: "#0D0D0D", fontSize: 24, marginLeft: 4 }}>▶</span>
                    </div>
                    <div className="mono dim" style={{ fontSize: 11 }}>{sel?.size} · archivo no cacheado</div>
                    {sel?.err && <div className="mono" style={{ fontSize: 11, color: "var(--alert)" }}>{sel.err}</div>}
                  </div>
                </div>
              )}

              <div className="row" style={{ justifyContent: "space-between" }}>
                <span className="mono dim" style={{ fontSize: 12 }}>
                  {sel?.url ? "▶ controles HTML5 nativos · 1920×1080" : "—"}
                </span>
                {sel?.url && (
                  <a href={sel.url} download={sel.name} className="btn sm ghost" style={{ textDecoration: "none" }}>
                    <Icon name="folder" size={11}/> Descargar MP4
                  </a>
                )}
              </div>
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · LOGS
// ════════════════════════════════════════════════════════════
function PageLogs({ onNav, onOpenAI }) {
  const logs = SOURCE_ITEMS.logs;
  const [sel, setSel] = React.useState(logs[0].name);
  const [auto, setAuto] = React.useState(false);
  const [lines, setLines] = React.useState(LOG_LINES);
  const [filter, setFilter] = React.useState("");

  // Auto-refresh: append random line every 5s
  React.useEffect(() => {
    if (!auto) return;
    const id = setInterval(() => {
      const t = new Date().toLocaleTimeString("es-ES", { hour12: false });
      const samples = [
        `{"t":"${t}","lvl":"INFO","src":"runner","msg":"heartbeat","cpu":12,"mem":42}`,
        `{"t":"${t}","lvl":"INFO","src":"claude","msg":"token","model":"haiku-4.5","tokens":${Math.floor(Math.random()*200)+20}}`,
        `{"t":"${t}","lvl":"WARN","src":"eleven","msg":"latency high","ms":${Math.floor(Math.random()*800)+200}}`,
      ];
      setLines((l) => [...l, samples[Math.floor(Math.random() * samples.length)]]);
    }, 1500);
    return () => clearInterval(id);
  }, [auto]);

  const filtered = filter
    ? lines.filter(l => l.toLowerCase().includes(filter.toLowerCase()))
    : lines;

  const counts = lines.reduce((acc, l) => {
    if (l.includes('"ERROR"')) acc.err++;
    else if (l.includes('"WARN"')) acc.warn++;
    else acc.info++;
    return acc;
  }, { info: 0, warn: 0, err: 0 });

  return (
    <div className="content">
      <PageHeader
        title="Logs de producción"
        sub="JSONL en logs/ · auto-refresh opcional · diagnóstico IA sobre las últimas líneas"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({
            target: `Log · ${sel}`,
            purpose: "improve",
          })} icon={<Icon name="spark" size={11}/>}>Diagnóstico con IA</Btn>
        }
      />
      <SourcePills files={srcFor("logs")}/>

      <div className="kpi-grid mb-12">
        <Kpi label="Líneas"     value={lines.length} delta={`auto-refresh ${auto ? "ON" : "OFF"}`} deltaDir={auto ? "up" : ""}/>
        <Kpi label="INFO"       value={counts.info}/>
        <Kpi label="WARN"       value={counts.warn} delta={counts.warn ? "atención" : "ok"}/>
        <Kpi label="ERROR"      value={counts.err}  delta={counts.err ? "investigar" : "limpio"} deltaDir={counts.err ? "dn" : "up"}/>
      </div>

      <div className="grid gap-8" style={{ gridTemplateColumns: "280px 1fr" }}>
        <Panel title={<span><Icon name="folder" size={12}/> &nbsp;Archivos</span>} noPad>
          <div className="col gap-2" style={{ padding: 10 }}>
            {logs.map((l) => (
              <div key={l.name}
                   onClick={() => setSel(l.name)}
                   style={{
                     padding: "8px 10px",
                     border: "1px solid",
                     borderColor: sel === l.name ? "var(--y)" : "var(--border)",
                     background: sel === l.name ? "var(--y-soft)" : "var(--panel-2)",
                     cursor: "pointer",
                   }}>
                <div className="mono" style={{ fontSize: 11, color: sel === l.name ? "var(--y)" : "var(--text)", wordBreak: "break-all" }}>
                  {l.name}
                </div>
                <div className="mono dim" style={{ fontSize: 10, marginTop: 2 }}>{l.size} · {l.t}</div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel
          title={<span><Icon name="log" size={12}/> &nbsp;{sel}</span>}
          meta={auto ? "live · 1.5s" : "snapshot"}
          actions={
            <React.Fragment>
              <input className="ai-input" placeholder="Filtrar…" value={filter}
                     onChange={(e) => setFilter(e.target.value)} style={{ width: 140, fontSize: 11 }}/>
              <button className={`btn sm ${auto ? "primary" : "ghost"}`} onClick={() => setAuto(!auto)}>
                <Icon name="refresh" size={10}/> Auto
              </button>
            </React.Fragment>
          }
        >
          <pre className="code" style={{
            maxHeight: 480, overflow: "auto", fontSize: 11.5,
            borderLeftColor: auto ? "var(--info)" : "var(--y)",
          }}>
            {filtered.map((l, i) => {
              const isErr = l.includes('"ERROR"');
              const isWarn = l.includes('"WARN"');
              const color = isErr ? "var(--alert)" : isWarn ? "var(--warn)" : "var(--text-dim)";
              return (
                <div key={i} style={{ color, whiteSpace: "pre-wrap" }}>{l}</div>
              );
            })}
            {auto && <span className="ai-cursor"/>}
          </pre>
        </Panel>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · OPTIMIZAR
// ════════════════════════════════════════════════════════════
function PageOptimizar({ onNav, onOpenAI }) {
  const totalSavings = OPT_RECS.reduce((s, r) => s + r.savings, 0);
  const sevColor = { critical: "var(--alert)", warning: "var(--warn)", info: "var(--info)" };
  const sevLabel = { critical: "CRÍTICA", warning: "AVISO", info: "INFO" };

  return (
    <div className="content">
      <PageHeader
        title="Optimizar consumo"
        sub="Heurísticas sobre ai_usage.jsonl · sin IA · solo reglas explicables"
        actions={
          <React.Fragment>
            <Btn sm kind="ghost" icon={<Icon name="refresh" size={11}/>}
                 onClick={() => window.location.reload()}>Re-analizar</Btn>
            <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Optimización · reglas", purpose: "improve" })}
                 icon={<Icon name="spark" size={11}/>}>Proponer más reglas</Btn>
          </React.Fragment>
        }
      />
      <SourcePills files={srcFor("optimizar")}/>

      <div className="kpi-grid mb-12">
        <Kpi label="Llamadas analizadas"  value="2.4k"          delta="últimos 30 días"/>
        <Kpi label="Gasto total"           value="142.18" unit="€"/>
        <Kpi label="Ahorro potencial"      value={totalSavings.toFixed(2)} unit="€" delta={`${Math.round((totalSavings / 142.18) * 100)}% del gasto`} deltaDir="up"/>
        <Kpi label="Recomendaciones"       value={OPT_RECS.length} delta={`${OPT_RECS.filter(r => r.severity === "critical").length} críticas`}/>
      </div>

      <div className="h2"><Icon name="brain" size={14}/> Recomendaciones</div>

      <div className="col gap-3">
        {OPT_RECS.map((r) => (
          <div key={r.id} className="panel" style={{
            padding: "14px 18px",
            borderLeft: `3px solid ${sevColor[r.severity]}`,
          }}>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 10 }}>
              <div className="row gap-4">
                <span className="badge" style={{
                  color: sevColor[r.severity],
                  borderColor: sevColor[r.severity],
                  background: r.severity === "critical" ? "rgba(204,34,0,0.08)"
                            : r.severity === "warning"  ? "rgba(232,114,17,0.08)"
                            : "rgba(77,184,255,0.08)",
                }}>{sevLabel[r.severity]}</span>
                <div className="display" style={{ fontSize: 14, letterSpacing: "0.04em" }}>{r.title}</div>
                <span className="mono dim" style={{ fontSize: 10 }}>regla: {r.id}</span>
              </div>
              <div className="col" style={{ alignItems: "flex-end", gap: 0 }}>
                <div className="display" style={{ fontSize: 9, color: "var(--text-mute)", letterSpacing: "0.16em" }}>AHORRO</div>
                <div className="mono" style={{ fontSize: 18, color: "var(--ok)" }}>{r.savings.toFixed(2)}€</div>
              </div>
            </div>
            <div className="grid gap-8" style={{ gridTemplateColumns: "1fr 1fr" }}>
              <div>
                <div className="display mb-4" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.14em" }}>EVIDENCIA</div>
                <div className="mono" style={{ fontSize: 12, color: "var(--text-dim)", lineHeight: 1.5 }}>{r.evidence}</div>
              </div>
              <div>
                <div className="display mb-4" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.14em" }}>ACCIÓN</div>
                <div className="mono" style={{ fontSize: 12, color: "var(--y)", lineHeight: 1.5 }}>{r.action}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · CONSUMO (Tokens + Economics)
// ════════════════════════════════════════════════════════════
function PageConsumo({ onNav, onOpenAI }) {
  const [tab, setTab] = React.useState("uso");
  const totalBalance = PROVIDER_BALANCE.reduce((s, p) => s + (p.topped - p.spent), 0);

  return (
    <div className="content">
      <PageHeader
        title="Consumo · tokens y saldos"
        sub="Agregado de ai_usage.jsonl + recargas por proveedor"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Consumo IA", purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Mejorar con IA</Btn>
        }
      />
      <SourcePills files={srcFor("consumo")}/>

      <div className="kpi-grid mb-12">
        <Kpi label="Tokens · 30d"   value="18.4" unit="M" delta="−12% vs mes anterior" deltaDir="dn"/>
        <Kpi label="Gasto · 30d"    value="142.18" unit="€" delta="57% del budget (250€)"/>
        <Kpi label="Saldo global"   value={totalBalance.toFixed(2)} unit="€" delta={`${PROVIDER_BALANCE.length} proveedores`} deltaDir="up"/>
        <Kpi label="Llamadas · 30d" value="2 402" delta="ø 53/día"/>
      </div>

      <div className="tabs mb-12">
        {[
          { id: "uso",     icon: "coin",  label: "Uso por modelo" },
          { id: "saldo",   icon: "key",   label: "Saldos & recargas" },
          { id: "eventos", icon: "log",   label: "Últimos eventos" },
        ].map((t) => (
          <div key={t.id} className={`tab ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
            <Icon name={t.icon} size={11}/>{t.label}
          </div>
        ))}
      </div>

      {tab === "uso" && (
        <div className="grid gap-8" style={{ gridTemplateColumns: "1.5fr 1fr" }}>
          <Panel title={<span><Icon name="brain" size={12}/> &nbsp;Por modelo</span>} noPad>
            <table className="tbl">
              <thead>
                <tr>
                  <th>Modelo</th>
                  <th style={{ width: 100, textAlign: "right" }}>Tokens</th>
                  <th style={{ width: 90,  textAlign: "right" }}>Coste</th>
                  <th style={{ width: 200 }}>Cuota</th>
                </tr>
              </thead>
              <tbody>
                {TOKEN_DATA.byModel.map((m) => (
                  <tr key={m.model}>
                    <td className="mono" style={{ fontSize: 12, color: "var(--y)" }}>{m.model}</td>
                    <td className="mono tabular" style={{ textAlign: "right", fontSize: 12 }}>{(m.tokens / 1e6).toFixed(2)}M</td>
                    <td className="mono tabular" style={{ textAlign: "right", fontSize: 13 }}>{m.cost.toFixed(2)}€</td>
                    <td>
                      <div className="row gap-3">
                        <div style={{ flex: 1 }}><Bar pct={m.share} status="ok"/></div>
                        <span className="mono" style={{ fontSize: 10, minWidth: 28, textAlign: "right" }}>{m.share}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>

          <Panel title={<span><Icon name="grid" size={12}/> &nbsp;Por tipo</span>}>
            <div className="col gap-4">
              {TOKEN_DATA.byKind.map((k) => (
                <div key={k.kind}>
                  <div className="row" style={{ justifyContent: "space-between", marginBottom: 4 }}>
                    <span className="display" style={{ fontSize: 11, letterSpacing: "0.06em", color: "var(--text-dim)" }}>{k.kind}</span>
                    <span className="mono" style={{ fontSize: 11, color: "var(--y)" }}>{k.pct}%</span>
                  </div>
                  <Bar pct={k.pct}/>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      )}

      {tab === "saldo" && (
        <div className="grid gap-8" style={{ gridTemplateColumns: "1.2fr 1fr" }}>
          <Panel title={<span><Icon name="coin" size={12}/> &nbsp;Saldos por proveedor</span>} noPad>
            <table className="tbl">
              <thead>
                <tr>
                  <th>Proveedor</th>
                  <th style={{ width: 100, textAlign: "right" }}>Recargado</th>
                  <th style={{ width: 100, textAlign: "right" }}>Gastado</th>
                  <th style={{ width: 100, textAlign: "right" }}>Saldo</th>
                  <th style={{ width: 80,  textAlign: "right" }}>Llamadas</th>
                </tr>
              </thead>
              <tbody>
                {PROVIDER_BALANCE.map((p) => {
                  const bal = p.topped - p.spent;
                  const low = bal < 20;
                  return (
                    <tr key={p.id}>
                      <td className="display" style={{ fontSize: 12 }}>{p.id}</td>
                      <td className="mono tabular" style={{ textAlign: "right" }}>{p.topped.toFixed(2)}€</td>
                      <td className="mono tabular" style={{ textAlign: "right", color: "var(--text-dim)" }}>{p.spent.toFixed(2)}€</td>
                      <td className="mono tabular" style={{ textAlign: "right", color: low ? "var(--warn)" : "var(--ok)", fontSize: 14 }}>
                        {bal.toFixed(2)}€
                      </td>
                      <td className="mono tabular dim" style={{ textAlign: "right" }}>{p.calls}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Panel>

          <Panel title={<span><Icon name="key" size={12}/> &nbsp;Histórico recargas</span>} meta={`${TOPUPS.length} en total`} noPad>
            <div className="col gap-2" style={{ padding: 12, maxHeight: 320, overflow: "auto" }}>
              {TOPUPS.map((t, i) => (
                <div key={i} className="row" style={{
                  padding: "6px 10px", border: "1px solid var(--border)", background: "var(--panel-2)",
                  fontFamily: "var(--f-mono)", fontSize: 11,
                }}>
                  <span style={{ color: "var(--text-mute)", width: 110 }}>{t.t}</span>
                  <span style={{ flex: 1, color: "var(--y)" }}>{t.provider}</span>
                  <span style={{ color: "var(--ok)" }}>+{t.amount.toFixed(2)}€</span>
                </div>
              ))}
            </div>
            <div style={{ padding: 12, borderTop: "1px solid var(--border)", background: "var(--panel-2)" }}>
              <Btn sm kind="primary" icon={<Icon name="key" size={10}/>}
                   onClick={async () => {
                     const provider = window.prompt("Proveedor (anthropic / openai / elevenlabs / kling):");
                     if (!provider) return;
                     const amount = parseFloat(window.prompt("Importe USD:") || "0");
                     if (!amount || amount <= 0) return;
                     const note = window.prompt("Nota (opcional):") || "";
                     const res = await fetch("/api/economics/topup", {
                       method: "POST",
                       headers: { "Content-Type": "application/json" },
                       body: JSON.stringify({ provider, amount, note }),
                     });
                     const data = await res.json();
                     if (data.ok) window.location.reload();
                     else window.alert("Error: " + (data.error || "desconocido"));
                   }}>
                Registrar recarga
              </Btn>
            </div>
          </Panel>
        </div>
      )}

      {tab === "eventos" && (
        <Panel title={<span><Icon name="log" size={12}/> &nbsp;Últimos eventos</span>} meta="ai_usage.jsonl" noPad>
          <table className="tbl">
            <thead>
              <tr>
                <th style={{ width: 90 }}>T</th>
                <th>Modelo</th>
                <th>Tipo</th>
                <th style={{ width: 100, textAlign: "right" }}>Tokens</th>
                <th style={{ width: 90,  textAlign: "right" }}>Coste</th>
              </tr>
            </thead>
            <tbody>
              {AI_LOG.map((e, i) => (
                <tr key={i}>
                  <td className="mono dim" style={{ fontSize: 11 }}>{e.t}</td>
                  <td className="mono" style={{ color: "var(--y)" }}>{e.model}</td>
                  <td>{e.kind}</td>
                  <td className="mono tabular" style={{ textAlign: "right" }}>{e.tok.toLocaleString()}</td>
                  <td className="mono tabular" style={{ textAlign: "right", color: "var(--ok)" }}>{e.cost.toFixed(3)}€</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · AJUSTES (API Keys + sandbox)
// ════════════════════════════════════════════════════════════
function PageAjustes({ onNav, onOpenAI }) {
  const [checking, setChecking] = React.useState(false);
  const [keys, setKeys] = React.useState(CONNECTORS.service);

  const recheck = async () => {
    setChecking(true);
    // Llama a /api/api-key/ping para cada proveedor y actualiza el estado
    const updated = await Promise.all(CONNECTORS.service.map(async (k) => {
      const t0 = performance.now();
      try {
        const res = await fetch("/api/api-key/ping", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ provider: (k.id || k.label || "").toLowerCase() }),
        });
        const data = await res.json();
        const latency = Math.round(performance.now() - t0);
        return { ...k, latency, status: data.ok ? "ok" : "warn",
                 detail: data.ok ? `${data.found.length}/${data.expected.length} keys` : (data.error || k.detail) };
      } catch {
        return { ...k, status: "alert", detail: "sin conexión con backend" };
      }
    }));
    setKeys(updated);
    setChecking(false);
  };

  return (
    <div className="content">
      <PageHeader
        title="Ajustes"
        sub="API keys · sandbox · preferencias del cockpit"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Ajustes · API keys", purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Mejorar con IA</Btn>
        }
      />
      <SourcePills files={srcFor("ajustes")}/>

      <div className="h2">
        <Icon name="key" size={14}/> API keys de proveedores
        <Btn sm kind="ghost" onClick={recheck} icon={<Icon name="refresh" size={11}/>}>
          {checking ? "Verificando…" : "Re-verificar (ignora caché 5min)"}
        </Btn>
      </div>

      <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}>
        {keys.map((k) => {
          const badge = k.status === "ok" ? "🟢 OK" : k.status === "warn" ? "🟡 AVISO" : "🔴 ERROR";
          return (
            <div key={k.id} className="panel" style={{ padding: "14px 16px" }}>
              <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
                <div className="display" style={{ fontSize: 14, letterSpacing: "0.04em" }}>{k.label}</div>
                <StatusDot status={k.status}/>
              </div>
              <div className="mono dim" style={{ fontSize: 10, marginBottom: 8 }}>{badge}</div>
              <div className="row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
                <span className="badge">{k.env}</span>
                <span className="mono" style={{ fontSize: 10, color: "var(--text-mute)" }}>
                  {checking ? "…" : `${k.latency}ms`}
                </span>
              </div>
              <div className="mono" style={{ fontSize: 10, color: "var(--text-dim)", lineHeight: 1.4, minHeight: 28 }}>
                {k.detail}
              </div>
              <div className="row gap-3 mt-8">
                <Btn sm kind="ghost" style={{ flex: 1 }}
                     onClick={() => window.alert(`Rota la API key de ${k.label} editando .env y reinicia el servidor.`)}>
                  <Icon name="settings" size={10}/> Rotar
                </Btn>
                <Btn sm kind="ghost" style={{ flex: 1 }}
                     onClick={async () => {
                       const res = await fetch("/api/api-key/ping", {
                         method: "POST",
                         headers: { "Content-Type": "application/json" },
                         body: JSON.stringify({ provider: (k.id || k.label || "").toLowerCase() }),
                       });
                       const data = await res.json();
                       window.alert(data.ok
                         ? `OK · ${data.found.length}/${data.expected.length} keys presentes`
                         : `Faltan: ${(data.expected || []).filter(n => !(data.found || []).some(f => f.name === n)).join(", ") || data.error}`);
                     }}>
                  <Icon name="check" size={10}/> Ping
                </Btn>
              </div>
            </div>
          );
        })}
      </div>

      <div className="h2"><Icon name="settings" size={14}/> Sandbox · ejecución</div>

      <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <Panel title={<span><Icon name="folder" size={12}/> &nbsp;Whitelist de rutas</span>}>
          <div className="mono dim mb-8" style={{ fontSize: 11 }}>
            Rutas dentro del repo donde el cockpit puede escribir. Cualquier otra es solo-lectura.
          </div>
          <div className="col gap-2">
            {[
              "cockpit/components_map.json",
              "logs/",
              "Guiones/",
              "escaletas/",
              "episodios/",
              "videopodcast/",
            ].map((p) => (
              <div key={p} className="row" style={{
                padding: "6px 10px", background: "var(--panel-2)", border: "1px solid var(--border)",
                borderLeft: "2px solid var(--ok)",
              }}>
                <Icon name="check" size={11}/>
                <span className="mono" style={{ fontSize: 12, color: "var(--y)" }}>{p}</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title={<span><Icon name="settings" size={12}/> &nbsp;Preferencias</span>}>
          <div className="col gap-6">
            {[
              { label: "Modelo por defecto",    v: "claude-haiku-4.5",  hint: "Usado en validaciones y Mejorar con IA" },
              { label: "Timeout pipeline",       v: "30 min",            hint: "Antes de cancelar un proceso colgado" },
              { label: "Auto-refresh logs",      v: "5 s",               hint: "Cuando 'Auto' está activado" },
              { label: "Budget mensual",         v: "250.00 €",          hint: "Avisa al 80%" },
              { label: "Caché de prompts",       v: "ON",                hint: "Anthropic prompt-caching" },
            ].map((p) => (
              <div key={p.label} className="row" style={{
                justifyContent: "space-between", padding: "8px 0",
                borderBottom: "1px dashed var(--border)",
              }}>
                <div className="col" style={{ gap: 2 }}>
                  <span className="display" style={{ fontSize: 11, letterSpacing: "0.06em" }}>{p.label}</span>
                  <span className="mono dim" style={{ fontSize: 10 }}>{p.hint}</span>
                </div>
                <span className="mono" style={{ fontSize: 12, color: "var(--y)" }}>{p.v}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="h2"><Icon name="dot" size={14}/> Acerca de</div>
      <Panel>
        <div className="grid gap-8" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
          {[
            { lbl: "Versión",      v: "v0.9.0"     },
            { lbl: "Branch",       v: "master"     },
            { lbl: "Commit",       v: "30bfb39"    },
            { lbl: "Tests",        v: "163 ✓"      },
            { lbl: "Python",       v: "3.11.6"     },
            { lbl: "Streamlit",    v: "1.36.0"     },
          ].map((a) => (
            <div key={a.lbl}>
              <div className="display" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.16em" }}>{a.lbl}</div>
              <div className="mono" style={{ fontSize: 14, color: "var(--y)", marginTop: 4 }}>{a.v}</div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · MÉTRICAS DE DIFUSIÓN (Spotify · iVoox · LinkedIn)
// ════════════════════════════════════════════════════════════

// 30 días de datos sintéticos por plataforma
const _trend = (base, drift, jitter) =>
  Array.from({ length: 30 }, (_, i) =>
    Math.max(0, Math.round(base + i * drift + (Math.sin(i * 0.7) * jitter * 0.5) + (Math.random() - 0.5) * jitter))
  );

const METRICS = {
  spotify: {
    label: "Spotify",
    color: "#1DB954",
    logo: "♫",
    followers: 1842,
    followers_delta: "+124 (30d)",
    plays_30d: 14_280,
    listeners_30d: 6_420,
    completion_rate: 68,
    avg_listen: "18:42",
    countries: [
      { c: "España",      pct: 64 },
      { c: "México",      pct: 12 },
      { c: "Argentina",   pct:  8 },
      { c: "Colombia",    pct:  6 },
      { c: "Chile",       pct:  4 },
      { c: "Otros",       pct:  6 },
    ],
    trend: _trend(380, 6, 120),
    auth: { type: "OAuth 2.0", expires: "2026-08-12", scopes: ["podcast-read","metrics-read"] },
  },
  ivoox: {
    label: "iVoox",
    color: "#E5005B",
    logo: "▶",
    followers: 928,
    followers_delta: "+42 (30d)",
    plays_30d: 8_140,
    downloads_30d: 3_280,
    completion_rate: 71,
    avg_listen: "21:18",
    countries: [
      { c: "España",      pct: 88 },
      { c: "Argentina",   pct:  4 },
      { c: "México",      pct:  4 },
      { c: "Otros",       pct:  4 },
    ],
    trend: _trend(220, 4, 80),
    auth: { type: "API key + RSS", expires: "—", scopes: ["read"] },
  },
  linkedin: {
    label: "LinkedIn",
    color: "#0A66C2",
    logo: "in",
    followers: 3_640,
    followers_delta: "+286 (30d)",
    impressions_30d: 48_220,
    engagement_30d: 4_180,
    engagement_rate: 8.7,
    avg_listen: "—",
    countries: [
      { c: "España",      pct: 58 },
      { c: "México",      pct: 14 },
      { c: "USA",         pct:  9 },
      { c: "UK",          pct:  6 },
      { c: "Argentina",   pct:  5 },
      { c: "Otros",       pct:  8 },
    ],
    trend: _trend(1500, 18, 320),
    auth: { type: "OAuth 2.0", expires: "2026-05-23", scopes: ["r_organization_social","r_member_social"], warn: "expira en 11 días" },
  },
};

// Top episodios cross-platform
const TOP_EPISODES = [
  { id: "M3",    title: "Transformers",             spotify: 2840, ivoox: 1820, linkedin: 12420 },
  { id: "M2",    title: "Redes neuronales",         spotify: 2410, ivoox: 1580, linkedin:  9840 },
  { id: "M1",    title: "Datos y ML clásico",       spotify: 2180, ivoox: 1420, linkedin:  8120 },
  { id: "M0",    title: "Cimientos",                spotify: 1980, ivoox: 1320, linkedin:  7640 },
  { id: "M4",    title: "LLMs y emergencia",        spotify: 1420, ivoox:  980, linkedin:  6280 },
  { id: "M3_T1", title: "T1 · Mecanismo de atención", spotify: 1180, ivoox:  840, linkedin: 4180 },
  { id: "M6",    title: "Prompting avanzado",       spotify:  920, ivoox:  640, linkedin:  3420 },
];

// Sparkline component
function Spark({ values, color, height = 40, fill }) {
  const max = Math.max(...values);
  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * 100;
    const y = 100 - (v / max) * 92 - 4;
    return [x, y];
  });
  const path = "M " + pts.map(p => p.join(" ")).join(" L ");
  const areaPath = path + ` L 100 100 L 0 100 Z`;
  return (
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: "100%", height, display: "block" }}>
      {fill && <path d={areaPath} fill={color} fillOpacity={0.15}/>}
      <path d={path} fill="none" stroke={color} strokeWidth={1.4} vectorEffect="non-scaling-stroke"/>
      {pts.map(([x, y], i) => i === pts.length - 1 ? <circle key={i} cx={x} cy={y} r={1.6} fill={color}/> : null)}
    </svg>
  );
}

function PageMetricas({ onNav, onOpenAI }) {
  const [tab, setTab] = React.useState("global"); // global | spotify | ivoox | linkedin
  const [refreshing, setRefreshing] = React.useState(false);
  const [lastSync, setLastSync] = React.useState("hoy 12:38");

  const totalListeners = METRICS.spotify.listeners_30d + METRICS.ivoox.plays_30d;
  const totalPlays     = METRICS.spotify.plays_30d + METRICS.ivoox.plays_30d;
  const totalImpr      = METRICS.linkedin.impressions_30d;
  const totalFollowers = METRICS.spotify.followers + METRICS.ivoox.followers + METRICS.linkedin.followers;

  const refresh = () => {
    setRefreshing(true);
    setTimeout(() => {
      setRefreshing(false);
      const now = new Date();
      setLastSync(`hoy ${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`);
    }, 1100);
  };

  return (
    <div className="content">
      <PageHeader
        title="Métricas de difusión"
        sub="Spotify · iVoox · LinkedIn · oyentes, descargas, engagement"
        actions={
          <React.Fragment>
            <span className="mono dim" style={{ fontSize: 11, letterSpacing: "0.08em" }}>
              sync: {lastSync}
            </span>
            <Btn sm kind="ghost" onClick={refresh} icon={<Icon name="refresh" size={11}/>}>
              {refreshing ? "Sincronizando…" : "Sincronizar ahora"}
            </Btn>
            <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Métricas de difusión", purpose: "improve" })}
                 icon={<Icon name="spark" size={11}/>}>Analizar con IA</Btn>
          </React.Fragment>
        }
      />
      <SourcePills files={srcFor("metricas")}/>

      {/* KPIs cross-platform */}
      <div className="kpi-grid mb-12">
        <Kpi label="Reproducciones · 30d"
             value={(totalPlays / 1000).toFixed(1)} unit="K"
             delta="+18% vs mes anterior" deltaDir="up"/>
        <Kpi label="Oyentes únicos · 30d"
             value={(totalListeners / 1000).toFixed(1)} unit="K"
             delta="Spotify + iVoox"/>
        <Kpi label="Impresiones LinkedIn · 30d"
             value={(totalImpr / 1000).toFixed(1)} unit="K"
             delta={`${METRICS.linkedin.engagement_rate}% engagement`} deltaDir="up"/>
        <Kpi label="Seguidores totales"
             value={totalFollowers.toLocaleString("es-ES")}
             delta="+452 (30d)" deltaDir="up"/>
      </div>

      {/* Platform tabs */}
      <div className="tabs mb-12">
        {[
          { id: "global",   label: "Global"    },
          { id: "spotify",  label: "Spotify"   },
          { id: "ivoox",    label: "iVoox"     },
          { id: "linkedin", label: "LinkedIn"  },
        ].map((t) => (
          <div key={t.id} className={`tab ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
            {t.label}
            {t.id !== "global" && <StatusDot status={METRICS[t.id].auth.warn ? "warn" : "ok"} sm/>}
          </div>
        ))}
      </div>

      {tab === "global" && (
        <React.Fragment>
          {/* Platform cards with sparklines */}
          <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
            {["spotify", "ivoox", "linkedin"].map((id) => {
              const m = METRICS[id];
              const primary = id === "linkedin"
                ? { lbl: "Impresiones · 30d", v: m.impressions_30d.toLocaleString("es-ES") }
                : { lbl: "Reproducciones · 30d", v: m.plays_30d.toLocaleString("es-ES") };
              const secondary = id === "spotify"  ? { lbl: "Oyentes", v: m.listeners_30d.toLocaleString("es-ES") }
                              : id === "ivoox"    ? { lbl: "Descargas", v: m.downloads_30d.toLocaleString("es-ES") }
                              : { lbl: "Engagement", v: m.engagement_30d.toLocaleString("es-ES") };

              return (
                <div key={id} className="panel"
                     onClick={() => setTab(id)}
                     style={{ padding: 0, cursor: "pointer", borderLeft: `3px solid ${m.color}` }}>
                  <div style={{ padding: "14px 18px", borderBottom: "1px solid var(--border)" }}>
                    <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
                      <div className="row gap-4">
                        <div style={{
                          width: 28, height: 28, background: m.color, color: "#fff",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontFamily: "var(--f-display)", fontSize: 14, fontWeight: 700, borderRadius: 4,
                        }}>{m.logo}</div>
                        <div className="display" style={{ fontSize: 14, letterSpacing: "0.04em" }}>{m.label}</div>
                      </div>
                      <StatusDot status={m.auth.warn ? "warn" : "ok"}/>
                    </div>
                    <div className="mono dim" style={{ fontSize: 10, letterSpacing: "0.06em" }}>
                      {m.followers.toLocaleString("es-ES")} seguidores · {m.followers_delta}
                    </div>
                  </div>
                  <div style={{ padding: "14px 18px" }}>
                    <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
                      <div>
                        <div className="display" style={{ fontSize: 9, color: "var(--text-mute)", letterSpacing: "0.16em" }}>{primary.lbl}</div>
                        <div className="mono" style={{ fontSize: 24, color: m.color, marginTop: 2 }}>{primary.v}</div>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <div className="display" style={{ fontSize: 9, color: "var(--text-mute)", letterSpacing: "0.16em" }}>{secondary.lbl}</div>
                        <div className="mono" style={{ fontSize: 14, color: "var(--text)", marginTop: 4 }}>{secondary.v}</div>
                      </div>
                    </div>
                    <div style={{ marginTop: 10 }}>
                      <Spark values={m.trend} color={m.color} height={48} fill/>
                    </div>
                    <div className="row mono" style={{ fontSize: 9, color: "var(--text-mute)", justifyContent: "space-between", marginTop: 4 }}>
                      <span>-30d</span><span>hoy</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Top episodios cross-platform */}
          <Panel
            title={<span><Icon name="episode" size={12}/> &nbsp;Top episodios · multi-plataforma</span>}
            meta="ranking por reproducciones agregadas"
            noPad
          >
            <table className="tbl">
              <thead>
                <tr>
                  <th style={{ width: 60 }}>#</th>
                  <th style={{ width: 80 }}>ID</th>
                  <th>Título</th>
                  <th style={{ width: 90,  textAlign: "right" }}>Spotify</th>
                  <th style={{ width: 90,  textAlign: "right" }}>iVoox</th>
                  <th style={{ width: 110, textAlign: "right" }}>LinkedIn</th>
                  <th style={{ width: 140 }}>Cuota Spotify</th>
                </tr>
              </thead>
              <tbody>
                {TOP_EPISODES.map((e, i) => {
                  const total = e.spotify + e.ivoox;
                  const pct = Math.round((e.spotify / total) * 100);
                  return (
                    <tr key={e.id} className="clickable" onClick={() => onNav("episodio")}>
                      <td className="mono dim" style={{ fontSize: 11 }}>{String(i + 1).padStart(2, "0")}</td>
                      <td className="mono" style={{ color: "var(--y)" }}>{e.id}</td>
                      <td style={{ fontSize: 13 }}>{e.title}</td>
                      <td className="mono tabular" style={{ textAlign: "right", color: METRICS.spotify.color }}>
                        {e.spotify.toLocaleString("es-ES")}
                      </td>
                      <td className="mono tabular" style={{ textAlign: "right", color: METRICS.ivoox.color }}>
                        {e.ivoox.toLocaleString("es-ES")}
                      </td>
                      <td className="mono tabular" style={{ textAlign: "right", color: METRICS.linkedin.color }}>
                        {e.linkedin.toLocaleString("es-ES")}
                      </td>
                      <td>
                        <div className="row gap-3">
                          <div style={{ flex: 1, height: 4, background: "var(--panel-3)", display: "flex", overflow: "hidden" }}>
                            <div style={{ width: `${pct}%`,        height: "100%", background: METRICS.spotify.color }}/>
                            <div style={{ width: `${100 - pct}%`,  height: "100%", background: METRICS.ivoox.color   }}/>
                          </div>
                          <span className="mono" style={{ fontSize: 10, color: "var(--text-mute)", minWidth: 36, textAlign: "right" }}>
                            {pct}/{100 - pct}
                          </span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Panel>
        </React.Fragment>
      )}

      {tab !== "global" && <PlatformDetail id={tab} m={METRICS[tab]} onNav={onNav}/>}
    </div>
  );
}

function PlatformDetail({ id, m, onNav }) {
  const isSpotify  = id === "spotify";
  const isIvoox    = id === "ivoox";
  const isLinkedin = id === "linkedin";

  return (
    <div className="col gap-8">
      {/* Header card with auth state */}
      <Panel noPad>
        <div style={{ padding: "16px 20px", borderLeft: `3px solid ${m.color}`, background: "var(--panel-2)" }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div className="row gap-4">
              <div style={{
                width: 40, height: 40, background: m.color, color: "#fff",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontFamily: "var(--f-display)", fontSize: 18, fontWeight: 700, borderRadius: 4,
              }}>{m.logo}</div>
              <div>
                <div className="display" style={{ fontSize: 18, letterSpacing: "0.04em" }}>{m.label}</div>
                <div className="mono dim" style={{ fontSize: 10, marginTop: 2, letterSpacing: "0.08em" }}>
                  {m.auth.type} · token expira {m.auth.expires}
                </div>
              </div>
            </div>
            <div className="row gap-3">
              <span className={`badge ${m.auth.warn ? "warn" : "ok"}`}>
                {m.auth.warn || "OPERATIVO"}
              </span>
              <Btn sm kind="ghost" icon={<Icon name="refresh" size={10}/>}
                   onClick={() => window.alert(`Para refrescar el token de ${m.label}, regenera la API key en su panel y actualízala en .env.`)}>
                Refrescar token
              </Btn>
            </div>
          </div>
        </div>
      </Panel>

      {/* KPIs */}
      <div className="kpi-grid">
        <Kpi label="Seguidores"
             value={m.followers.toLocaleString("es-ES")} delta={m.followers_delta} deltaDir="up"/>
        {isLinkedin ? (
          <React.Fragment>
            <Kpi label="Impresiones · 30d" value={m.impressions_30d.toLocaleString("es-ES")}/>
            <Kpi label="Engagements · 30d" value={m.engagement_30d.toLocaleString("es-ES")} delta={`${m.engagement_rate}% tasa`} deltaDir="up"/>
          </React.Fragment>
        ) : (
          <React.Fragment>
            <Kpi label="Reproducciones · 30d" value={m.plays_30d.toLocaleString("es-ES")}/>
            {isSpotify && <Kpi label="Oyentes únicos · 30d" value={m.listeners_30d.toLocaleString("es-ES")} delta={`${Math.round((m.listeners_30d / m.plays_30d) * 100)}% conversión`}/>}
            {isIvoox   && <Kpi label="Descargas · 30d" value={m.downloads_30d.toLocaleString("es-ES")}/>}
          </React.Fragment>
        )}
        <Kpi label={isLinkedin ? "Tasa engagement" : "Tasa de finalización"}
             value={isLinkedin ? m.engagement_rate : m.completion_rate} unit="%"
             delta={!isLinkedin ? `escucha media ${m.avg_listen}` : "vs 4.1% benchmark"}
             deltaDir="up"/>
      </div>

      <div className="grid gap-8" style={{ gridTemplateColumns: "1.4fr 1fr" }}>
        {/* Trend chart (bars) */}
        <Panel title={<span><Icon name="brain" size={12}/> &nbsp;Tendencia · últimos 30 días</span>} meta={isLinkedin ? "impresiones/día" : "reproducciones/día"}>
          <div style={{ position: "relative", height: 180, display: "flex", alignItems: "flex-end", gap: 2 }}>
            {m.trend.map((v, i) => {
              const max = Math.max(...m.trend);
              const h = (v / max) * 100;
              return (
                <div key={i} style={{ flex: 1, height: `${h}%`, background: m.color, opacity: 0.7, position: "relative" }}
                     title={`día ${i + 1}: ${v.toLocaleString("es-ES")}`}>
                </div>
              );
            })}
          </div>
          <div className="row mono mt-4" style={{ fontSize: 10, color: "var(--text-mute)", justifyContent: "space-between", letterSpacing: "0.08em" }}>
            <span>-30 días</span>
            <span>media: {Math.round(m.trend.reduce((s, v) => s + v, 0) / m.trend.length).toLocaleString("es-ES")}/día</span>
            <span>hoy</span>
          </div>
        </Panel>

        {/* Geo distribution */}
        <Panel title={<span><Icon name="map" size={12}/> &nbsp;Por país</span>}>
          <div className="col gap-4">
            {m.countries.map((c) => (
              <div key={c.c}>
                <div className="row" style={{ justifyContent: "space-between", marginBottom: 3 }}>
                  <span className="display" style={{ fontSize: 11, letterSpacing: "0.06em", color: "var(--text-dim)" }}>{c.c}</span>
                  <span className="mono" style={{ fontSize: 11, color: m.color }}>{c.pct}%</span>
                </div>
                <div style={{ height: 4, background: "var(--panel-3)" }}>
                  <div style={{ width: `${c.pct}%`, height: "100%", background: m.color }}/>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      {/* Top episodes for this platform */}
      <Panel
        title={<span><Icon name="episode" size={12}/> &nbsp;Top episodios en {m.label}</span>}
        meta={`${TOP_EPISODES.length} episodios`}
        noPad
      >
        <table className="tbl">
          <thead>
            <tr>
              <th style={{ width: 60 }}>#</th>
              <th style={{ width: 100 }}>ID</th>
              <th>Título</th>
              <th style={{ width: 140, textAlign: "right" }}>{isLinkedin ? "Impresiones" : "Reproducciones"}</th>
              <th style={{ width: 180 }}>Cuota</th>
            </tr>
          </thead>
          <tbody>
            {(() => {
              const sorted = [...TOP_EPISODES].sort((a, b) => (b[id] || 0) - (a[id] || 0));
              const max = sorted[0][id];
              return sorted.map((e, i) => (
                <tr key={e.id} className="clickable" onClick={() => onNav("episodio")}>
                  <td className="mono dim" style={{ fontSize: 11 }}>{String(i + 1).padStart(2, "0")}</td>
                  <td className="mono" style={{ color: "var(--y)" }}>{e.id}</td>
                  <td style={{ fontSize: 13 }}>{e.title}</td>
                  <td className="mono tabular" style={{ textAlign: "right", color: m.color, fontSize: 13 }}>
                    {(e[id] || 0).toLocaleString("es-ES")}
                  </td>
                  <td>
                    <div style={{ height: 4, background: "var(--panel-3)" }}>
                      <div style={{ width: `${(e[id] / max) * 100}%`, height: "100%", background: m.color }}/>
                    </div>
                  </td>
                </tr>
              ));
            })()}
          </tbody>
        </table>
      </Panel>

      {/* Auth detail */}
      <Panel title={<span><Icon name="key" size={12}/> &nbsp;Autenticación</span>}>
        <div className="grid gap-6" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
          <div>
            <div className="display" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.14em" }}>TIPO</div>
            <div className="mono" style={{ fontSize: 13, color: "var(--y)", marginTop: 4 }}>{m.auth.type}</div>
          </div>
          <div>
            <div className="display" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.14em" }}>EXPIRA</div>
            <div className="mono" style={{ fontSize: 13, color: m.auth.warn ? "var(--warn)" : "var(--text)", marginTop: 4 }}>
              {m.auth.expires}
            </div>
          </div>
          <div>
            <div className="display" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.14em" }}>SCOPES</div>
            <div className="row gap-2" style={{ marginTop: 4, flexWrap: "wrap" }}>
              {m.auth.scopes.map(s => <span key={s} className="badge mono" style={{ fontSize: 9 }}>{s}</span>)}
            </div>
          </div>
        </div>
      </Panel>
    </div>
  );
}

Object.assign(window, {
  PageMapa, PageConectores, PageLanzador, PageFuentes, PagePlayer,
  PageLogs, PageOptimizar, PageConsumo, PageAjustes, PageMetricas,
});
