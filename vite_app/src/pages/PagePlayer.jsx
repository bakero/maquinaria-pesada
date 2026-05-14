// PagePlayer — previsualización de audio/vídeo reales (Fase 2f).
// Cola desde /api/sources (connectors source 'audio' y 'video');
// reproducción vía /files/<path>.
import * as React from "react";
import { Btn, Icon, Panel, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";

function fmtSize(b) {
  if (b == null) return "—";
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / 1024 / 1024).toFixed(1)} MB`;
}

function PagePlayer({ onNav, onOpenAI }) {
  const [sources, setSources] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [tab, setTab] = React.useState("audio");
  const [pick, setPick] = React.useState(null);

  React.useEffect(() => {
    fetch("/api/sources", { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => { setSources((d && d.sources) || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const byId = Object.fromEntries(sources.map((s) => [s.id, s]));
  const items = (byId[tab] && byId[tab].items) || [];
  React.useEffect(() => { setPick(items[0]?.path || null); }, [tab, sources]);
  const sel = items.find((i) => i.path === pick) || items[0] || null;

  return (
    <div className="content">
      <PageHeader
        title="Previsualizar"
        sub="Audio y vídeo generados · escucha y revisa antes de publicar"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: `Preview · ${sel?.name || "—"}`, purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Sugerir checks</Btn>
        }
      />
      <SourcePills files={srcFor("player")}/>

      <div className="tabs mb-12">
        {[{ id: "audio", label: "Audio" }, { id: "video", label: "Vídeo" }].map((t) => (
          <div key={t.id} className={`tab ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
            <Icon name="play" size={11}/>
            {t.label}
            <span className="badge" style={{ marginLeft: 4 }}>
              {(byId[t.id] && byId[t.id].count) || 0}
            </span>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="mono dim" style={{ fontSize: 12, padding: "40px 0", textAlign: "center" }}>
          Cargando cola…
        </div>
      ) : (
        <div className="grid gap-8" style={{ gridTemplateColumns: "280px 1fr" }}>
          <Panel title={<span><Icon name="folder" size={12}/> &nbsp;Cola</span>} noPad>
            <div className="col gap-2" style={{ padding: 10, maxHeight: 520, overflow: "auto" }}>
              {items.map((it) => (
                <div key={it.path}
                     onClick={() => setPick(it.path)}
                     style={{
                       padding: "8px 10px",
                       border: "1px solid",
                       borderColor: pick === it.path ? "var(--y)" : "var(--border)",
                       borderLeft: pick === it.path ? "3px solid var(--y)" : "1px solid var(--border)",
                       background: pick === it.path ? "var(--y-soft)" : "var(--panel-2)",
                       cursor: "pointer",
                     }}>
                  <div className="mono" style={{ fontSize: 12, color: pick === it.path ? "var(--y)" : "var(--text)", wordBreak: "break-all" }}>
                    {it.name}
                  </div>
                  <div className="mono dim" style={{ fontSize: 10, marginTop: 2 }}>{fmtSize(it.size)} · {it.t}</div>
                </div>
              ))}
              {items.length === 0 && (
                <div className="mono dim" style={{ fontSize: 11, padding: 16, textAlign: "center" }}>
                  Sin archivos {tab === "audio" ? "de audio" : "de vídeo"}.
                </div>
              )}
            </div>
          </Panel>

          <Panel
            title={<span><Icon name="play" size={12}/> &nbsp;{sel?.name || "—"}</span>}
            meta={sel ? `${fmtSize(sel.size)} · ${sel.t}` : ""}
          >
            {!sel ? (
              <div className="mono dim" style={{ fontSize: 12, padding: "40px 0", textAlign: "center" }}>
                Selecciona un archivo de la cola.
              </div>
            ) : tab === "audio" ? (
              <div className="col gap-8">
                <div style={{
                  background: "#0A0A0A", padding: "24px 20px", border: "1px solid var(--border)",
                  borderLeft: "3px solid var(--y)",
                }}>
                  <audio key={sel.path} src={`/files/${sel.path}`} controls preload="metadata"
                         style={{ width: "100%", filter: "invert(0.92) hue-rotate(180deg)" }}/>
                </div>
                <div className="row" style={{ justifyContent: "flex-end" }}>
                  <a href={`/files/${sel.path}`} download={sel.name} className="btn sm ghost" style={{ textDecoration: "none" }}>
                    <Icon name="folder" size={11}/> Descargar
                  </a>
                </div>
              </div>
            ) : (
              <div className="col gap-8">
                <div style={{ background: "#000", border: "1px solid var(--border)", borderLeft: "3px solid var(--y)" }}>
                  <video key={sel.path} src={`/files/${sel.path}`} controls preload="metadata"
                         style={{ width: "100%", aspectRatio: "16/9", display: "block", background: "#000" }}/>
                </div>
                <div className="row" style={{ justifyContent: "flex-end" }}>
                  <a href={`/files/${sel.path}`} download={sel.name} className="btn sm ghost" style={{ textDecoration: "none" }}>
                    <Icon name="folder" size={11}/> Descargar
                  </a>
                </div>
              </div>
            )}
          </Panel>
        </div>
      )}
    </div>
  );
}

export { PagePlayer };
