// TabEscaleta — escaleta real del episodio (Fase 2). Carga /files/<path>.
import * as React from "react";
import { Icon, Panel } from "../../../components";

export interface TabEscaletaProps {
  path: string | null;
}

export function TabEscaleta({ path }: TabEscaletaProps) {
  const [text, setText] = React.useState<string | null>(null);
  const [err, setErr] = React.useState("");

  React.useEffect(() => {
    setText(null); setErr("");
    if (!path) return;
    fetch(`/files/${path}`, { cache: "no-store" })
      .then((r) => (r.ok ? r.text() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setText)
      .catch((e) => setErr(String(e)));
  }, [path]);

  if (!path) {
    return (
      <Panel title="Escaleta">
        <div className="mono dim" style={{ fontSize: 12, padding: "24px 0", textAlign: "center" }}>
          Este episodio aún no tiene escaleta.
        </div>
      </Panel>
    );
  }

  const lines = text ? text.split("\n") : [];

  return (
    <div className="fv">
      <div className="fv-chrome">
        <Icon name="doc" size={11} />
        <span className="fv-path">{path}</span>
        <span className="fv-meta">{lines.length} líneas</span>
        <span className="fill" />
        <a href={`/files/${path}`} target="_blank" rel="noopener" className="btn ghost sm"
           title="Abrir" style={{ textDecoration: "none" }}>
          <Icon name="folder" size={11} />
        </a>
      </div>
      {err ? (
        <div className="fv-body" style={{ padding: 20 }}>
          <span className="mono" style={{ color: "var(--alert)", fontSize: 12 }}>Error: {err}</span>
        </div>
      ) : text === null ? (
        <div className="fv-body" style={{ padding: 20 }}>
          <span className="mono dim" style={{ fontSize: 12 }}>Cargando…</span>
        </div>
      ) : (
        <div className="fv-body fv-text">
          <div className="ln">{lines.map((_, i) => <div key={i}>{i + 1}</div>)}</div>
          <div>
            {lines.map((l, i) => {
              const style: React.CSSProperties = {};
              if (l.startsWith("# ")) { style.color = "var(--y)"; style.fontWeight = 600; }
              else if (l.startsWith("## ")) style.color = "var(--y)";
              else if (l.startsWith("> ")) { style.color = "var(--text-mute)"; style.fontStyle = "italic"; }
              else if (l.startsWith("- ")) style.color = "var(--text-dim)";
              return <div key={i} className="lc" style={style}>{l || " "}</div>;
            })}
          </div>
        </div>
      )}
    </div>
  );
}
