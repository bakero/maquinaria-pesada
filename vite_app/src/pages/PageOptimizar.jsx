// PageOptimizar — recomendaciones de ahorro reales (Fase 2).
// Datos de /api/optimization: heurísticas de cockpit/core/optimization_advisor
// sobre los eventos reales de logs/ai_usage.jsonl.
import * as React from "react";
import { Btn, Icon, Kpi, PageHeader, SourcePills } from "../components";
import { getTokenData } from "../data";
import { srcFor } from "../lib/nav";

function PageOptimizar({ onNav, onOpenAI }) {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);

  const load = React.useCallback(() => {
    setLoading(true);
    fetch("/api/optimization", { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false); })
      .catch((e) => { setData({ ok: false, error: String(e), recommendations: [] }); setLoading(false); });
  }, []);

  React.useEffect(() => { load(); }, [load]);

  const sevColor = { critical: "var(--alert)", warning: "var(--warn)", info: "var(--info)" };
  const sevLabel = { critical: "CRÍTICA", warning: "AVISO", info: "INFO" };

  const recs = (data && data.recommendations) || [];
  const totalSavings = data ? (data.total_savings_usd || 0) : 0;
  const gastoTotal = getTokenData().cost_30d || 0;
  const analizadas = data ? (data.events_analyzed || 0) : 0;

  return (
    <div className="content">
      <PageHeader
        title="Optimizar consumo"
        sub="Heurísticas sobre ai_usage.jsonl · sin IA · solo reglas explicables"
        actions={
          <React.Fragment>
            <Btn sm kind="ghost" icon={<Icon name="refresh" size={11}/>}
                 onClick={load}>{loading ? "Analizando…" : "Re-analizar"}</Btn>
            <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Optimización · reglas", purpose: "improve" })}
                 icon={<Icon name="spark" size={11}/>}>Proponer más reglas</Btn>
          </React.Fragment>
        }
      />
      <SourcePills files={srcFor("optimizar")}/>

      <div className="kpi-grid mb-12">
        <Kpi label="Llamadas analizadas"  value={analizadas} delta="logs/ai_usage.jsonl"/>
        <Kpi label="Gasto total"           value={gastoTotal.toFixed(2)} unit="€"/>
        <Kpi label="Ahorro potencial"      value={totalSavings.toFixed(2)} unit="€"
             delta={gastoTotal ? `${Math.round((totalSavings / gastoTotal) * 100)}% del gasto` : ""} deltaDir="up"/>
        <Kpi label="Recomendaciones"       value={recs.length}
             delta={`${recs.filter(r => r.severity === "critical").length} críticas`}/>
      </div>

      <div className="h2"><Icon name="brain" size={14}/> Recomendaciones</div>

      {loading ? (
        <div className="mono dim" style={{ fontSize: 12, padding: "24px 0", textAlign: "center" }}>
          Analizando eventos…
        </div>
      ) : data && !data.ok ? (
        <div className="mono" style={{ fontSize: 12, padding: "24px 0", textAlign: "center", color: "var(--alert)" }}>
          No se pudieron cargar las recomendaciones: {data.error || "error"}
        </div>
      ) : recs.length === 0 ? (
        <div className="mono dim" style={{ fontSize: 12, padding: "24px 0", textAlign: "center" }}>
          Sin recomendaciones — no hay eventos suficientes en ai_usage.jsonl o el consumo ya está optimizado.
        </div>
      ) : (
        <div className="col gap-3">
          {recs.map((r) => (
            <div key={r.rule_id} className="panel" style={{
              padding: "14px 18px",
              borderLeft: `3px solid ${sevColor[r.severity] || "var(--border-2)"}`,
            }}>
              <div className="row" style={{ justifyContent: "space-between", marginBottom: 10 }}>
                <div className="row gap-4">
                  <span className="badge" style={{
                    color: sevColor[r.severity],
                    borderColor: sevColor[r.severity],
                    background: r.severity === "critical" ? "rgba(204,34,0,0.08)"
                              : r.severity === "warning"  ? "rgba(232,114,17,0.08)"
                              : "rgba(77,184,255,0.08)",
                  }}>{sevLabel[r.severity] || r.severity}</span>
                  <div className="display" style={{ fontSize: 14, letterSpacing: "0.04em" }}>{r.title}</div>
                  <span className="mono dim" style={{ fontSize: 10 }}>regla: {r.rule_id}</span>
                </div>
                <div className="col" style={{ alignItems: "flex-end", gap: 0 }}>
                  <div className="display" style={{ fontSize: 9, color: "var(--text-mute)", letterSpacing: "0.16em" }}>AHORRO</div>
                  <div className="mono" style={{ fontSize: 18, color: "var(--ok)" }}>{(r.savings || 0).toFixed(2)}€</div>
                </div>
              </div>
              <div className="grid gap-8" style={{ gridTemplateColumns: "1fr 1fr" }}>
                <div>
                  <div className="display mb-4" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.14em" }}>EVIDENCIA</div>
                  <div className="mono" style={{ fontSize: 12, color: "var(--text-dim)", lineHeight: 1.5 }}>{r.evidence}</div>
                </div>
                <div>
                  <div className="display mb-4" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.14em" }}>ACCIÓN</div>
                  <div className="mono" style={{ fontSize: 12, color: "var(--y)", lineHeight: 1.5 }}>{r.action}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export { PageOptimizar };
