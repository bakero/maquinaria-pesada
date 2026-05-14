// PageOptimizar — extraído del monolito (Fase 1b).
import * as React from "react";
import { Btn, Icon, Kpi, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";
import { OPT_RECS } from "./fixtures";

function PageOptimizar({ onNav, onOpenAI }) {
  const totalSavings = OPT_RECS.reduce((s, r) => s + r.savings, 0);
  const sevColor = { critical: "var(--alert)", warning: "var(--warn)", info: "var(--info)" };
  const sevLabel = { critical: "CRÍTICA", warning: "AVISO", info: "INFO" };

  return (
    <div className="content">
      <PageHeader
        title="Optimizar consumo"
        sub="Heurísticas sobre ai_usage.jsonl · sin IA · solo reglas explicables"
        actions={
          <React.Fragment>
            <Btn sm kind="ghost" icon={<Icon name="refresh" size={11}/>}
                 onClick={() => window.location.reload()}>Re-analizar</Btn>
            <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Optimización · reglas", purpose: "improve" })}
                 icon={<Icon name="spark" size={11}/>}>Proponer más reglas</Btn>
          </React.Fragment>
        }
      />
      <SourcePills files={srcFor("optimizar")}/>

      <div className="kpi-grid mb-12">
        <Kpi label="Llamadas analizadas"  value="2.4k"          delta="últimos 30 días"/>
        <Kpi label="Gasto total"           value="142.18" unit="€"/>
        <Kpi label="Ahorro potencial"      value={totalSavings.toFixed(2)} unit="€" delta={`${Math.round((totalSavings / 142.18) * 100)}% del gasto`} deltaDir="up"/>
        <Kpi label="Recomendaciones"       value={OPT_RECS.length} delta={`${OPT_RECS.filter(r => r.severity === "critical").length} críticas`}/>
      </div>

      <div className="h2"><Icon name="brain" size={14}/> Recomendaciones</div>

      <div className="col gap-3">
        {OPT_RECS.map((r) => (
          <div key={r.id} className="panel" style={{
            padding: "14px 18px",
            borderLeft: `3px solid ${sevColor[r.severity]}`,
          }}>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 10 }}>
              <div className="row gap-4">
                <span className="badge" style={{
                  color: sevColor[r.severity],
                  borderColor: sevColor[r.severity],
                  background: r.severity === "critical" ? "rgba(204,34,0,0.08)"
                            : r.severity === "warning"  ? "rgba(232,114,17,0.08)"
                            : "rgba(77,184,255,0.08)",
                }}>{sevLabel[r.severity]}</span>
                <div className="display" style={{ fontSize: 14, letterSpacing: "0.04em" }}>{r.title}</div>
                <span className="mono dim" style={{ fontSize: 10 }}>regla: {r.id}</span>
              </div>
              <div className="col" style={{ alignItems: "flex-end", gap: 0 }}>
                <div className="display" style={{ fontSize: 9, color: "var(--text-mute)", letterSpacing: "0.16em" }}>AHORRO</div>
                <div className="mono" style={{ fontSize: 18, color: "var(--ok)" }}>{r.savings.toFixed(2)}€</div>
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
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · CONSUMO (Tokens + Economics)
// ════════════════════════════════════════════════════════════

export { PageOptimizar };
