// PageFuentes — fuentes de contenido reales (Fase 2f).
// Datos de /api/sources: connectors/sources listan los archivos reales del
// repo. La previsualización se resuelve por extensión sobre /files/<path>.
import * as React from "react";
import { Btn, Icon, Panel, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";

function fmtSize(b) {
  if (b == null) return "—";
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / 1024 / 1024).toFixed(1)} MB`;
}

function ext(name) {
  const i = name.lastIndexOf(".");
  return i >= 0 ? name.slice(i).toLowerCase() : "";
}

function FilePreview({ item }) {
  const [text, setText] = React.useState(null);
  const e = ext(item.name);
  const isText = [".txt", ".md", ".jsonl", ".json", ".log", ".srt"].includes(e);
  const url = `/files/${item.path}`;

  React.useEffect(() => {
    setText(null);
    if (!isText) return;
    fetch(url, { cache: "no-store" })
      .then((r) => (r.ok ? r.text() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setText)
      .catch((err) => setText(`[error] ${err}`));
  }, [item.path]);

  if (e === ".pdf") {
    return (
      <div style={{ background: "#525659", border: "1px solid var(--border)" }}>
        <iframe key={url} src={`${url}#view=FitH&toolbar=1`}
                style={{ width: "100%", height: 600, border: 0, display: "block" }}
                title={item.name}/>
      </div>
    );
  }
  if ([".mp3", ".wav", ".m4a"].includes(e)) {
    return (
      <div style={{ background: "#0A0A0A", padding: 16, border: "1px solid var(--border)" }}>
        <audio key={url} src={url} controls preload="metadata"
               style={{ width: "100%", filter: "invert(0.92) hue-rotate(180deg)" }}/>
      </div>
    );
  }
  if ([".mp4", ".webm", ".mov"].includes(e)) {
    return (
      <div style={{ background: "#000", border: "1px solid var(--border)" }}>
        <video key={url} src={url} controls preload="metadata"
               style={{ width: "100%", aspectRatio: "16/9", display: "block" }}/>
      </div>
    );
  }
  if (isText) {
    return (
      <pre className="code" style={{ maxHeight: 420, overflow: "auto", fontSize: 11.5 }}>
        {text === null ? <span className="dim">Cargando…</span> : text || <span className="dim">(vacío)</span>}
      </pre>
    );
  }
  return (
    <div className="mono dim" style={{ fontSize: 12, padding: "24px 0", textAlign: "center" }}>
      Sin previsualización para {e || "este tipo"} · usa Descargar.
    </div>
  );
}

function PageFuentes({ onNav, onOpenAI }) {
  const [sources, setSources] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [src, setSrc] = React.useState(null);
  const [filter, setFilter] = React.useState("");
  const [picked, setPicked] = React.useState(null);

  React.useEffect(() => {
    fetch("/api/sources", { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => {
        const ss = (d && d.sources) || [];
        setSources(ss);
        setSrc((s) => s || (ss[0] && ss[0].id) || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const source = sources.find((s) => s.id === src) || null;
  const items = (source ? source.items : []).filter(
    (it) => it.name.toLowerCase().includes(filter.toLowerCase()),
  );

  React.useEffect(() => { setPicked(items[0] || null); }, [src, sources]);

  return (
    <div className="content">
      <PageHeader
        title="Fuentes de contenido"
        sub="Filesystem como única fuente de verdad · PDFs, guiones, escaletas, audio, vídeo, logs"
        actions={
          <Btn sm kind="primary"
               onClick={() => onOpenAI({ target: `Fuentes · ${picked?.name || "—"}`, purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Analizar con IA</Btn>
        }
      />
      <SourcePills files={srcFor("fuentes")}/>

      {loading ? (
        <div className="mono dim" style={{ fontSize: 12, padding: "40px 0", textAlign: "center" }}>
          Escaneando fuentes…
        </div>
      ) : (
        <React.Fragment>
          {/* Source-type picker */}
          <div className="row gap-3 mb-12" style={{ flexWrap: "wrap" }}>
            {sources.map((s) => (
              <div key={s.id}
                   className={`btn sm ${src === s.id ? "primary" : ""}`}
                   onClick={() => setSrc(s.id)}
                   style={{ cursor: "pointer" }}>
                <Icon name="folder" size={10}/>
                {s.label}
                <span className="mono" style={{
                  fontSize: 9, padding: "1px 5px",
                  background: src === s.id ? "rgba(0,0,0,0.2)" : "var(--panel-2)",
                  color: src === s.id ? "#0D0D0D" : "var(--text-mute)",
                  borderRadius: 2,
                }}>{s.count}</span>
              </div>
            ))}
          </div>

          <div className="grid gap-8" style={{ gridTemplateColumns: "360px 1fr" }}>
            {/* LEFT — file list */}
            <Panel
              title={<span><Icon name="folder" size={12}/> &nbsp;{source ? source.label : "—"}</span>}
              meta={source ? `${items.length}/${source.count}` : ""}
            >
              <input className="ai-input mb-8" placeholder="Filtrar por nombre…"
                     value={filter} onChange={(e) => setFilter(e.target.value)}
                     style={{ width: "100%" }}/>
              <div className="col gap-2" style={{ maxHeight: 480, overflowY: "auto" }}>
                {items.map((it) => (
                  <div key={it.path}
                       onClick={() => setPicked(it)}
                       style={{
                         padding: "8px 10px",
                         border: "1px solid",
                         borderColor: picked?.path === it.path ? "var(--y)" : "var(--border)",
                         borderLeft: picked?.path === it.path ? "3px solid var(--y)" : "1px solid var(--border)",
                         background: picked?.path === it.path ? "var(--y-soft)" : "var(--panel-2)",
                         cursor: "pointer",
                       }}>
                    <div className="mono" style={{
                      fontSize: 12,
                      color: picked?.path === it.path ? "var(--y)" : "var(--text)",
                      wordBreak: "break-all",
                    }}>{it.name}</div>
                    <div className="row gap-3 mt-2 mono" style={{ fontSize: 10, color: "var(--text-mute)" }}>
                      <span>{fmtSize(it.size)}</span><span>·</span><span>{it.t}</span>
                    </div>
                  </div>
                ))}
                {!items.length && (
                  <div className="mono dim" style={{ fontSize: 11, padding: 16, textAlign: "center" }}>
                    Sin archivos.
                  </div>
                )}
              </div>
            </Panel>

            {/* RIGHT — viewer */}
            <Panel
              title={picked ? <span><Icon name="doc" size={12}/> &nbsp;{picked.name}</span>
                            : <span>Selecciona un archivo</span>}
              meta={picked ? `${fmtSize(picked.size)} · ${picked.t}` : ""}
            >
              {picked ? (
                <div className="col gap-8">
                  <div className="row gap-4">
                    <div style={{ flex: 1 }}>
                      <div className="display" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.16em" }}>RUTA</div>
                      <div className="mono" style={{ fontSize: 12, color: "var(--y)", marginTop: 4, wordBreak: "break-all" }}>{picked.path}</div>
                    </div>
                    <Btn sm kind="ghost" icon={<Icon name="folder" size={10}/>}
                         onClick={() => fetch("/api/reveal", {
                           method: "POST",
                           headers: { "Content-Type": "application/json" },
                           body: JSON.stringify({ path: picked.path }),
                         }).catch(() => {})}>
                      Revelar
                    </Btn>
                    <Btn sm icon={<Icon name="doc" size={10}/>}
                         onClick={() => window.open(`/files/${picked.path}`, "_blank")}>
                      Descargar
                    </Btn>
                  </div>
                  <FilePreview item={picked}/>
                </div>
              ) : (
                <div className="mono dim" style={{ textAlign: "center", padding: 40, fontSize: 12 }}>
                  Sin selección.
                </div>
              )}
            </Panel>
          </div>
        </React.Fragment>
      )}
    </div>
  );
}

export { PageFuentes };
