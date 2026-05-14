import { Btn, Panel, SourceTitle, StatusDot } from "../../../components";
import { CHECKS_M3 } from "../../../data";
import type { OpenFixFn } from "../types";

export interface TabChecksProps {
  epId: string;
  onOpenFix: OpenFixFn;
}

export function TabChecks({ epId, onOpenFix }: TabChecksProps) {
  return (
    <Panel
      title={<SourceTitle kind="checks" epId={epId} customPath="todas las carpetas anteriores" />}
      meta="9 OK · 1 WARN · 1 ALERT"
    >
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
            <StatusDot status={c.status} />
            <div className="fill">
              <div className="display" style={{ fontSize: 12, letterSpacing: "0.06em" }}>{c.name}</div>
              <div className="mono dim" style={{ fontSize: 11, marginTop: 2 }}>{c.detail}</div>
            </div>
            {c.status !== "ok" && (
              <Btn sm kind="ghost"
                   onClick={() => onOpenFix({ target: c.name, id: c.id, error: c.detail })}>
                Investigar
              </Btn>
            )}
          </div>
        ))}
      </div>
    </Panel>
  );
}
