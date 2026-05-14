// TabGuion — guion real del episodio (Fase 2). Carga /files/<path>.
import * as React from "react";
import { Btn, Icon, Panel, Speaker } from "../../../components";

export interface TabGuionProps {
  epId: string;
  path: string | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onOpenAI: (ctx: any) => void;
}

const SPEAKER_RE = /^\s*(IAGO|MAR[IÍ]A)\s*:\s*(.*)$/i;

export function TabGuion({ epId, path, onOpenAI }: TabGuionProps) {
  const [mode, setMode] = React.useState("read"); // read | raw
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
      <Panel title="Guion">
        <div className="mono dim" style={{ fontSize: 12, padding: "24px 0", textAlign: "center" }}>
          Este episodio aún no tiene guion. Genéralo desde el panel "Generar guion" de arriba.
        </div>
      </Panel>
    );
  }

  const lines = text ? text.split("\n") : [];
  const turns = lines
    .map((l) => { const m = SPEAKER_RE.exec(l); return m ? { who: m[1].toUpperCase().startsWith("I") ? "iago" : "maria", text: m[2] } : null; })
    .filter(Boolean) as { who: string; text: string }[];
  const words = text ? text.trim().split(/\s+/).filter(Boolean).length : 0;
  const kb = text ? (new Blob([text]).size / 1024).toFixed(1) : "0";

  return (
    <div className="grid gap-8" style={{ gridTemplateColumns: "1.8fr 1fr" }}>
      <div className="fv">
        <div className="fv-chrome">
          <Icon name="doc" size={11} />
          <span className="fv-path">{path}</span>
          <span className="fv-meta">{words} palabras · {turns.length} turnos · {kb} KB</span>
          <span className="fill" />
          <div className="fv-toggle">
            <button className={mode === "read" ? "on" : ""} onClick={() => setMode("read")}>Lectura</button>
            <button className={mode === "raw" ? "on" : ""} onClick={() => setMode("raw")}>Raw</button>
          </div>
        </div>

        {err ? (
          <div className="fv-body" style={{ padding: 20 }}>
            <span className="mono" style={{ color: "var(--alert)", fontSize: 12 }}>Error al leer el guion: {err}</span>
          </div>
        ) : text === null ? (
          <div className="fv-body" style={{ padding: 20 }}>
            <span className="mono dim" style={{ fontSize: 12 }}>Cargando…</span>
          </div>
        ) : mode === "read" ? (
          <div className="fv-body" style={{ padding: "20px 28px" }}>
            <div className="col gap-6" style={{ fontFamily: "var(--f-body)", fontSize: 15, lineHeight: 1.6 }}>
              {turns.length === 0 ? (
                <pre className="mono" style={{ fontSize: 12, whiteSpace: "pre-wrap" }}>{text}</pre>
              ) : turns.map((t, i) => (
                <div key={i} style={{ display: "grid", gridTemplateColumns: "92px 1fr", gap: 14, padding: "8px 0", borderBottom: "1px dashed var(--border)" }}>
                  <Speaker who={t.who} />
                  <div>{t.text}</div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="fv-body fv-text">
            <div className="ln">{lines.map((_, i) => <div key={i}>{i + 1}</div>)}</div>
            <div>{lines.map((l, i) => <div key={i} className="lc">{l || " "}</div>)}</div>
          </div>
        )}
      </div>

      <div className="col gap-8">
        <Panel title="Métricas del guion">
          <div className="col gap-4 mono" style={{ fontSize: 13 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="muted">Palabras</span><span>{words.toLocaleString("es-ES")}</span>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="muted">Turnos</span><span>{turns.length}</span>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="muted">Líneas</span><span>{lines.length}</span>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="muted">Tamaño</span><span>{kb} KB</span>
            </div>
          </div>
        </Panel>
        <Panel title="Acciones">
          <div className="col gap-3">
            <Btn icon={<Icon name="prompt" size={11} />}
                 onClick={() => onOpenAI({ target: `Guion ${epId}`, purpose: "improve",
                                           hint: "regenerar preservando tono" })}>
              Regenerar (preservar tono)
            </Btn>
            <Btn kind="ghost" icon={<Icon name="check" size={11} />}
                 onClick={() => onOpenAI({ target: `Guion ${epId}`, purpose: "improve",
                                           hint: "validación dual Claude vs GPT" })}>
              Validar con GPT (dual)
            </Btn>
            <Btn kind="ghost" icon={<Icon name="doc" size={11} />}
                 onClick={() => window.open(`/files/${path}`, "_blank")}>
              Abrir .txt
            </Btn>
          </div>
        </Panel>
      </div>
    </div>
  );
}
