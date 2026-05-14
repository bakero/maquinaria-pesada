// PagePizarra — extraído del monolito (Fase 1b).
import * as React from "react";
import { Btn, Icon, Panel, Kpi, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";

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
  const loadedRef = React.useRef(false);

  const CW = 1640, CH = 800;

  // Carga el lienzo persistido (cockpit/pizarra_board.json). Si no hay,
  // se queda con el pipeline por defecto. Marca loadedRef para no
  // sobrescribir el archivo con el default antes de leerlo.
  React.useEffect(() => {
    let alive = true;
    fetch("/api/pizarra", { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => {
        if (!alive) return;
        const b = d && d.board;
        if (b && Array.isArray(b.nodes) && b.nodes.length) {
          setNodes(b.nodes);
          setEdges(Array.isArray(b.edges) ? b.edges : []);
        }
      })
      .catch(() => {})
      .finally(() => { loadedRef.current = true; });
    return () => { alive = false; };
  }, []);

  // Persiste el lienzo tras cualquier cambio (add/quitar/reset/arrastrar),
  // con debounce para no escribir en cada frame de un arrastre.
  React.useEffect(() => {
    if (!loadedRef.current) return undefined;
    const id = setTimeout(() => {
      fetch("/api/pizarra", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nodes, edges }),
      }).catch(() => {});
    }, 600);
    return () => clearTimeout(id);
  }, [nodes, edges]);

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

  const submit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !desc.trim()) return;
    if (kind !== "ai") {
      finish("");
      return;
    }
    // Generación real con Claude vía /api/pizarra/generate-component.
    setStage("generating");
    setStreamed("");
    try {
      const res = await fetch("/api/pizarra/generate-component", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description: desc, kind }),
      });
      const data = await res.json();
      if (data.ok && data.code) {
        setCode(data.code);
        setStage("done");
      } else {
        setStreamed(data.error || data.code || "Claude no disponible");
        setStage("error");
      }
    } catch (err) {
      setStreamed(String(err));
      setStage("error");
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
          {stage === "generating" && "✨ CLAUDE GENERANDO…"}
          {stage === "done"       && "✓ CÓDIGO GENERADO"}
          {stage === "error"      && "✕ NO SE PUDO GENERAR"}
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
            <Icon name="spark" size={10}/> claude-sonnet-4-6 · generando código…
          </div>
          <pre className="code" style={{ fontSize: 10.5, maxHeight: 320, overflow: "auto" }}>
            <span className="ai-cursor"/>
          </pre>
        </div>
      )}

      {stage === "error" && (
        <div>
          <div className="mono" style={{ fontSize: 11, color: "var(--alert)", marginBottom: 8 }}>
            No se pudo generar el componente.
          </div>
          <pre className="code" style={{ fontSize: 10.5, maxHeight: 200, overflow: "auto", marginBottom: 12 }}>
            {streamed}
          </pre>
          <div className="row gap-3" style={{ justifyContent: "flex-end" }}>
            <Btn sm kind="ghost" onClick={() => setStage("form")}>← Volver</Btn>
          </div>
        </div>
      )}

      {stage === "done" && (
        <div>
          <div className="row gap-4" style={{ marginBottom: 10 }}>
            <span className="badge ok">✓ {code.split("\n").length} líneas</span>
            <span className="badge">generado por Claude</span>
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

export { PagePizarra };
