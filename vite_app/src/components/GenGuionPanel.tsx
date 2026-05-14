// Generación de guion por episodio + traza de validación.
// Lanza generar_guion.py / generar_guion_t.py para UN episodio concreto y
// muestra la traza de validación/regeneración (intentos, issues hard/soft).
import * as React from "react";
import { Btn } from "./Btn";
import { Icon } from "./Icon";
import { Panel } from "./Panel";
import { StatusDot } from "./StatusDot";

interface GenLog {
  ok: boolean;
  exists?: boolean;
  verdict?: "ok" | "warn" | "running";
  attempts?: number;
  hard_issues?: string[];
  soft_issues?: string[];
  text?: string;
}

export interface GenGuionPanelProps {
  epId: string;
}

export function GenGuionPanel({ epId }: GenGuionPanelProps) {
  const [log, setLog]   = React.useState<GenLog | null>(null);
  const [busy, setBusy] = React.useState(false);
  const [msg, setMsg]   = React.useState("");
  const [open, setOpen] = React.useState(false);
  const pollRef = React.useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPoll = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  };

  const load = React.useCallback(() => {
    fetch(`/api/episode/${encodeURIComponent(epId)}/gen-log`, { cache: "no-store" })
      .then((r) => r.json())
      .then((d: GenLog) => {
        setLog(d);
        if (d && d.exists && d.verdict && d.verdict !== "running") {
          stopPoll();
          setBusy(false);
        }
      })
      .catch(() => {});
  }, [epId]);

  React.useEffect(() => {
    load();
    return stopPoll;
  }, [load]);

  const generate = () => {
    setBusy(true);
    setMsg("");
    fetch(`/api/episode/${encodeURIComponent(epId)}/generate`, { method: "POST" })
      .then((r) => r.json())
      .then((d) => {
        if (!d.ok) {
          setBusy(false);
          setMsg(d.error || "No se pudo lanzar la generación");
          return;
        }
        setMsg(`Generando… (pid ${d.pid}) · ${d.pdf}`);
        stopPoll();
        pollRef.current = setInterval(load, 3000);
      })
      .catch((e) => { setBusy(false); setMsg(String(e)); });
  };

  const verdict = log && log.exists ? log.verdict : null;
  const vColor = verdict === "ok" ? "var(--ok)"
    : verdict === "warn" ? "var(--warn)"
    : verdict === "running" ? "var(--info)" : "var(--text-mute)";
  const vLabel = verdict === "ok" ? "Validación OK"
    : verdict === "warn" ? "Guardado con issues"
    : verdict === "running" ? "En curso…"
    : "Sin generar todavía";
  const hard = (log && log.hard_issues) || [];
  const soft = (log && log.soft_issues) || [];

  return (
    <Panel title={<span><Icon name="prompt" size={12} /> &nbsp;Generar guion · {epId}</span>}>
      <div className="col gap-6">
        <Btn kind="primary" disabled={busy} onClick={generate}
             icon={<Icon name="play" size={11} />}>
          {busy ? "Generando…" : (verdict ? "Regenerar este guion" : "Generar este guion")}
        </Btn>
        {msg && <div className="mono" style={{ fontSize: 11, color: "var(--text-dim)" }}>{msg}</div>}

        {/* Traza de validación */}
        <div className="row gap-4" style={{ alignItems: "center" }}>
          <StatusDot status={verdict === "ok" ? "ok" : verdict === "warn" ? "warn"
            : verdict === "running" ? "run" : "empty"} sm />
          <span className="display" style={{ fontSize: 11, letterSpacing: "0.08em", color: vColor }}>
            {vLabel}
          </span>
          {log && log.exists && typeof log.attempts === "number" && (
            <span className="mono dim" style={{ fontSize: 11 }}>
              · {log.attempts} intento{log.attempts === 1 ? "" : "s"}
            </span>
          )}
        </div>

        {hard.length > 0 && (
          <div className="col gap-3">
            <div className="mono" style={{ fontSize: 10, color: "var(--alert)", letterSpacing: "0.08em" }}>
              ISSUES HARD ({hard.length})
            </div>
            {hard.map((it, i) => (
              <div key={i} className="mono" style={{ fontSize: 11, color: "var(--text-dim)", lineHeight: 1.4 }}>
                <span style={{ color: "var(--alert)" }}>● </span>{it}
              </div>
            ))}
          </div>
        )}
        {soft.length > 0 && (
          <div className="col gap-3">
            <div className="mono" style={{ fontSize: 10, color: "var(--warn)", letterSpacing: "0.08em" }}>
              ISSUES SOFT ({soft.length})
            </div>
            {soft.map((it, i) => (
              <div key={i} className="mono" style={{ fontSize: 11, color: "var(--text-dim)", lineHeight: 1.4 }}>
                <span style={{ color: "var(--warn)" }}>● </span>{it}
              </div>
            ))}
          </div>
        )}

        {log && log.exists && log.text && (
          <div className="col gap-3">
            <button className="btn ghost sm" onClick={() => setOpen((o) => !o)}>
              <Icon name="log" size={10} /> {open ? "Ocultar traza completa" : "Ver traza completa"}
            </button>
            {open && (
              <pre className="mono" style={{
                fontSize: 10, lineHeight: 1.45, maxHeight: 280, overflow: "auto",
                background: "var(--panel-2)", border: "1px solid var(--border)",
                padding: "8px 10px", whiteSpace: "pre-wrap", wordBreak: "break-word",
              }}>{log.text}</pre>
            )}
          </div>
        )}
      </div>
    </Panel>
  );
}
