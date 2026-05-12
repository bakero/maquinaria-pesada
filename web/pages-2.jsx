// pages-2.jsx — Episodio + Pizarra

// ── Helper: panel title with explicit source path ───────
function SourceTitle({ kind, epId, customPath }) {
  const src = SOURCES[kind];
  const path = customPath || (src ? `${src.folder}${epId}${src.ext}` : "");
  return (
    <span className="row gap-4" style={{ alignItems: "baseline" }}>
      <Icon name={src ? src.icon : "doc"} size={12}/>
      <span>{src ? src.label : kind}</span>
      <span style={{
        marginLeft: 8,
        fontFamily: "var(--f-mono)",
        fontSize: 11,
        fontWeight: 400,
        letterSpacing: 0,
        textTransform: "none",
        color: "var(--y)",
        background: "var(--y-soft)",
        padding: "2px 8px",
        border: "1px solid rgba(245,196,0,0.3)",
        borderRadius: 2,
      }}>
        {path}
      </span>
    </span>
  );
}

// ════════════════════════════════════════════════════════════
// EPISODIO — detalle de M3_T2 (con tabs y errores reales)
// ════════════════════════════════════════════════════════════
function PageEpisodio({ onNav, onOpenAI, onOpenFix }) {
  const ep = EPISODES.find(e => e.id === "M3_T2");
  const [tab, setTab] = React.useState("guion");

  const tabs = [
    { id: "guion",    label: "Guion",          icon: "doc",   status: ep.state.guion,    src: "guion" },
    { id: "pdf",      label: "PDF fuente",     icon: "doc",   status: ep.state.pdf,      src: "pdf" },
    { id: "escaleta", label: "Escaleta",       icon: "doc",   status: ep.state.escaleta, src: "escaleta" },
    { id: "audio",    label: "Audio",          icon: "play",  status: ep.state.audio,    src: "audio" },
    { id: "video",    label: "Vídeo",          icon: "play",  status: ep.state.video,    src: "video" },
    { id: "logs",     label: "Logs",           icon: "log",   status: ep.state.logs,     src: "logs" },
    { id: "checks",   label: "Verificaciones", icon: "check", status: "warn",            src: "checks" },
  ];

  return (
    <div className="content">
      <PageHeader
        title={ep.title}
        sub={`${ep.id} · Módulo M3 — Transformers · Tipo T (tema corto)`}
        actions={
          <React.Fragment>
            <Btn sm kind="danger" onClick={() => onOpenFix({
              target: ep.id,
              error: "ElevenLabs 502 en bloque 4 · audio truncado en 03:14",
              id: ep.id,
            })} icon={<Icon name="wrench" size={11}/>}>
              Arreglar con Claude
            </Btn>
            <Btn sm kind="primary" onClick={() => onOpenAI({ target: ep.id, purpose: "improve" })}
                 icon={<Icon name="spark" size={11}/>}>
              Mejorar con IA
            </Btn>
          </React.Fragment>
        }
      />
      <SourcePills files={srcFor("episodio")}/>

      {/* Banner de error */}
      <div style={{
        background: "rgba(204,34,0,0.08)",
        border: "1px solid rgba(204,34,0,0.5)",
        borderLeft: "3px solid var(--alert)",
        padding: "10px 14px",
        marginBottom: 24,
        display: "flex",
        alignItems: "center",
        gap: 12,
      }}>
        <span style={{ color: "var(--alert)", fontSize: 18, lineHeight: 1 }}>●</span>
        <div className="fill">
          <div className="display" style={{ fontSize: 12, color: "var(--alert)", letterSpacing: "0.12em" }}>
            FALLO DETECTADO · 12:14:02
          </div>
          <div className="mono" style={{ fontSize: 12, color: "var(--text)", marginTop: 2 }}>
            ElevenLabs 502 en M3_T2 · bloque 4 "Atención escalada" · 2 reintentos · audio incompleto.
          </div>
        </div>
        <Btn sm kind="danger" onClick={() => onOpenFix({
          target: ep.id,
          error: "ElevenLabs 502 en bloque 4 · audio truncado en 03:14",
          id: ep.id,
        })}>Arreglar</Btn>
      </div>

      {/* Mapa de fuentes — filesystem como única fuente de verdad */}
      <div style={{
        background: "var(--panel)",
        border: "1px solid var(--border)",
        borderLeft: "3px solid var(--y)",
        padding: "10px 14px",
        marginBottom: 16,
      }}>
        <div className="row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
          <div className="display" style={{ fontSize: 11, color: "var(--text-dim)", letterSpacing: "0.16em" }}>
            <Icon name="folder" size={11}/> &nbsp; FUENTES EN DISCO
          </div>
          <div className="mono" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.08em" }}>
            filesystem-source-of-truth · scan auto
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: 6 }}>
          {tabs.map((t) => {
            const src = SOURCES[t.src];
            const has = t.status !== "empty";
            return (
              <div
                key={t.id}
                onClick={() => setTab(t.id)}
                style={{
                  padding: "8px 10px",
                  background: tab === t.id ? "var(--y-soft)" : "var(--panel-2)",
                  border: "1px solid",
                  borderColor: tab === t.id ? "var(--y)" : "var(--border)",
                  cursor: "pointer",
                }}
              >
                <div className="row gap-3" style={{ marginBottom: 4 }}>
                  <StatusDot status={t.status === "empty" ? "empty" : t.status} sm/>
                  <span className="display" style={{ fontSize: 10, letterSpacing: "0.08em", color: tab === t.id ? "var(--y)" : "var(--text)" }}>
                    {t.label}
                  </span>
                </div>
                <div className="mono" style={{ fontSize: 10, color: has ? "var(--text-dim)" : "var(--text-mute)", letterSpacing: "0.02em", wordBreak: "break-all", lineHeight: 1.3 }}>
                  {t.src === "checks"
                    ? <span style={{ fontStyle: "italic" }}>todas las anteriores</span>
                    : `${src.folder}${ep.id}${src.ext}`}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs mb-12">
        {tabs.map((t) => (
          <div key={t.id} className={`tab ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
            <Icon name={t.icon} size={11}/>
            {t.label}
            <StatusDot status={t.status === "empty" ? "empty" : t.status} sm/>
          </div>
        ))}
      </div>

      {tab === "guion"    && <TabGuion epId={ep.id}/>}
      {tab === "pdf"      && <TabPdf epId={ep.id}/>}
      {tab === "escaleta" && <TabEscaleta epId={ep.id}/>}
      {tab === "audio"    && <TabAudio onOpenFix={onOpenFix} epId={ep.id}/>}
      {tab === "video"    && <TabVideo epId={ep.id}/>}
      {tab === "logs"     && <TabLogs epId={ep.id}/>}
      {tab === "checks"   && <TabChecks epId={ep.id}/>}
    </div>
  );
}

// ── Tab: Guion (file viewer) ─────────────────────────────
function TabGuion({ epId }) {
  const [mode, setMode] = React.useState("read"); // read | raw
  const path = pathOf("guion", epId);

  // Build raw text content from preview turns
  const rawLines = [];
  rawLines.push(`# ${epId} · guion`);
  rawLines.push(`# generado: 2026-05-12 12:11`);
  rawLines.push(`# turnos: 142 · palabras: 9842`);
  rawLines.push(``);
  GUION_PREVIEW.forEach((line) => {
    rawLines.push(`[${line.who.toUpperCase()}] ${line.text}`);
    rawLines.push(``);
  });
  rawLines.push(`# … 136 turnos más …`);

  return (
    <div className="grid gap-8" style={{ gridTemplateColumns: "1.8fr 1fr" }}>
      <div className="fv">
        <div className="fv-chrome">
          <Icon name="doc" size={11}/>
          <span className="fv-path">{path}</span>
          <span className="fv-meta">9842 palabras · 142 turnos · 38.4 KB</span>
          <span className="fill"/>
          <div className="fv-toggle">
            <button className={mode === "read" ? "on" : ""} onClick={() => setMode("read")}>Lectura</button>
            <button className={mode === "raw"  ? "on" : ""} onClick={() => setMode("raw")}>Raw</button>
          </div>
          <button className="btn ghost sm" title="Abrir en editor"><Icon name="prompt" size={11}/></button>
        </div>

        {mode === "read" ? (
          <div className="fv-body" style={{ padding: "20px 28px" }}>
            <div className="col gap-6" style={{ fontFamily: "var(--f-body)", fontSize: 15, lineHeight: 1.6 }}>
              {GUION_PREVIEW.map((line, i) => (
                <div key={i} style={{ display: "grid", gridTemplateColumns: "92px 1fr", gap: 14, padding: "8px 0", borderBottom: "1px dashed var(--border)" }}>
                  <Speaker who={line.who}/>
                  <div>{line.text}</div>
                </div>
              ))}
              <div className="mono dim" style={{ fontSize: 11, textAlign: "center", marginTop: 8, padding: "8px 0" }}>
                … 136 turnos más en el archivo …
              </div>
            </div>
          </div>
        ) : (
          <div className="fv-body fv-text">
            <div className="ln">
              {rawLines.map((_, i) => <div key={i}>{i + 1}</div>)}
            </div>
            <div>
              {rawLines.map((l, i) => {
                let cls = "lc";
                let tag = null;
                if (l.startsWith("[IAGO]"))  { cls += " spk-iago";  tag = <span className="tag iago">IAGO</span>;  l = l.slice(6).trim(); }
                if (l.startsWith("[MARIA]")) { cls += " spk-maria"; tag = <span className="tag maria">MARIA</span>; l = l.slice(7).trim(); }
                if (l.startsWith("#")) cls = "lc"; // comments
                return (
                  <div key={i} className={cls} style={{ color: l.startsWith("#") ? "var(--text-mute)" : undefined }}>
                    {tag}{l || "\u00A0"}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <div className="col gap-8">
        <Panel title="Métricas del guion">
          <div className="col gap-4 mono" style={{ fontSize: 13 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="muted">Palabras totales</span><span>9 842</span>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="muted">Turnos</span><span>142</span>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="muted">Balance Iago/María</span>
              <span style={{ color: "var(--ok)" }}>48% / 52%</span>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="muted">Duración estimada</span><span>11:08</span>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="muted">Coste generación</span><span>0.198€</span>
            </div>
            <div className="row" style={{ justifyContent: "space-between", borderTop: "1px solid var(--border)", paddingTop: 8, marginTop: 4 }}>
              <span className="muted">Modificado</span><span>hoy 12:11</span>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="muted">SHA</span><span style={{ color: "var(--text-dim)" }}>a4e1f8c</span>
            </div>
          </div>
        </Panel>
        <Panel title="Acciones">
          <div className="col gap-3">
            <Btn icon={<Icon name="prompt" size={11}/>}
                 onClick={() => onOpenAI && onOpenAI({ target: "Guion M3_T2", purpose: "improve",
                                                       hint: "regenerar preservando tono" })}>
              Regenerar (preservar tono)
            </Btn>
            <Btn kind="ghost" icon={<Icon name="check" size={11}/>}
                 onClick={() => onOpenAI && onOpenAI({ target: "Guion M3_T2", purpose: "improve",
                                                       hint: "validación dual Claude vs GPT" })}>
              Validar con GPT (dual)
            </Btn>
            <Btn kind="ghost" icon={<Icon name="doc" size={11}/>}
                 onClick={() => window.open("/files/Guiones/M3_TX_T2_RoPE.txt", "_blank")}>
              Exportar .txt
            </Btn>
          </div>
        </Panel>
      </div>
    </div>
  );
}

// ── Tab: PDF (file viewer) ───────────────────────────────
function TabPdf({ epId }) {
  const [mode, setMode]   = React.useState("embed"); // embed | text
  const [page, setPage]   = React.useState(1);
  const total = 18;
  const path = pathOf("pdf", epId);
  const pdfUrl = "assets/pdf/RESUMEN_M3.pdf"; // M3 resumen as stand-in

  // Synthetic page content for first few pages
  const pages = {
    1: {
      h1: "POSICIONALES ROTATIVOS (ROPE)",
      h2: "1. Introducción",
      paras: [
        "Las codificaciones posicionales originales (Vaswani et al., 2017) son aditivas y absolutas. Cada posición de la secuencia recibe un vector posicional que se suma al embedding del token. Esta solución es funcional pero presenta dos problemas: no extrapola bien a longitudes no vistas en entrenamiento, y rompe la simetría translacional del modelo.",
        "RoPE — introducido por Su et al. (2021) — propone una alternativa: rotar cada vector de embedding en función de su posición. La rotación se aplica en pares de dimensiones y respeta la propiedad fundamental de que el producto interno entre dos tokens depende sólo de su distancia relativa\u00B91.",
        "Esta propiedad tiene tres consecuencias prácticas:",
      ],
      h22: "2. Propiedades",
      paras2: [
        "(i) extrapolación natural a contextos más largos que los vistos en entrenamiento;",
        "(ii) mejor caché de K/V gracias a la invarianza translacional;",
        "(iii) integración natural con atención causal.",
      ],
    },
    2: {
      h1: "FORMULACIÓN MATEMÁTICA",
      h2: "3. Rotación 2D",
      paras: [
        "Sea x_m el vector de embedding en la posición m. RoPE aplica una rotación R_θ(m) sobre cada par de dimensiones (i, i+1). La matriz de rotación es la matriz 2D estándar parametrizada por un ángulo θ_i = 10000^(-2i/d).",
        "La elegancia del método reside en que la atención escalada Q·K^T entre las posiciones m y n se convierte naturalmente en una función de (m - n) tras aplicar las rotaciones a Q y K. Es decir: ⟨R_θ(m)·q, R_θ(n)·k⟩ depende sólo de (m - n).",
      ],
    },
    3: {
      h1: "EXTRAPOLACIÓN",
      paras: [
        "Una de las propiedades más interesantes de RoPE es que el modelo, una vez entrenado con contextos de longitud L, puede operar con contextos de longitud 2L, 4L o más sin degradación catastrófica del rendimiento. Esto contrasta con las posicionales absolutas, que producen tokens fuera de distribución para posiciones no vistas.",
      ],
    },
  };

  const pg = pages[page] || pages[1];

  return (
    <div className="grid gap-8" style={{ gridTemplateColumns: "1.4fr 1fr" }}>
      <div className="fv">
        <div className="fv-chrome">
          <Icon name="doc" size={11}/>
          <span className="fv-path">{path}</span>
          <span className="fv-meta">2.4 MB · 18 páginas · v1</span>
          <span className="fill"/>
          <div className="fv-toggle">
            <button className={mode === "embed" ? "on" : ""} onClick={() => setMode("embed")}>PDF</button>
            <button className={mode === "text"  ? "on" : ""} onClick={() => setMode("text")}>Texto</button>
          </div>
          <a href={pdfUrl} target="_blank" rel="noopener" className="btn ghost sm" title="Abrir en nueva pestaña" style={{ textDecoration: "none" }}>
            <Icon name="folder" size={11}/>
          </a>
        </div>

        {mode === "embed" ? (
          <div style={{ background: "#525659" }}>
            <iframe
              src={pdfUrl + "#view=FitH&toolbar=1&navpanes=0"}
              style={{ width: "100%", height: 720, border: 0, display: "block" }}
              title={`PDF · ${epId}`}
            />
          </div>
        ) : (
          <React.Fragment>
            <div className="fv-body paper">
              <div className="fv-page">
                <h1>{pg.h1}</h1>
                {pg.h2 && <h2>{pg.h2}</h2>}
                {pg.paras && pg.paras.map((p, i) => <p key={i}>{p}</p>)}
                {pg.h22 && <h2>{pg.h22}</h2>}
                {pg.paras2 && pg.paras2.map((p, i) => <p key={"b" + i}>{p}</p>)}
                <div className="footnum">— {page} —</div>
              </div>
            </div>

            <div className="fv-pagenav">
              <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>‹</button>
              <span className="pageof">Página</span>
              <input
                className="pageinp"
                value={page}
                onChange={(e) => {
                  const v = parseInt(e.target.value, 10);
                  if (!isNaN(v) && v >= 1 && v <= total) setPage(v);
                  else if (e.target.value === "") setPage(1);
                }}
              />
              <span className="pageof">de {total}</span>
              <button onClick={() => setPage((p) => Math.min(total, p + 1))} disabled={page >= total}>›</button>
            </div>
          </React.Fragment>
        )}
      </div>

      <Panel title="Resumen IA del PDF" meta="haiku-4.5 · 0.002€">
        <div style={{ fontSize: 13, color: "var(--text-dim)", lineHeight: 1.6 }}>
          <p style={{ marginTop: 0 }}><b style={{ color: "var(--text)" }}>Tema central:</b> codificaciones posicionales rotativas en Transformers, alternativa a las posicionales absolutas del paper original.</p>
          <p><b style={{ color: "var(--text)" }}>Conceptos clave:</b> rotación 2D por pares, distancia relativa, extrapolación, RoFormer, LLaMA, GPT-NeoX.</p>
          <p><b style={{ color: "var(--text)" }}>Recomendación para el guion:</b> empezar por la intuición geométrica antes que las fórmulas. María lleva las matemáticas; Iago pregunta desde la analogía del reloj.</p>
        </div>
        <div className="mt-8">
          <div className="h3 mb-4">Páginas con material clave</div>
          <div className="row gap-3">
            {[1, 2, 5, 9, 14].map((p) => (
              <button key={p} className="btn sm" onClick={() => setPage(p)}>{p}</button>
            ))}
          </div>
        </div>
      </Panel>
    </div>
  );
}

// ── Tab: Escaleta (markdown viewer) ──────────────────────
function TabEscaleta({ epId }) {
  const [mode, setMode] = React.useState("render");
  const path = pathOf("escaleta", epId);

  const blocks = [
    { n: 1, title: "Apertura",                  t: "0:00 → 0:42",  w: 320,  body: "Saludo, contexto del episodio, conexión con M3 (Transformers)." },
    { n: 2, title: "El problema posicional",    t: "0:42 → 2:10",  w: 680,  body: "Por qué las posicionales absolutas fallan en extrapolación. María pone el ejemplo numérico." },
    { n: 3, title: "Rotación 2D por pares",     t: "2:10 → 4:30",  w: 1240, body: "Intuición geométrica primero (reloj que gira), después la matriz 2D." },
    { n: 4, title: "Atención escalada",         t: "4:30 → 6:20",  w: 1010, body: "Producto interno como medida de similitud, distancia relativa emerge naturalmente." },
    { n: 5, title: "Distancia relativa",        t: "6:20 → 8:15",  w: 980,  body: "Por qué (m - n) es lo único que importa. Implicaciones para caché K/V." },
    { n: 6, title: "Extrapolación",             t: "8:15 → 10:00", w: 920,  body: "Demostrar que un modelo con RoPE puede operar a 2× o 4× la longitud sin re-training." },
    { n: 7, title: "Cierre y siguiente",        t: "10:00 → 11:08",w: 380,  body: "Recap, enlace al próximo episodio (M4 · LLMs y emergencia)." },
  ];

  const rawMd =
`# Escaleta · M3_T2 — Posicionales rotativos (RoPE)
> duración total: 11:08 · 7 bloques · 5530 palabras

` + blocks.map((b) =>
`## ${b.n.toString().padStart(2, "0")} · ${b.title}
- tiempo: \`${b.t}\`
- palabras: \`${b.w}\`
- contenido: ${b.body}
`).join("\n");

  return (
    <div className="grid gap-8" style={{ gridTemplateColumns: "1.5fr 1fr" }}>
      <div className="fv">
        <div className="fv-chrome">
          <Icon name="doc" size={11}/>
          <span className="fv-path">{path}</span>
          <span className="fv-meta">7 bloques · 5 530 palabras · 11.2 KB</span>
          <span className="fill"/>
          <div className="fv-toggle">
            <button className={mode === "render" ? "on" : ""} onClick={() => setMode("render")}>Render</button>
            <button className={mode === "raw"    ? "on" : ""} onClick={() => setMode("raw")}>Raw</button>
          </div>
          <button className="btn ghost sm" title="Editar"><Icon name="prompt" size={11}/></button>
        </div>

        {mode === "render" ? (
          <div className="fv-body fv-md">
            <h1>Escaleta · M3_T2 — Posicionales rotativos (RoPE)</h1>
            <div className="meta">duración total: 11:08 · 7 bloques · 5530 palabras</div>
            {blocks.map((b) => (
              <div key={b.n}>
                <h2>{b.n.toString().padStart(2, "0")} · {b.title}</h2>
                <ul>
                  <li>tiempo: <code>{b.t}</code></li>
                  <li>palabras: <code>{b.w}</code></li>
                  <li>contenido: {b.body}</li>
                </ul>
              </div>
            ))}
          </div>
        ) : (
          <div className="fv-body fv-text">
            <div className="ln">
              {rawMd.split("\n").map((_, i) => <div key={i}>{i + 1}</div>)}
            </div>
            <div>
              {rawMd.split("\n").map((l, i) => {
                let cls = "lc";
                let style = {};
                if (l.startsWith("# ")) { cls += " "; style.color = "var(--y)"; style.fontWeight = 600; }
                else if (l.startsWith("## ")) { style.color = "var(--y)"; }
                else if (l.startsWith("> ")) { style.color = "var(--text-mute)"; style.fontStyle = "italic"; }
                else if (l.startsWith("- ")) { style.color = "var(--text-dim)"; }
                return <div key={i} className={cls} style={style}>{l || "\u00A0"}</div>;
              })}
            </div>
          </div>
        )}
      </div>

      <Panel title="Visión global">
        <div className="col gap-3">
          {blocks.map((b) => (
            <div key={b.n} className="row" style={{
              padding: "8px 10px",
              border: "1px solid var(--border)",
              background: "var(--panel-2)",
              borderLeft: "3px solid var(--y)",
              gap: 10,
            }}>
              <span className="mono" style={{ color: "var(--y)", fontSize: 11, width: 22 }}>{b.n.toString().padStart(2, "0")}</span>
              <div className="fill">
                <div className="display" style={{ fontSize: 12, letterSpacing: "0.04em" }}>{b.title}</div>
                <div className="mono dim" style={{ fontSize: 10, marginTop: 1 }}>{b.t} · {b.w} pal.</div>
              </div>
              <StatusDot status="ok" sm/>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function TabAudio({ onOpenFix, epId }) {
  return (
    <div className="grid gap-8" style={{ gridTemplateColumns: "1.4fr 1fr" }}>
      <Panel title={<SourceTitle kind="audio" epId={epId}/>} meta="ElevenLabs eleven_v3 · 4.8 MB" >
        <div className="col gap-8">
          {/* Waveform mock */}
          <div style={{
            background: "#0A0A0A",
            border: "1px solid var(--border)",
            padding: "20px 16px",
            position: "relative",
            height: 120,
            display: "flex",
            alignItems: "center",
            gap: 1,
          }}>
            {Array.from({ length: 90 }).map((_, i) => {
              const isFail = i > 60;
              const h = isFail ? 4 : 12 + Math.abs(Math.sin(i * 0.4)) * 60 + Math.random() * 16;
              return (
                <div key={i} style={{
                  flex: 1,
                  height: `${h}px`,
                  background: isFail ? "var(--alert)" : "var(--y)",
                  opacity: isFail ? 0.5 : 0.85,
                }}/>
              );
            })}
            <div style={{
              position: "absolute",
              left: "67%", top: 0, bottom: 0,
              width: 1, background: "var(--alert)",
            }}/>
            <div style={{
              position: "absolute",
              left: "calc(67% + 6px)",
              top: 8,
              background: "var(--alert)",
              color: "#fff",
              fontFamily: "var(--f-mono)",
              fontSize: 9,
              padding: "2px 6px",
              letterSpacing: "0.1em",
            }}>FALLO @ 03:14</div>
          </div>

          <div className="row" style={{ justifyContent: "space-between" }}>
            <div className="row gap-4">
              <Btn sm onClick={() => window.open(`/files/episodios/${epId}.mp3`, "_blank")}>
                <Icon name="play" size={11}/> Play
              </Btn>
              <span className="mono dim" style={{ fontSize: 11 }}>00:00 / 03:14 (truncado)</span>
            </div>
            <Btn sm kind="danger" onClick={() => onOpenFix({
              target: epId, error: "ElevenLabs 502 en bloque 4 · audio truncado en 03:14", id: epId,
            })}><Icon name="wrench" size={11}/> Arreglar</Btn>
          </div>

          {/* Blocks */}
          <div className="col gap-3">
            <div className="h3">Bloques generados</div>
            {[
              { n: 1, ok: true,  t: "0:00 → 0:42"  },
              { n: 2, ok: true,  t: "0:42 → 2:10"  },
              { n: 3, ok: true,  t: "2:10 → 3:14"  },
              { n: 4, ok: false, t: "3:14 → 6:20", err: "ElevenLabs 502 · 2 reintentos"  },
              { n: 5, ok: null,  t: "—" },
              { n: 6, ok: null,  t: "—" },
              { n: 7, ok: null,  t: "—" },
            ].map((b) => (
              <div key={b.n} className="row" style={{
                padding: "6px 10px",
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                borderLeft: b.ok === false ? "2px solid var(--alert)" : b.ok ? "2px solid var(--ok)" : "2px solid var(--border-2)",
                fontFamily: "var(--f-mono)",
                fontSize: 11,
              }}>
                <span style={{ width: 24, color: "var(--text-mute)" }}>{b.n.toString().padStart(2, "0")}</span>
                <span style={{ flex: 1 }}>{b.t}</span>
                {b.err && <span style={{ color: "var(--alert)" }}>{b.err}</span>}
                <StatusDot status={b.ok === false ? "alert" : b.ok ? "ok" : "empty"} sm/>
              </div>
            ))}
          </div>
        </div>
      </Panel>

      <Panel title="Configuración de voz">
        <div className="col gap-4">
          <div>
            <div className="h3 mb-4">Iago</div>
            <div className="mono dim" style={{ fontSize: 11 }}>voice_id: pNInz6obpgDQGcFmaJgB</div>
            <div className="mono" style={{ fontSize: 11, color: "var(--iago)" }}>stability 0.65 · similarity 0.78</div>
          </div>
          <div>
            <div className="h3 mb-4">María</div>
            <div className="mono dim" style={{ fontSize: 11 }}>voice_id: EXAVITQu4vr4xnSDxMaL</div>
            <div className="mono" style={{ fontSize: 11, color: "var(--maria)" }}>stability 0.72 · similarity 0.81</div>
          </div>
          <div style={{ borderTop: "1px solid var(--border)", paddingTop: 10, marginTop: 4 }}>
            <div className="mono dim" style={{ fontSize: 11 }}>Saldo ElevenLabs</div>
            <div className="mono" style={{ fontSize: 16, color: "var(--warn)" }}>8.40€</div>
            <div className="mono dim" style={{ fontSize: 10 }}>recargar antes de 10.00€</div>
          </div>
        </div>
      </Panel>
    </div>
  );
}

function TabVideo({ epId }) {
  return (
    <Panel title={<SourceTitle kind="video" epId={epId}/>} meta="Kling · pendiente">
      <div style={{
        background: "#0A0A0A",
        border: "1px dashed var(--border-2)",
        padding: 60,
        textAlign: "center",
      }}>
        <div className="display" style={{ fontSize: 14, color: "var(--text-mute)", letterSpacing: "0.16em" }}>VÍDEO NO GENERADO</div>
        <div className="mono dim" style={{ fontSize: 11, marginTop: 8 }}>Requiere audio finalizado primero · bloqueado por bloque 4</div>
        <div className="mt-12">
          <Btn sm icon={<Icon name="play" size={11}/>}
               onClick={() => onNav && onNav("lanzador")}>Lanzar generación</Btn>
        </div>
      </div>
    </Panel>
  );
}

function TabLogs({ epId }) {
  return (
    <Panel title={<SourceTitle kind="logs" epId={epId} customPath={`logs/2026-05-12_${epId}.jsonl`}/>} meta="auto-refresh 3s">
      <pre className="code" style={{ maxHeight: 480, overflow: "auto" }}>
{`{"t":"12:14:02","lvl":"ERROR","src":"eleven","msg":"502 Bad Gateway","blk":4,"retry":2}
{"t":"12:13:38","lvl":"WARN", "src":"eleven","msg":"502 Bad Gateway","blk":4,"retry":1}
{"t":"12:13:14","lvl":"INFO", "src":"eleven","msg":"block synthesized","blk":3,"dur":1.04,"cost":0.018}
{"t":"12:12:50","lvl":"INFO", "src":"eleven","msg":"block synthesized","blk":2,"dur":1.88,"cost":0.032}
{"t":"12:12:18","lvl":"INFO", "src":"eleven","msg":"block synthesized","blk":1,"dur":0.42,"cost":0.008}
{"t":"12:12:02","lvl":"INFO", "src":"runner","msg":"starting audio generation","blocks":7}
{"t":"12:11:48","lvl":"INFO", "src":"escaleta","msg":"7 blocks parsed","total_words":5530}
{"t":"12:11:30","lvl":"INFO", "src":"guion","msg":"script loaded","words":9842,"turns":142}
{"t":"12:11:24","lvl":"INFO", "src":"runner","msg":"M3_T2 pipeline start","mode":"v2"}`}
      </pre>
    </Panel>
  );
}

function TabChecks({ epId }) {
  return (
    <Panel title={<SourceTitle kind="checks" epId={epId} customPath="todas las carpetas anteriores"/>} meta="9 OK · 1 WARN · 1 ALERT">
      <div className="col gap-3">
        {CHECKS_M3.map((c) => (
          <div key={c.id} className="row" style={{
            padding: "10px 12px",
            background: "var(--panel-2)",
            border: "1px solid var(--border)",
            borderLeft: `3px solid ${
              c.status === "ok" ? "var(--ok)" :
              c.status === "warn" ? "var(--warn)" :
              c.status === "alert" ? "var(--alert)" : "var(--border-2)"
            }`,
            gap: 14,
          }}>
            <StatusDot status={c.status}/>
            <div className="fill">
              <div className="display" style={{ fontSize: 12, letterSpacing: "0.06em" }}>{c.name}</div>
              <div className="mono dim" style={{ fontSize: 11, marginTop: 2 }}>{c.detail}</div>
            </div>
            {c.status !== "ok" && (
              <Btn sm kind="ghost"
                   onClick={() => onOpenFix && onOpenFix({
                     target: c.name, id: c.id,
                     error: c.detail,
                   })}>
                Investigar
              </Btn>
            )}
          </div>
        ))}
      </div>
    </Panel>
  );
}

// ════════════════════════════════════════════════════════════
// PIZARRA — generador de episodios real (audio + video pipelines)
// ════════════════════════════════════════════════════════════

const REPO_URL = "https://github.com/bakero/maquinaria-pesada";
const REPO_BRANCH = "master";

// ── Real pipeline of maquinaria-pesada ──
// Layout: x ∈ [40, 1500], y ∈ [40, 700]
// Audio pipeline (top, y=80-260) — Video pipeline (y=420-700)
const INITIAL_NODES = [
  // ─── INPUTS (left column) ───────────────────────────────
  { id: "pdf",       label: "PDFs/resumenes/RESUMEN_Mn.pdf", kind: "input", x:  40, y:  80, code: "PDFs/resumenes/RESUMEN_Mn.pdf", repo: "PDFs/", description: "PDF resumen temático del módulo — fuente humana de partida." },
  { id: "docs",      label: "Docs vivos del repo",          kind: "input", x:  40, y: 200, code: "BIBLIA_SISTEMA.md · PODCAST.md · VIDEOPODCAST.md · PRIMERPODCAST.md", repo: "BIBLIA_SISTEMA.md", description: "4 documentos vivos que aportan APLICACIÓN_PRÁCTICA al guion." },
  { id: "spec_md",   label: "PODCAST_M_SPEC.md",            kind: "input", x:  40, y: 320, code: "PODCAST_M_SPEC.md", repo: "PODCAST_M_SPEC.md", description: "Spec normativa: estructura de bloques, balance Iago/María, frases obligatorias." },

  // ─── SPEC ENGINE (central rules) ────────────────────────
  { id: "spec_py",   label: "podcast_spec.py",              kind: "art",   x: 240, y: 200, code: "podcast_spec.py", repo: "podcast_spec.py", description: "Reglas Python derivadas del spec MD. Valida guiones y parsea bloques." },

  // ─── AUDIO PIPELINE (top swim lane) ─────────────────────
  { id: "gen_guion", label: "generar_guion.py",             kind: "ai",    x: 440, y:  80, code: "generar_guion.py", repo: "generar_guion.py", model: "claude-sonnet-4.5", description: "Genera el guion M desde PDF + docs vivos + spec." },
  { id: "guion",     label: "Guiones/Mn.txt",               kind: "art",   x: 640, y:  80, code: "Guiones/Mn_<Nombre>.txt", repo: "Guiones/", description: "Guion final con diálogo Iago/María estructurado." },
  { id: "gen_ep",    label: "generar_episodio_v2.py",       kind: "ai",    x: 840, y:  80, code: "generar_episodio_v2.py", repo: "generar_episodio_v2.py", model: "elevenlabs · eleven_v3", description: "Sintetiza audio dual con 2 voces validadas. Mezcla con sintonía y bed." },
  { id: "mp3",       label: "episodios/Mn.mp3",             kind: "art",   x:1040, y:  80, code: "episodios/Mn.mp3", repo: "episodios/", description: "Audio final del episodio. Salida de la rama audio, entrada de la rama vídeo." },
  { id: "validar",   label: "validar_episodio.py",          kind: "ai",    x:1240, y:  80, code: "validar_episodio.py", repo: "validar_episodio.py", model: "claude-haiku-4.5", description: "QA del audio: detecta gaps, comprueba duración y loudness." },

  // ─── DIVIDER (visual only, no node) ────────────────────

  // ─── VIDEO PIPELINE (bottom swim lane) ──────────────────
  // Column V1 — extracción audio
  { id: "transcr",   label: "transcriber.py",               kind: "ai",    x:  40, y: 460, code: "maquinaria_pesada_pipeline/pipeline/transcriber.py", repo: "maquinaria_pesada_pipeline/pipeline/transcriber.py", model: "whisper-large-v3 (local)", description: "Transcripción word-level del audio para subtítulos y alineación." },
  { id: "audio_an",  label: "audio_analyzer.py",            kind: "ai",    x:  40, y: 580, code: "maquinaria_pesada_pipeline/pipeline/audio_analyzer.py", repo: "maquinaria_pesada_pipeline/pipeline/audio_analyzer.py", model: "silencedetect", description: "Detecta silencios y segmentos de habla con FFmpeg." },
  { id: "sintonia",  label: "sintonia_detector.py",         kind: "ai",    x:  40, y: 700, code: "maquinaria_pesada_pipeline/pipeline/sintonia_detector.py", repo: "maquinaria_pesada_pipeline/pipeline/sintonia_detector.py", model: "scipy.correlate", description: "Cross-correlation para encontrar la sintonía con precisión exacta." },

  // Column V2 — extracción contenido
  { id: "content",   label: "content_extractor.py",         kind: "ai",    x: 240, y: 460, code: "maquinaria_pesada_pipeline/pipeline/content_extractor.py", repo: "maquinaria_pesada_pipeline/pipeline/content_extractor.py", description: "Parser de guion + PDF → estructura canónica." },
  { id: "concept",   label: "concept_extractor.py",         kind: "ai",    x: 240, y: 580, code: "maquinaria_pesada_pipeline/pipeline/concept_extractor.py", repo: "maquinaria_pesada_pipeline/pipeline/concept_extractor.py", model: "claude-haiku-4.5", description: "Extrae 1614 conceptos clave del PDF para indexación visual." },

  // Column V3 — media
  { id: "media",     label: "media_finder.py",              kind: "ai",    x: 440, y: 460, code: "maquinaria_pesada_pipeline/pipeline/media_finder.py", repo: "maquinaria_pesada_pipeline/pipeline/media_finder.py", description: "Busca imágenes/gifs en Wikipedia/Wikimedia/Tenor para cada concepto." },
  { id: "gen_esc",   label: "escaleta_generator.py",        kind: "ai",    x: 440, y: 580, code: "maquinaria_pesada_pipeline/pipeline/escaleta_generator.py", repo: "maquinaria_pesada_pipeline/pipeline/escaleta_generator.py", model: "claude-sonnet-4.5", description: "Genera escaleta markdown con timing y assets por bloque." },

  // Column V4 — escaleta artefactos
  { id: "escaleta",  label: "escaletas/Mn.md",              kind: "art",   x: 640, y: 460, code: "escaletas/Mn.md", repo: "escaletas/", description: "Escaleta canónica: 7-8 bloques con tiempos y media references." },
  { id: "parse_esc", label: "escaleta_parser.py",           kind: "ai",    x: 640, y: 580, code: "maquinaria_pesada_pipeline/pipeline/escaleta_parser.py", repo: "maquinaria_pesada_pipeline/pipeline/escaleta_parser.py", description: "Parsea escaleta MD → estructura tipada." },

  // Column V5 — pipeline assembly
  { id: "esc_pipe",  label: "escaleta_to_pipeline.py",      kind: "ai",    x: 840, y: 500, code: "maquinaria_pesada_pipeline/pipeline/escaleta_to_pipeline.py", repo: "maquinaria_pesada_pipeline/pipeline/escaleta_to_pipeline.py", description: "Construye scene_track + scene_timeline (cronograma de escenas)." },

  // Column V6 — rendering
  { id: "kling",     label: "kling_generator.py",           kind: "ai",    x:1040, y: 460, code: "maquinaria_pesada_pipeline/pipeline/kling_generator.py", repo: "maquinaria_pesada_pipeline/pipeline/kling_generator.py", model: "kling-1.6-pro (kuaishou)", description: "Image-to-video con JWT auth. Catálogo de clips estudio (~$24/episodio)." },
  { id: "overlay",   label: "overlay_renderer.py",          kind: "ai",    x:1040, y: 580, code: "maquinaria_pesada_pipeline/pipeline/overlay_renderer.py", repo: "maquinaria_pesada_pipeline/pipeline/overlay_renderer.py", description: "Renderiza overlays con PIL → frames PNG por escena." },
  { id: "subs",      label: "subtitle_generator.py",        kind: "ai",    x:1040, y: 700, code: "maquinaria_pesada_pipeline/pipeline/subtitle_generator.py", repo: "maquinaria_pesada_pipeline/pipeline/subtitle_generator.py", description: "Genera .srt blanco desde Whisper word-level." },

  // Column V7 — final composition
  { id: "compose",   label: "video_compositor.py",          kind: "ai",    x:1240, y: 580, code: "maquinaria_pesada_pipeline/pipeline/video_compositor.py", repo: "maquinaria_pesada_pipeline/pipeline/video_compositor.py", model: "ffmpeg layout-C (PIP)", description: "Compone Kling + overlays + subs + audio con ffmpeg." },

  // Final output
  { id: "mp4",       label: "videopodcast/Mn.mp4",          kind: "out",   x:1440, y: 580, code: "videopodcast/Mn.mp4", repo: "videopodcast/", description: "MP4 1080p final, listo para YouTube." },
];

const INITIAL_EDGES = [
  // Audio
  ["pdf",       "gen_guion"],
  ["docs",      "gen_guion"],
  ["spec_md",   "spec_py"],
  ["spec_py",   "gen_guion"],
  ["gen_guion", "guion"],
  ["guion",     "gen_ep"],
  ["spec_py",   "gen_ep"],
  ["gen_ep",    "mp3"],
  ["mp3",       "validar"],

  // Audio → Video bridges
  ["mp3",       "transcr"],
  ["mp3",       "audio_an"],
  ["mp3",       "sintonia"],
  ["guion",     "content"],
  ["pdf",       "concept"],

  // Video pipeline
  ["transcr",   "content"],
  ["content",   "gen_esc"],
  ["audio_an",  "gen_esc"],
  ["concept",   "media"],
  ["media",     "gen_esc"],
  ["gen_esc",   "escaleta"],
  ["escaleta",  "parse_esc"],
  ["parse_esc", "esc_pipe"],
  ["esc_pipe",  "kling"],
  ["esc_pipe",  "overlay"],
  ["transcr",   "subs"],
  ["sintonia",  "compose"],
  ["kling",     "compose"],
  ["overlay",   "compose"],
  ["subs",      "compose"],
  ["mp3",       "compose"],
  ["compose",   "mp4"],
];

// Component kinds & their canonical folders
const PZ_KINDS = [
  { id: "input",  label: "Fuente",       icon: "doc",     folder: "PDFs/",         ext: ".pdf",  hint: "Material de partida" },
  { id: "ai",     label: "Componente IA",icon: "spark",   folder: "(script .py)",  ext: ".py",   hint: "Llamada a modelo" },
  { id: "art",    label: "Artefacto",    icon: "doc",     folder: "auto",          ext: "",      hint: "Guiones/, escaletas/, logs/…" },
  { id: "out",    label: "Salida",       icon: "play",    folder: "episodios/",    ext: ".mp3",  hint: "Audio o vídeo final" },
];

// Compute anchor point on the border of a node along direction to (tx, ty)
function nodeAnchor(node, tx, ty) {
  const NODE_W = 132;
  const NODE_H = 76;
  const cx = node.x + NODE_W / 2;
  const cy = node.y + NODE_H / 2;
  const dx = tx - cx;
  const dy = ty - cy;

  if (node.kind === "ai") {
    // Circular node (110px diameter centered in 132-wide box → offset by 11)
    const r = 55;
    const len = Math.sqrt(dx * dx + dy * dy) || 1;
    return [cx + (dx / len) * r, cy + (dy / len) * r];
  }
  // Rectangle anchor: intersect with bbox border
  const hw = NODE_W / 2 - 4;
  const hh = NODE_H / 2 - 4;
  const ax = Math.abs(dx);
  const ay = Math.abs(dy);
  if (ax * hh > ay * hw) {
    // Hits left/right
    const k = hw / (ax || 1);
    return [cx + (dx > 0 ? hw : -hw), cy + dy * k];
  }
  const k = hh / (ay || 1);
  return [cx + dx * k, cy + (dy > 0 ? hh : -hh)];
}

function PagePizarra({ onNav, onOpenAI }) {
  const [nodes, setNodes] = React.useState(INITIAL_NODES);
  const [edges, setEdges] = React.useState(INITIAL_EDGES);
  const [selected, setSelected] = React.useState("gen_guion");
  const [dragging, setDragging] = React.useState(null);
  const [adding, setAdding] = React.useState(false);
  const canvasRef = React.useRef(null);

  const CW = 1640, CH = 800;

  // Drag handlers
  const onNodeMouseDown = (e, nodeId) => {
    if (e.button !== 0) return;
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const scaleX = CW / rect.width;
    const scaleY = CH / rect.height;
    setDragging({
      id: nodeId,
      offX: e.clientX * scaleX - node.x,
      offY: e.clientY * scaleY - node.y,
      scaleX, scaleY,
    });
    setSelected(nodeId);
    e.preventDefault();
    e.stopPropagation();
  };

  const onCanvasMouseMove = (e) => {
    if (!dragging) return;
    const x = e.clientX * dragging.scaleX - dragging.offX;
    const y = e.clientY * dragging.scaleY - dragging.offY;
    const cx = Math.max(10, Math.min(CW - 142, x));
    const cy = Math.max(10, Math.min(CH - 86,  y));
    setNodes((ns) => ns.map(n => n.id === dragging.id ? { ...n, x: cx, y: cy } : n));
  };

  const onCanvasMouseUp = () => setDragging(null);

  React.useEffect(() => {
    if (!dragging) return;
    const up = () => setDragging(null);
    window.addEventListener("mouseup", up);
    return () => window.removeEventListener("mouseup", up);
  }, [dragging]);

  const selNode = nodes.find(n => n.id === selected);

  const addNode = (newNode) => {
    setNodes((ns) => [...ns, newNode]);
    setSelected(newNode.id);
    setAdding(false);
  };

  const deleteSelected = () => {
    if (!selected) return;
    setNodes((ns) => ns.filter(n => n.id !== selected));
    setEdges((es) => es.filter(([a, b]) => a !== selected && b !== selected));
    setSelected(null);
  };

  const resetLayout = () => {
    setNodes(INITIAL_NODES);
    setEdges(INITIAL_EDGES);
  };

  const nAI = nodes.filter(n => n.kind === "ai").length;
  const nIn = nodes.filter(n => n.kind === "input").length;
  const nArt= nodes.filter(n => n.kind === "art").length;
  const nOut= nodes.filter(n => n.kind === "out").length;

  return (
    <div className="content">
      <PageHeader
        title="Pizarra · Generador de episodios"
        sub={`bakero/maquinaria-pesada @ master · ${nodes.length} componentes · ${edges.length} conexiones`}
        actions={
          <React.Fragment>
            <Btn sm kind="ghost" icon={<Icon name="folder" size={11}/>}
                 onClick={() => window.open(REPO_URL, "_blank")}>Repositorio</Btn>
            <Btn sm kind="ghost" icon={<Icon name="refresh" size={11}/>} onClick={resetLayout}>
              Resetear layout
            </Btn>
            <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Pipeline canónico", purpose: "improve" })}
                 icon={<Icon name="spark" size={11}/>}>Mejorar con IA</Btn>
          </React.Fragment>
        }
      />
      <SourcePills files={srcFor("pizarra")}/>

      <div className="grid gap-8" style={{ gridTemplateColumns: "1fr 400px" }}>
        {/* Canvas */}
        <Panel
          title={<span><Icon name="pipe" size={12}/> &nbsp;Pipeline real · audio + vídeo</span>}
          meta={`${nIn} fuentes · ${nAI} IA · ${nArt} artefactos · ${nOut} salidas`}
          noPad
        >
          <div style={{ overflow: "auto", maxHeight: 640 }}>
            <div
              ref={canvasRef}
              className={`pz-canvas ${dragging ? "dragging" : ""}`}
              style={{ width: CW, height: CH, minWidth: CW }}
              onMouseMove={onCanvasMouseMove}
              onMouseUp={onCanvasMouseUp}
              onClick={(e) => { if (e.target === e.currentTarget) setSelected(null); }}
            >
              {/* Lane labels */}
              <div style={{
                position: "absolute", top: 14, left: 200,
                fontFamily: "var(--f-display)", fontSize: 11, color: "var(--y)",
                letterSpacing: "0.2em", opacity: 0.6,
              }}>RAMA AUDIO · raíz del repo</div>
              <div style={{
                position: "absolute", top: 380, left: 200,
                fontFamily: "var(--f-display)", fontSize: 11, color: "var(--y)",
                letterSpacing: "0.2em", opacity: 0.6,
              }}>RAMA VÍDEO · maquinaria_pesada_pipeline/</div>

              {/* Lane separator */}
              <div style={{
                position: "absolute", left: 0, right: 0, top: 360,
                height: 8, background: "repeating-linear-gradient(-45deg, rgba(245,196,0,0.4) 0 8px, transparent 8px 16px)",
              }}/>

              {/* Toolbar */}
              <div className="pz-toolbar">
                <button className="btn primary sm" onClick={() => setAdding(!adding)}>
                  <Icon name="arrow" size={10}/> Añadir componente
                </button>
                {selected && (
                  <button className="btn danger sm" onClick={deleteSelected}>
                    <Icon name="close" size={10}/> Quitar
                  </button>
                )}
              </div>

              {/* Add modal */}
              {adding && <AddComponentForm onAdd={addNode} onCancel={() => setAdding(false)} canvasW={CW} canvasH={CH}/>}

              {/* SVG overlay with edges */}
              <svg
                className="pz-svg-overlay"
                viewBox={`0 0 ${CW} ${CH}`}
                preserveAspectRatio="none"
                style={{ width: CW, height: CH }}
              >
                <defs>
                  <marker id="arr2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto">
                    <path d="M0 0 L10 5 L0 10 z" fill="var(--y)"/>
                  </marker>
                  <marker id="arr2-sel" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto">
                    <path d="M0 0 L10 5 L0 10 z" fill="#FFD93D"/>
                  </marker>
                </defs>
                {edges.map(([a, b], i) => {
                  const na = nodes.find(n => n.id === a);
                  const nb = nodes.find(n => n.id === b);
                  if (!na || !nb) return null;
                  const nbCx = nb.x + 66;
                  const nbCy = nb.y + 38;
                  const naCx = na.x + 66;
                  const naCy = na.y + 38;
                  const [x1, y1] = nodeAnchor(na, nbCx, nbCy);
                  const [x2, y2] = nodeAnchor(nb, naCx, naCy);
                  const isSel = selected && (a === selected || b === selected);
                  return (
                    <line
                      key={i}
                      x1={x1} y1={y1} x2={x2} y2={y2}
                      stroke={isSel ? "#FFD93D" : "var(--y)"}
                      strokeOpacity={isSel ? 0.95 : 0.5}
                      strokeWidth={isSel ? 2 : 1.4}
                      markerEnd={`url(#${isSel ? "arr2-sel" : "arr2"})`}
                    />
                  );
                })}
              </svg>

              {/* Nodes */}
              {nodes.map((n) => (
                <div
                  key={n.id}
                  className={`pz-node kind-${n.kind} ${selected === n.id ? "selected" : ""} ${dragging?.id === n.id ? "dragging" : ""}`}
                  style={{ left: n.x, top: n.y }}
                  onMouseDown={(e) => onNodeMouseDown(e, n.id)}
                  onClick={(e) => { e.stopPropagation(); setSelected(n.id); }}
                >
                  <div className="pz-node-body">
                    <div className="pz-node-kind">
                      {n.kind === "ai" ? "IA" : n.kind === "input" ? "FUENTE" : n.kind === "art" ? "ARTEFACTO" : "SALIDA"}
                      {n.generated && <span style={{ color: "var(--ok)", marginLeft: 6 }}>· ✨</span>}
                    </div>
                    <div className="pz-node-label">
                      {(n.label.length > 28 ? n.label.slice(0, 26) + "…" : n.label)}
                    </div>
                    {n.model && (
                      <div className="pz-node-path" style={{ color: "var(--info)", marginTop: 2 }}>
                        {n.model}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Legend */}
              <div className="pz-legend">
                <div className="row"><span style={{ display: "inline-block", width: 12, height: 12, borderRadius: "50%", background: "var(--y-soft)", border: "1px solid var(--y)" }}/> COMPONENTE IA</div>
                <div className="row"><span style={{ display: "inline-block", width: 12, height: 12, background: "var(--panel-2)", borderLeft: "3px solid var(--info)" }}/> FUENTE</div>
                <div className="row"><span style={{ display: "inline-block", width: 12, height: 12, background: "var(--panel-2)", borderLeft: "3px solid var(--text-dim)" }}/> ARTEFACTO</div>
                <div className="row"><span style={{ display: "inline-block", width: 12, height: 12, background: "var(--panel-2)", borderLeft: "3px solid var(--ok)" }}/> SALIDA</div>
                <div className="row" style={{ marginTop: 4, color: "var(--text-mute)" }}>↻ arrastra cualquier nodo</div>
                <div className="row" style={{ color: "var(--text-mute)" }}>✨ generado por Claude</div>
              </div>
            </div>
          </div>
        </Panel>

        {/* Inspector */}
        <Panel title={<span><Icon name="doc" size={12}/> &nbsp;Inspector</span>}>
          {selNode ? (
            <NodeInspector node={selNode} onNav={onNav} onOpenAI={onOpenAI}/>
          ) : (
            <div className="mono dim" style={{ fontSize: 12, textAlign: "center", padding: "32px 0" }}>
              Selecciona un componente
            </div>
          )}
        </Panel>
      </div>

      {/* Pipeline metrics */}
      <div className="kpi-grid mt-12">
        <Kpi label="Componentes IA"   value={nAI} delta={`${nodes.filter(n => n.model).length} con modelo declarado`}/>
        <Kpi label="Tiempo medio"      value="6:42" unit="min" delta="por episodio M"/>
        <Kpi label="Coste medio"       value="0.84" unit="€"   delta="audio + ~24€ vídeo Kling"/>
        <Kpi label="Tasa éxito · 30d"  value="96.4" unit="%"   delta="3 fallos · 84 runs"/>
      </div>
    </div>
  );
}

// ── Node inspector with GitHub link, description, code ───
function NodeInspector({ node, onNav, onOpenAI }) {
  const ghUrl = node.repo ? `${REPO_URL}/blob/${REPO_BRANCH}/${node.repo}` : REPO_URL;
  const ghTreeUrl = node.repo && node.repo.endsWith("/") ? `${REPO_URL}/tree/${REPO_BRANCH}/${node.repo}` : ghUrl;

  return (
    <React.Fragment>
      <div className="display" style={{ fontSize: 15, color: "var(--y)", marginBottom: 4 }}>
        {node.label}
      </div>
      <div className="mono dim" style={{ fontSize: 11, marginBottom: 12 }}>
        {node.kind === "ai"    ? "Componente · IA" :
         node.kind === "input" ? "Fuente · Input" :
         node.kind === "art"   ? "Artefacto" : "Salida"}
        {node.generated && <span style={{ color: "var(--ok)" }}> · ✨ Claude-generated</span>}
      </div>

      {node.description && (
        <div style={{
          fontSize: 13,
          color: "var(--text-dim)",
          lineHeight: 1.55,
          background: "var(--panel-2)",
          borderLeft: "2px solid var(--y)",
          padding: "8px 12px",
          marginBottom: 12,
        }}>
          {node.description}
        </div>
      )}

      <div className="col gap-3" style={{ marginBottom: 12 }}>
        <div>
          <div className="muted mono" style={{ fontSize: 10, letterSpacing: "0.08em", marginBottom: 2 }}>ARCHIVO</div>
          <div className="mono" style={{ fontSize: 11, color: "var(--y)", wordBreak: "break-all" }}>{node.code}</div>
        </div>

        {node.model && (
          <div>
            <div className="muted mono" style={{ fontSize: 10, letterSpacing: "0.08em", marginBottom: 2 }}>MODELO</div>
            <div className="mono" style={{ fontSize: 11, color: "var(--info)" }}>{node.model}</div>
          </div>
        )}

        <div className="row gap-3 mt-4">
          <a href={ghUrl} target="_blank" rel="noopener" className="btn sm" style={{ textDecoration: "none" }}>
            <Icon name="folder" size={11}/> Abrir en GitHub
          </a>
          {node.repo && node.repo.endsWith("/") && (
            <a href={ghTreeUrl} target="_blank" rel="noopener" className="btn sm ghost" style={{ textDecoration: "none" }}>
              Carpeta ↗
            </a>
          )}
        </div>
      </div>

      <div className="h3 mt-12">Código</div>
      <pre className="code" style={{ fontSize: 11, maxHeight: 240, overflow: "auto" }}>
{node.generated && node.generatedCode
  ? node.generatedCode
  : node.kind === "ai"
  ? `# ${node.code}
"""${node.description || ""}"""

from anthropic import Anthropic
from pathlib import Path

client = Anthropic()
MODEL  = "${node.model || "claude-sonnet-4-5"}"

def run(input_path: Path) -> Path:
    ${node.id === "transcr" ? `import whisper
    model = whisper.load_model("large-v3")
    result = model.transcribe(str(input_path), word_timestamps=True)
    return write_srt(result)` : `text = input_path.read_text(encoding="utf-8")
    response = client.messages.create(
        model=MODEL,
        max_tokens=16_000,
        messages=[{"role": "user", "content": build_prompt(text)}],
    )
    out = output_path_for(input_path)
    out.write_text(response.content[0].text, encoding="utf-8")
    return out`}`
  : node.kind === "art"
  ? `# ${node.code}
# Artefacto en disco — filesystem source-of-truth.
# Generado por la fase anterior, consumido por la siguiente.`
  : node.kind === "input"
  ? `# ${node.code}
# Material de partida humano.
# Versionado fuera del pipeline.`
  : `# ${node.code}
# Salida final del pipeline.`}
      </pre>

      <div className="row gap-3 mt-12">
        <Btn sm icon={<Icon name="prompt" size={11}/>}
             onClick={() => onOpenAI && onOpenAI({ target: `Nodo · ${node.code}`, purpose: "improve",
                                                   hint: "editar lógica del nodo" })}>
          Editar
        </Btn>
        <Btn sm kind="ghost" icon={<Icon name="play" size={11}/>}
             onClick={() => onNav && onNav("lanzador")}>
          Re-ejecutar
        </Btn>
      </div>
    </React.Fragment>
  );
}

// ── Add component form: describe → Claude generates code ──
function AddComponentForm({ onAdd, onCancel }) {
  const [kind, setKind] = React.useState("ai");
  const [name, setName] = React.useState("");
  const [desc, setDesc] = React.useState("");
  const [folder, setFolder] = React.useState("maquinaria_pesada_pipeline/pipeline/");
  const [stage, setStage] = React.useState("form"); // form | generating | done
  const [code, setCode] = React.useState("");
  const [streamed, setStreamed] = React.useState("");

  React.useEffect(() => {
    if (kind === "input")  setFolder("PDFs/");
    if (kind === "ai")     setFolder("maquinaria_pesada_pipeline/pipeline/");
    if (kind === "art")    setFolder("Guiones/");
    if (kind === "out")    setFolder("episodios/");
  }, [kind]);

  const folderOptions = kind === "ai"
    ? ["maquinaria_pesada_pipeline/pipeline/", "(raíz del repo)"]
    : kind === "art"
    ? ["Guiones/", "escaletas/", "logs/"]
    : kind === "out"
    ? ["episodios/", "videopodcast/"]
    : ["PDFs/", "PDFs/resumenes/"];

  const submit = (e) => {
    e.preventDefault();
    if (!name.trim() || !desc.trim()) return;
    if (kind === "ai") {
      // Simulate Claude generating code
      setStage("generating");
      const generated = generateMockCode(name, desc);
      let i = 0;
      const tick = () => {
        i += Math.floor(Math.random() * 8) + 4;
        setStreamed(generated.slice(0, i));
        if (i < generated.length) setTimeout(tick, 16);
        else {
          setCode(generated);
          setStage("done");
        }
      };
      setTimeout(tick, 300);
    } else {
      finish("");
    }
  };

  const finish = (generatedCode) => {
    const safe = name.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/_+$/, "").slice(0, 30) || `node_${Date.now()}`;
    const ext = kind === "ai" ? ".py" : kind === "input" ? ".pdf" : kind === "out" ? ".mp3" : ".md";
    const folderFinal = folder === "(raíz del repo)" ? "" : folder;
    const node = {
      id: safe,
      label: kind === "ai" ? safe + ".py" : folderFinal + safe + ext,
      kind,
      x: 700, y: 380,
      code: folderFinal + safe + ext,
      repo: folderFinal + safe + ext,
      description: desc,
      generated: true,
      generatedCode: generatedCode || undefined,
      model: kind === "ai" ? "claude-sonnet-4.5 (interpretado)" : undefined,
    };
    onAdd(node);
  };

  return (
    <form
      className="pz-add-modal"
      onSubmit={submit}
      onMouseDown={(e) => e.stopPropagation()}
      onClick={(e) => e.stopPropagation()}
      style={{ width: stage === "form" ? 380 : 540 }}
    >
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
        <div className="display" style={{ fontSize: 11, color: "var(--y)", letterSpacing: "0.16em" }}>
          {stage === "form"       && "NUEVO COMPONENTE"}
          {stage === "generating" && "✨ CLAUDE INTERPRETANDO…"}
          {stage === "done"       && "✓ CÓDIGO GENERADO"}
        </div>
        <button type="button" className="btn ghost sm" onClick={onCancel} style={{ padding: "2px 6px" }}>
          <Icon name="close" size={10}/>
        </button>
      </div>

      {stage === "form" && (
        <div className="col gap-6">
          {/* Kind */}
          <div>
            <div className="h3 mb-4" style={{ fontSize: 10 }}>Tipo</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4 }}>
              {PZ_KINDS.map((k) => (
                <button
                  type="button" key={k.id} onClick={() => setKind(k.id)}
                  className="btn sm"
                  style={{
                    background: kind === k.id ? "var(--y)" : "transparent",
                    color: kind === k.id ? "#0D0D0D" : "var(--text)",
                    borderColor: kind === k.id ? "var(--y)" : "var(--border-2)",
                    fontWeight: kind === k.id ? 600 : 500,
                    justifyContent: "flex-start",
                  }}>
                  <Icon name={k.icon} size={10}/> {k.label}
                </button>
              ))}
            </div>
          </div>

          {/* Name */}
          <div>
            <div className="h3 mb-4" style={{ fontSize: 10 }}>Nombre del archivo</div>
            <input
              autoFocus
              className="ai-input"
              placeholder={kind === "ai" ? "resumir_pdf_corto" : "nuevo_artefacto"}
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={{ width: "100%" }}
            />
          </div>

          {/* Description — only for AI; key for Claude to generate code */}
          {kind === "ai" && (
            <div>
              <div className="row" style={{ justifyContent: "space-between", marginBottom: 4 }}>
                <div className="h3" style={{ fontSize: 10, margin: 0 }}>¿Qué debe hacer este componente?</div>
                <span className="mono" style={{ fontSize: 9, color: "var(--y)" }}>✨ Claude generará el código</span>
              </div>
              <textarea
                className="ai-input"
                placeholder="p.ej. 'Toma un PDF, extrae las 5 ideas principales con Claude Haiku y las escribe a logs/ideas_<Mn>.json'"
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
                rows={4}
                style={{ width: "100%", resize: "vertical", fontFamily: "var(--f-mono)", fontSize: 11, lineHeight: 1.5 }}
              />
            </div>
          )}

          {kind !== "ai" && (
            <div>
              <div className="h3 mb-4" style={{ fontSize: 10 }}>Descripción</div>
              <textarea
                className="ai-input"
                placeholder="Qué representa este nodo en el pipeline"
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
                rows={3}
                style={{ width: "100%", resize: "vertical", fontFamily: "var(--f-body)", fontSize: 12 }}
              />
            </div>
          )}

          {/* Folder */}
          {folderOptions.length > 1 && (
            <div>
              <div className="h3 mb-4" style={{ fontSize: 10 }}>Carpeta destino</div>
              <div className="row gap-3" style={{ flexWrap: "wrap" }}>
                {folderOptions.map((f) => (
                  <button
                    type="button" key={f} onClick={() => setFolder(f)}
                    className="btn sm"
                    style={{
                      background: folder === f ? "var(--y-soft)" : "transparent",
                      borderColor: folder === f ? "var(--y)" : "var(--border-2)",
                      color: folder === f ? "var(--y)" : "var(--text-dim)",
                      fontFamily: "var(--f-mono)",
                      fontSize: 10, letterSpacing: 0, textTransform: "none",
                    }}>{f}</button>
                ))}
              </div>
            </div>
          )}

          {/* Preview path */}
          <div style={{
            background: "var(--panel-2)",
            border: "1px dashed var(--border-2)",
            padding: "6px 10px",
            fontFamily: "var(--f-mono)",
            fontSize: 11,
          }}>
            <span className="muted">→ se creará: </span>
            <span style={{ color: "var(--y)" }}>
              {kind === "ai"
                ? (folder === "(raíz del repo)" ? "" : folder) + (name || "componente") + ".py"
                : folder + (name || "nuevo") + (kind === "input" ? ".pdf" : kind === "out" ? ".mp3" : ".md")}
            </span>
          </div>

          <div className="row gap-3" style={{ justifyContent: "flex-end" }}>
            <Btn sm kind="ghost" onClick={onCancel}>Cancelar</Btn>
            <button type="submit" className="btn primary sm" disabled={!name.trim() || !desc.trim()}>
              {kind === "ai" ? <React.Fragment><Icon name="spark" size={11}/> Crear con Claude</React.Fragment> : <React.Fragment><Icon name="check" size={11}/> Crear</React.Fragment>}
            </button>
          </div>
        </div>
      )}

      {stage === "generating" && (
        <div>
          <div className="mono dim" style={{ fontSize: 11, marginBottom: 8, color: "var(--info)" }}>
            <Icon name="spark" size={10}/> claude-sonnet-4.5 · streaming…
          </div>
          <pre className="code" style={{ fontSize: 10.5, maxHeight: 320, overflow: "auto" }}>
            {streamed}<span className="ai-cursor"/>
          </pre>
        </div>
      )}

      {stage === "done" && (
        <div>
          <div className="row gap-4" style={{ marginBottom: 10 }}>
            <span className="badge ok">✓ {code.split("\n").length} líneas</span>
            <span className="badge">claude-sonnet-4.5</span>
            <span className="badge">~0.024€</span>
          </div>
          <pre className="code" style={{ fontSize: 10.5, maxHeight: 240, overflow: "auto", marginBottom: 12 }}>
            {code}
          </pre>
          <div className="row gap-3" style={{ justifyContent: "flex-end" }}>
            <Btn sm kind="ghost" onClick={() => setStage("form")}>← Volver</Btn>
            <button type="button" className="btn primary sm" onClick={() => finish(code)}>
              <Icon name="check" size={11}/> Añadir a la pizarra
            </button>
          </div>
        </div>
      )}
    </form>
  );
}

// ── Mock code generator: realistic Python for the prototype ──
function generateMockCode(name, desc) {
  const safe = name.toLowerCase().replace(/[^a-z0-9]+/g, "_") || "componente";
  // try to infer model from description
  const usesHaiku  = /haiku|r[aá]pido|simple|extracci[oó]n/i.test(desc);
  const usesGpt    = /gpt|openai|valid|debate/i.test(desc);
  const usesEleven = /audio|voz|tts|elevenlabs/i.test(desc);
  const usesWhisper= /whisper|transcrib|subtitul/i.test(desc);

  let imports, model, body;
  if (usesEleven) {
    imports = `from elevenlabs.client import ElevenLabs\nfrom pathlib import Path`;
    model = `eleven_v3`;
    body = `eleven = ElevenLabs()
    audio = eleven.text_to_speech.convert(
        text=text_input,
        voice_id="EXAVITQu4vr4xnSDxMaL",
        model_id="eleven_v3",
    )
    out_path.write_bytes(b"".join(audio))`;
  } else if (usesWhisper) {
    imports = `import whisper\nfrom pathlib import Path`;
    model = `whisper-large-v3`;
    body = `model = whisper.load_model("large-v3")
    result = model.transcribe(
        str(audio_path),
        word_timestamps=True,
        language="es",
    )
    return result["segments"]`;
  } else if (usesGpt) {
    imports = `from openai import OpenAI\nfrom pathlib import Path`;
    model = `gpt-4o-mini`;
    body = `client = OpenAI()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content`;
  } else {
    imports = `from anthropic import Anthropic\nfrom pathlib import Path\nimport json`;
    model = usesHaiku ? `claude-haiku-4-5` : `claude-sonnet-4-5`;
    body = `client = Anthropic()
    prompt = build_prompt(input_data)
    response = client.messages.create(
        model=MODEL,
        max_tokens=${usesHaiku ? "4_000" : "16_000"},
        messages=[{"role": "user", "content": prompt}],
    )
    output_text = response.content[0].text
    out_path.write_text(output_text, encoding="utf-8")
    return out_path`;
  }

  return `#!/usr/bin/env python3
"""${safe}.py

${desc.trim()}

Generado por Claude · interpretado desde descripción del usuario.
"""
from __future__ import annotations

${imports}

MODEL = "${model}"


def run(input_path: Path, out_path: Path) -> Path:
    """Punto de entrada del componente."""
    ${body}


def build_prompt(data) -> str:
    return f"""Eres un asistente del pipeline MaquinarIA Pesada.
Tarea: ${desc.trim()}

Input:
{data}
"""


if __name__ == "__main__":
    import sys
    in_p  = Path(sys.argv[1])
    out_p = Path(sys.argv[2]) if len(sys.argv) > 2 else in_p.with_suffix(".out")
    run(in_p, out_p)
    print(f"[ok] {in_p} -> {out_p}")
`;
}
Object.assign(window, { PageEpisodio, PagePizarra });
