// TabChecks — verificaciones reales del episodio (Fase 2).
// Datos de GET /api/episode/<id>/checks (cockpit.core.verifications.run_all).
import * as React from "react";
import { Btn, Panel, StatusDot } from "../../../components";
import type { OpenFixFn } from "../types";

export interface TabChecksProps {
  epId: string;
  onOpenFix: OpenFixFn;
}

interface Check { id: string; label: string; status: string; detail: string; }

// verifications usa ok|fail|warn|na; StatusDot usa ok|alert|warn|empty.
const DOT = { ok: "ok", fail: "alert", warn: "warn", na: "empty" } as Record<string, string>;
const COLOR = {
  ok: "var(--ok)", fail: "var(--alert)", warn: "var(--warn)", na: "var(--border-2)",
} as Record<string, string>;

export function TabChecks({ epId, onOpenFix }: TabChecksProps) {
  const [data, setData] = React.useState<{
    ok: boolean; error?: string; groups: Record<string, Check[]>;
  } | null>(null);

  React.useEffect(() => {
    setData(null);
    fetch(`/api/episode/${encodeURIComponent(epId)}/checks`, { cache: "no-store" })
      .then((r) => r.json())
      .then(setData)
      .catch((e) => setData({ ok: false, error: String(e), groups: {} }));
  }, [epId]);

  if (data === null) {
    return (
      <Panel title="Verificaciones">
        <div className="mono dim" style={{ fontSize: 12, padding: "24px 0", textAlign: "center" }}>
          Ejecutando verificaciones…
        </div>
      </Panel>
    );
  }
  if (!data.ok) {
    return (
      <Panel title="Verificaciones">
        <div className="mono" style={{ fontSize: 12, padding: "24px 0", textAlign: "center", color: "var(--alert)" }}>
          No se pudieron ejecutar: {data.error || "error"}
        </div>
      </Panel>
    );
  }

  const groups = Object.entries(data.groups);
  const allChecks = groups.flatMap(([, cs]) => cs);
  const nOk = allChecks.filter((c) => c.status === "ok").length;
  const nWarn = allChecks.filter((c) => c.status === "warn").length;
  const nFail = allChecks.filter((c) => c.status === "fail").length;

  return (
    <Panel title={<span>Verificaciones · {epId}</span>}
           meta={`${nOk} OK · ${nWarn} WARN · ${nFail} FAIL`}>
      <div className="col gap-6">
        {groups.map(([group, checks]) => (
          <div key={group} className="col gap-3">
            <div className="display" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.16em" }}>
              {group.toUpperCase()}
            </div>
            {checks.map((c) => (
              <div key={c.id} className="row" style={{
                padding: "10px 12px",
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                borderLeft: `3px solid ${COLOR[c.status] || "var(--border-2)"}`,
                gap: 14,
              }}>
                <StatusDot status={DOT[c.status] || "empty"} />
                <div className="fill">
                  <div className="display" style={{ fontSize: 12, letterSpacing: "0.06em" }}>{c.label}</div>
                  <div className="mono dim" style={{ fontSize: 11, marginTop: 2 }}>{c.detail || "—"}</div>
                </div>
                {c.status === "fail" && (
                  <Btn sm kind="ghost"
                       onClick={() => onOpenFix({ target: c.label, id: c.id, error: c.detail })}>
                    Investigar
                  </Btn>
                )}
              </div>
            ))}
          </div>
        ))}
        {groups.length === 0 && (
          <div className="mono dim" style={{ fontSize: 12, textAlign: "center", padding: 16 }}>
            Sin verificaciones.
          </div>
        )}
      </div>
    </Panel>
  );
}
