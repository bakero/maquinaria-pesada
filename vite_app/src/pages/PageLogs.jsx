// PageLogs — logs de producción reales (Fase 2).
// Lista de archivos: /api/logs (logs/ del repo). Contenido: /files/logs/<path>.
// "Auto" hace tail real (re-fetch periódico), no líneas sintéticas.
import * as React from "react";
import { Btn, Icon, Panel, Kpi, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";

function fmtSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function PageLogs({ onNav, onOpenAI }) {
  const [files, setFiles] = React.useState([]);
  const [sel, setSel] = React.useState(null);
  const [content, setContent] = React.useState("");
  const [auto, setAuto] = React.useState(false);
  const [filter, setFilter] = React.useState("");
  const pollRef = React.useRef(null);

  // Lista de archivos al montar.
  React.useEffect(() => {
    fetch("/api/logs", { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => {
        const fs = (d && d.files) || [];
        setFiles(fs);
        if (fs.length && !sel) setSel(fs[0].path);
      })
      .catch(() => setFiles([]));
  }, []);

  // Carga el contenido del archivo seleccionado.
  const loadContent = React.useCallback((path) => {
    if (!path) return;
    fetch(`/files/logs/${path}`, { cache: "no-store" })
      .then((r) => (r.ok ? r.text() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setContent)
      .catch((e) => setContent(`[error al leer ${path}] ${e}`));
  }, []);

  React.useEffect(() => { loadContent(sel); }, [sel, loadContent]);

  // Auto-refresh: tail real del archivo seleccionado.
  React.useEffect(() => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    if (auto && sel) {
      pollRef.current = setInterval(() => loadContent(sel), 3000);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [auto, sel, loadContent]);

  const lines = content ? content.split("\n").filter((l) => l.length) : [];
  const filtered = filter
    ? lines.filter((l) => l.toLowerCase().includes(filter.toLowerCase()))
    : lines;

  const counts = lines.reduce((acc, l) => {
    const u = l.toUpperCase();
    if (u.includes("ERROR")) acc.err++;
    else if (u.includes("WARN")) acc.warn++;
    else acc.info++;
    return acc;
  }, { info: 0, warn: 0, err: 0 });

  return (
    <div className="content">
      <PageHeader
        title="Logs de producción"
        sub="Archivos reales de logs/ · auto-refresh opcional · diagnóstico IA sobre las últimas líneas"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({
            target: `Log · ${sel || "—"}`, purpose: "improve",
          })} icon={<Icon name="spark" size={11}/>}>Diagnóstico con IA</Btn>
        }
      />
      <SourcePills files={srcFor("logs")}/>

      <div className="kpi-grid mb-12">
        <Kpi label="Líneas"  value={lines.length} delta={`auto-refresh ${auto ? "ON" : "OFF"}`} deltaDir={auto ? "up" : ""}/>
        <Kpi label="INFO"    value={counts.info}/>
        <Kpi label="WARN"    value={counts.warn} delta={counts.warn ? "atención" : "ok"}/>
        <Kpi label="ERROR"   value={counts.err}  delta={counts.err ? "investigar" : "limpio"} deltaDir={counts.err ? "dn" : "up"}/>
      </div>

      <div className="grid gap-8" style={{ gridTemplateColumns: "280px 1fr" }}>
        <Panel title={<span><Icon name="folder" size={12}/> &nbsp;Archivos</span>} meta={`${files.length}`} noPad>
          <div className="col gap-2" style={{ padding: 10, maxHeight: 520, overflow: "auto" }}>
            {files.map((l) => (
              <div key={l.path}
                   onClick={() => setSel(l.path)}
                   style={{
                     padding: "8px 10px",
                     border: "1px solid",
                     borderColor: sel === l.path ? "var(--y)" : "var(--border)",
                     background: sel === l.path ? "var(--y-soft)" : "var(--panel-2)",
                     cursor: "pointer",
                   }}>
                <div className="mono" style={{ fontSize: 11, color: sel === l.path ? "var(--y)" : "var(--text)", wordBreak: "break-all" }}>
                  {l.path}
                </div>
                <div className="mono dim" style={{ fontSize: 10, marginTop: 2 }}>{fmtSize(l.size)} · {l.t}</div>
              </div>
            ))}
            {files.length === 0 && (
              <div className="mono dim" style={{ fontSize: 11, padding: 12, textAlign: "center" }}>
                Sin archivos en logs/
              </div>
            )}
          </div>
        </Panel>

        <Panel
          title={<span><Icon name="log" size={12}/> &nbsp;{sel || "—"}</span>}
          meta={auto ? "live · 3s" : "snapshot"}
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
            {filtered.length === 0 ? (
              <div className="dim">{sel ? "(sin líneas que coincidan)" : "Selecciona un archivo"}</div>
            ) : filtered.map((l, i) => {
              const u = l.toUpperCase();
              const isErr = u.includes("ERROR");
              const isWarn = u.includes("WARN");
              const color = isErr ? "var(--alert)" : isWarn ? "var(--warn)" : "var(--text-dim)";
              return <div key={i} style={{ color, whiteSpace: "pre-wrap" }}>{l}</div>;
            })}
            {auto && <span className="ai-cursor"/>}
          </pre>
        </Panel>
      </div>
    </div>
  );
}

export { PageLogs };
