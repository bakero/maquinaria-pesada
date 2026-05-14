// TabLogs — logs reales de producción del episodio (Fase 2).
import * as React from "react";
import { Icon, Panel } from "../../../components";

export interface TabLogsProps {
  paths: string[];
}

export function TabLogs({ paths }: TabLogsProps) {
  const [sel, setSel] = React.useState<string | null>(paths[0] ?? null);
  const [text, setText] = React.useState<string | null>(null);

  React.useEffect(() => {
    setSel(paths[0] ?? null);
  }, [paths.join("|")]);

  React.useEffect(() => {
    setText(null);
    if (!sel) return;
    fetch(`/files/${sel}`, { cache: "no-store" })
      .then((r) => (r.ok ? r.text() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setText)
      .catch((e) => setText(`[error] ${e}`));
  }, [sel]);

  if (!paths.length) {
    return (
      <Panel title="Logs de producción">
        <div className="mono dim" style={{ fontSize: 12, padding: "24px 0", textAlign: "center" }}>
          Este episodio aún no tiene logs de producción.
        </div>
      </Panel>
    );
  }

  return (
    <div className="grid gap-8" style={{ gridTemplateColumns: "260px 1fr" }}>
      <Panel title={<span><Icon name="folder" size={12} /> &nbsp;Logs</span>} meta={`${paths.length}`} noPad>
        <div className="col gap-2" style={{ padding: 10 }}>
          {paths.map((p) => (
            <div key={p}
                 onClick={() => setSel(p)}
                 style={{
                   padding: "8px 10px",
                   border: "1px solid",
                   borderColor: sel === p ? "var(--y)" : "var(--border)",
                   background: sel === p ? "var(--y-soft)" : "var(--panel-2)",
                   cursor: "pointer",
                 }}>
              <span className="mono" style={{ fontSize: 11, color: sel === p ? "var(--y)" : "var(--text)", wordBreak: "break-all" }}>
                {p.split("/").pop()}
              </span>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title={<span><Icon name="log" size={12} /> &nbsp;{sel || "—"}</span>} noPad>
        <pre className="code" style={{ maxHeight: 480, overflow: "auto", fontSize: 11.5, margin: 0 }}>
          {text === null ? <span className="dim">Cargando…</span> : text || <span className="dim">(vacío)</span>}
        </pre>
      </Panel>
    </div>
  );
}
