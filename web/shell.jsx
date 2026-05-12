// shell.jsx — Sidebar + topbar + AI drawer

// Repo constants
const REPO = "https://github.com/bakero/maquinaria-pesada";
const REPO_REF = "master";
const ghLink = (path) => `${REPO}/blob/${REPO_REF}/${path}`;

// ─── Reorganized IA + source-file wiring ─────────────────
// Every nav item carries `src`: the actual files in the repo that implement it.
const NAV_GROUPS = [
  {
    label: "Producción",
    items: [
      { id: "home",     label: "Inicio",        icon: "home",    num: "00",
        src: ["cockpit/app.py", "cockpit/theme.py"] },
      { id: "master",   label: "Master",        icon: "grid",    num: "01", emph: true,
        src: ["cockpit/pages/0_🎓_Master.py", "cockpit/core/state.py", "cockpit/core/episodes.py"] },
      { id: "modulo",   label: "Módulo",        icon: "module",  num: "02",
        src: ["cockpit/pages/13_🎬_Modulo.py", "cockpit/core/episodes.py", "cockpit/core/paths.py"] },
      { id: "episodio", label: "Episodio",      icon: "episode", num: "03",
        src: ["cockpit/pages/14_📼_Episodio.py", "cockpit/core/verifications.py", "cockpit/core/log_parser.py"] },
    ],
  },
  {
    label: "Pipeline",
    items: [
      { id: "pizarra",   label: "Pizarra",      icon: "pipe",    num: "04",
        src: ["cockpit/pages/15_🎨_Pizarra.py", "cockpit/core/pizarra.py", "cockpit/core/components_map.py"] },
      { id: "mapa",      label: "Mapa",         icon: "map",     num: "05",
        src: ["cockpit/pages/12_🗺️_Mapa.py", "cockpit/core/components_map.py", "cockpit/ui_map.py"] },
      { id: "conectores",label: "Conectores",   icon: "plug",    num: "06",
        src: ["cockpit/pages/2_🔌_Conectores.py", "cockpit/connectors/"] },
      { id: "lanzador",  label: "Lanzador",     icon: "prompt",  num: "07",
        src: ["cockpit/pages/3_📝_Generar_Prompt.py", "cockpit/core/prompt_builder.py", "cockpit/core/runner.py"] },
    ],
  },
  {
    label: "Recursos",
    items: [
      { id: "fuentes", label: "Fuentes",        icon: "folder",  num: "08",
        src: ["cockpit/pages/4_📚_Fuentes.py", "PDFs/", "Guiones/", "escaletas/", "episodios/", "videopodcast/"] },
      { id: "player",  label: "Previsualizar",  icon: "play",    num: "09",
        src: ["cockpit/pages/8_🎧_Previsualizar.py"] },
    ],
  },
  {
    label: "Observabilidad",
    items: [
      { id: "logs",      label: "Logs",         icon: "log",     num: "10",
        src: ["cockpit/pages/5_📜_Logs.py", "cockpit/core/log_parser.py", "cockpit/core/logger.py", "cockpit/core/monitor.py"] },
      { id: "optimizar", label: "Optimizar",    icon: "brain",   num: "11",
        src: ["cockpit/pages/10_🧠_Optimizar.py", "cockpit/core/optimization_advisor.py"] },
    ],
  },
  {
    label: "Difusión",
    items: [
      { id: "metricas",  label: "Métricas",     icon: "map",     num: "12", emph: true,
        src: ["cockpit/pages/16_📡_Metricas.py", "cockpit/connectors/services/spotify.py",
              "cockpit/connectors/services/ivoox.py", "cockpit/connectors/services/linkedin.py",
              "cockpit/core/metrics_aggregator.py"] },
    ],
  },
  {
    label: "Cuenta",
    items: [
      { id: "consumo", label: "Consumo",        icon: "coin",    num: "13",
        src: ["cockpit/pages/7_💰_Tokens.py", "cockpit/pages/11_💳_Economics.py",
              "cockpit/core/usage_tracker.py", "cockpit/core/economics.py"] },
      { id: "ajustes", label: "Ajustes",        icon: "settings",num: "14",
        src: ["cockpit/pages/6_🔑_API_Keys.py", "cockpit/core/api_keys.py", "cockpit/core/sandbox.py"] },
    ],
  },
];

// Helper: get sources for a wired page id
function srcFor(pageId) {
  for (const g of NAV_GROUPS) {
    for (const it of g.items) if (it.id === pageId) return it.src || [];
  }
  return [];
}

// All 15 pages are now wired
const WIRED = new Set([
  "home", "master", "modulo", "episodio",
  "pizarra", "mapa", "conectores", "lanzador",
  "fuentes", "player", "logs", "optimizar",
  "metricas", "consumo", "ajustes",
]);

function Sidebar({ current, onNav }) {
  return (
    <aside className="sb">
      <div className="sb-brand">
        <div className="sb-logo">MP</div>
        <div>
          <div className="sb-title">Maquinaria<br/>Pesada</div>
          <div className="sb-sub">v0.9 · branch master</div>
        </div>
      </div>

      <div className="sb-nav">
        {NAV_GROUPS.map((g) => (
          <div key={g.label}>
            <div className="sb-group">{g.label}</div>
            {g.items.map((it) => {
              const active = current === it.id;
              const wired = WIRED.has(it.id);
              return (
                <div
                  key={it.id}
                  className={`sb-item ${active ? "active" : ""}`}
                  onClick={() => wired && onNav(it.id)}
                  style={{ opacity: wired ? 1 : 0.42, cursor: wired ? "pointer" : "not-allowed" }}
                  title={wired ? "" : "Página no incluida en este prototipo"}
                >
                  <span className="sb-item-num">{it.num}</span>
                  <span className="sb-item-icon"><Icon name={it.icon} size={13} /></span>
                  <span style={{ flex: 1 }}>{it.label}</span>
                  {it.emph && <span style={{ fontSize: 9, fontFamily: "var(--f-mono)", color: "var(--y)" }}>●</span>}
                </div>
              );
            })}
          </div>
        ))}
      </div>

      {/* Producción en vivo — discreto */}
      <div className="sb-live">
        <div className="sb-live-hd">
          <div className="sb-live-title">
            <span className="live-dot" />
            En producción
          </div>
          <div className="sb-live-refresh">5s</div>
        </div>
        {LIVE_PROC.map((p) => (
          <div key={p.id} className="sb-live-row">
            <span className="lbl" title={p.cmd}>
              {p.cmd.length > 22 ? p.cmd.slice(0, 22) + "…" : p.cmd}
            </span>
            <span className="val ok">{p.t}</span>
          </div>
        ))}
        <div className="sb-live-row" style={{ marginTop: 6 }}>
          <span className="lbl">Hoy</span>
          <span className="val">14 archivos · 3.42€</span>
        </div>
      </div>
    </aside>
  );
}

// ── Topbar ─────────────────────────────────────────────────
function Topbar({ crumbs, onCrumb, onOpenAI, onOpenFix }) {
  return (
    <div className="topbar">
      <div className="crumbs">
        {crumbs.map((c, i) => (
          <React.Fragment key={i}>
            {i > 0 && <span className="sep">/</span>}
            {c.id && i < crumbs.length - 1
              ? <a onClick={() => onCrumb(c.id)}>{c.label}</a>
              : <span className={i === crumbs.length - 1 ? "cur" : ""}>{c.label}</span>}
          </React.Fragment>
        ))}
      </div>
      <div className="topbar-actions">
        <div className="row gap-4 dim mono" style={{ fontSize: 11, letterSpacing: "0.08em", marginRight: 8 }}>
          <span>163 <span className="muted">tests</span> <span style={{ color: "var(--ok)" }}>●</span></span>
          <span className="muted">·</span>
          <span>30bfb39</span>
        </div>
        {onOpenFix && (
          <Btn kind="danger" sm onClick={onOpenFix} icon={<Icon name="wrench" size={11}/>}>
            Arreglar con Claude
          </Btn>
        )}
        <Btn kind="primary" sm onClick={onOpenAI} icon={<Icon name="spark" size={11}/>}>
          Mejorar con IA
        </Btn>
      </div>
    </div>
  );
}

// ── AI Drawer ──────────────────────────────────────────────
function AIDrawer({ open, onClose, mode, context }) {
  const [input, setInput] = React.useState("");
  const [messages, setMessages] = React.useState([]);
  const [streaming, setStreaming] = React.useState(false);
  const [streamText, setStreamText] = React.useState("");

  // Seed messages based on mode/context when opened
  React.useEffect(() => {
    if (!open) return;
    if (mode === "fix") {
      setMessages([
        { role: "system", body: context?.error || "Sesión Claude para arreglar episodio." },
      ]);
    } else {
      setMessages([]);
    }
    setStreamText("");
  }, [open, mode, context?.id]);

  const [lastUsage, setLastUsage] = React.useState(null);

  const send = async () => {
    if (!input.trim()) return;
    const userMsg = { role: "user", body: input };
    const userText = input;
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setStreaming(true);
    setStreamText("");

    const FALLBACK = mode === "fix"
      ? "He inspeccionado el episodio.\n\n1. El audio M3_T2 falla en el bloque 4: 'Atención escalada' — ElevenLabs devolvió 502 en el segundo intento.\n2. Voy a regenerar SOLO ese bloque con la voz María y volver a concatenar.\n3. No tocaré el guion ni la escaleta.\n\n¿Procedo?"
      : "He analizado este episodio. Mejoras sugeridas:\n\n→ El bloque 3 del guion es 22% más largo que la media. Considera dividirlo.\n→ María lleva 4 turnos seguidos entre 18:00 y 21:30. Insertar una intervención de Iago.\n→ La escaleta no menciona RoPE — está en el guion. Refrescar.\n\n[fallback offline]";

    // Llamada real al backend; si falla → fallback simulado.
    let reply = FALLBACK;
    let usage = null;
    try {
      const res = await fetch("/api/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode,
          target: context && (context.target || context.id) ? (context.target || context.id) : null,
          message: userText,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data && data.text) {
          reply = data.text;
          usage = data.usage || null;
        }
      }
    } catch (_) { /* keep fallback */ }

    setLastUsage(usage);

    // Efecto typewriter sobre la respuesta final (real o fallback)
    let i = 0;
    const tick = () => {
      i += Math.floor(Math.random() * 4) + 2;
      setStreamText(reply.slice(0, i));
      if (i < reply.length) setTimeout(tick, 18);
      else {
        setStreaming(false);
        setMessages((m) => [...m, { role: "ai", body: reply }]);
        setStreamText("");
      }
    };
    tick();
  };

  const onKey = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } };

  const title = mode === "fix" ? "Arreglar con Claude" : "Mejorar con IA";

  return (
    <React.Fragment>
      <div className={`drawer-overlay ${open ? "open" : ""}`} onClick={onClose} />
      <aside className={`drawer ${open ? "open" : ""}`}>
        <div className="drawer-hd">
          <div className="drawer-title">
            <Icon name={mode === "fix" ? "wrench" : "spark"} size={14}/>
            {title}
          </div>
          <button className="btn ghost sm" onClick={onClose}><Icon name="close" size={11}/></button>
        </div>

        <div className="drawer-body">
          {context && (
            <div className="ai-msg context">
              <div className="role">Contexto</div>
              <div style={{ marginTop: 6, color: "var(--text)", fontFamily: "var(--f-mono)", fontSize: 11 }}>
                <div><span className="muted">target:</span> {context.target || "—"}</div>
                {context.error && (
                  <pre style={{ margin: "4px 0 0", whiteSpace: "pre-wrap", color: "var(--alert)" }}>
                    {context.error}
                  </pre>
                )}
              </div>
            </div>
          )}

          {messages.length === 0 && !streaming && (
            <div style={{ color: "var(--text-mute)", fontFamily: "var(--f-mono)", fontSize: 11, marginTop: 12 }}>
              {mode === "fix"
                ? "Claude tiene el contexto del fallo. Escribe instrucciones o pulsa Enter para que proponga un fix."
                : "Pregunta lo que necesites sobre este recurso. Claude tiene acceso a archivos relacionados (PDFs, guion, escaleta, logs)."}
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`ai-msg ${m.role}`}>
              <div className="role">{m.role === "user" ? "Tú" : m.role === "ai" ? "Claude" : "Sistema"}</div>
              <div className="body" style={{ whiteSpace: "pre-wrap" }}>{m.body}</div>
            </div>
          ))}

          {streaming && (
            <div className="ai-msg ai">
              <div className="role">Claude</div>
              <div className="body" style={{ whiteSpace: "pre-wrap" }}>
                {streamText}
                <span className="ai-cursor" />
              </div>
            </div>
          )}
        </div>

        <div className="drawer-foot">
          <input
            className="ai-input"
            placeholder={mode === "fix" ? "Describe qué hay que arreglar…" : "Pregúntale algo…"}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKey}
          />
          <Btn kind="primary" sm onClick={send}><Icon name="arrow" size={11}/> Enviar</Btn>
        </div>

        <div className="drawer-foot" style={{ borderTop: 0, paddingTop: 0 }}>
          <div className="ai-cost">
            {lastUsage ? (
              <React.Fragment>
                <span>Modelo <b>{lastUsage.model}</b></span>
                <span>Tokens <b>{(lastUsage.input_tokens || 0) + (lastUsage.output_tokens || 0)}</b></span>
                <span>Coste <b>{((lastUsage.cost_usd || 0)).toFixed(4)}$</b></span>
              </React.Fragment>
            ) : (
              <React.Fragment>
                <span>Modelo <b>claude-haiku-4-5</b></span>
                <span>Tokens <b>—</b></span>
                <span>Coste <b>—</b></span>
              </React.Fragment>
            )}
          </div>
        </div>
      </aside>
    </React.Fragment>
  );
}

Object.assign(window, { Sidebar, Topbar, AIDrawer, NAV_GROUPS, WIRED, srcFor, ghLink, REPO, REPO_REF });
