// PageConsumo — tokens y saldos reales (Fase 2).
// Tokens/eventos: capa de datos del bootstrap (ai_usage.jsonl agregado).
// Saldos: /api/economics (cockpit/core/economics — economics.json + tracked).
import * as React from "react";
import { Btn, Icon, Panel, Kpi, Bar, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";
import { getAILog, getTokenData } from "../data";

function PageConsumo({ onNav, onOpenAI }) {
  const [tab, setTab] = React.useState("uso");
  const [eco, setEco] = React.useState(null);

  const loadEco = React.useCallback(() => {
    fetch("/api/economics", { cache: "no-store" })
      .then((r) => r.json())
      .then(setEco)
      .catch(() => setEco({ summary: {}, topups: [] }));
  }, []);
  React.useEffect(() => { loadEco(); }, [loadEco]);

  const td = getTokenData();
  const aiLog = getAILog();
  const summary = (eco && eco.summary) || {};
  const topups = (eco && eco.topups) || [];
  const providers = Object.keys(summary);
  const totalBalance = providers.reduce((s, p) => s + (summary[p].balance || 0), 0);
  const totalCalls = providers.reduce((s, p) => s + (summary[p].calls || 0), 0);
  const budget = td.budget || 250;

  const registrarRecarga = async () => {
    const provider = window.prompt("Proveedor (anthropic / openai / elevenlabs / kling):");
    if (!provider) return;
    const amount = parseFloat(window.prompt("Importe USD:") || "0");
    if (!amount || amount <= 0) return;
    const note = window.prompt("Nota (opcional):") || "";
    const res = await fetch("/api/economics/topup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider, amount, note }),
    });
    const data = await res.json();
    if (data.ok) loadEco();
    else window.alert("Error: " + (data.error || "desconocido"));
  };

  return (
    <div className="content">
      <PageHeader
        title="Consumo · tokens y saldos"
        sub="Agregado de ai_usage.jsonl + recargas por proveedor"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Consumo IA", purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Mejorar con IA</Btn>
        }
      />
      <SourcePills files={srcFor("consumo")}/>

      <div className="kpi-grid mb-12">
        <Kpi label="Tokens · 30d"   value={(td.total_30d / 1e6).toFixed(1)} unit="M"/>
        <Kpi label="Gasto · 30d"    value={(td.cost_30d || 0).toFixed(2)} unit="€"
             delta={`${Math.round(((td.cost_30d || 0) / budget) * 100)}% del budget (${budget}€)`}/>
        <Kpi label="Saldo global"   value={totalBalance.toFixed(2)} unit="€"
             delta={`${providers.length} proveedores`} deltaDir={totalBalance >= 0 ? "up" : "dn"}/>
        <Kpi label="Llamadas · 30d" value={totalCalls.toLocaleString("es-ES")}/>
      </div>

      <div className="tabs mb-12">
        {[
          { id: "uso",     icon: "coin",  label: "Uso por modelo" },
          { id: "saldo",   icon: "key",   label: "Saldos & recargas" },
          { id: "eventos", icon: "log",   label: "Últimos eventos" },
        ].map((t) => (
          <div key={t.id} className={`tab ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
            <Icon name={t.icon} size={11}/>{t.label}
          </div>
        ))}
      </div>

      {tab === "uso" && (
        <div className="grid gap-8" style={{ gridTemplateColumns: "1.5fr 1fr" }}>
          <Panel title={<span><Icon name="brain" size={12}/> &nbsp;Por modelo</span>} noPad>
            <table className="tbl">
              <thead>
                <tr>
                  <th>Modelo</th>
                  <th style={{ width: 100, textAlign: "right" }}>Tokens</th>
                  <th style={{ width: 90,  textAlign: "right" }}>Coste</th>
                  <th style={{ width: 200 }}>Cuota</th>
                </tr>
              </thead>
              <tbody>
                {(td.byModel || []).map((m) => (
                  <tr key={m.model}>
                    <td className="mono" style={{ fontSize: 12, color: "var(--y)" }}>{m.model}</td>
                    <td className="mono tabular" style={{ textAlign: "right", fontSize: 12 }}>{(m.tokens / 1e6).toFixed(2)}M</td>
                    <td className="mono tabular" style={{ textAlign: "right", fontSize: 13 }}>{m.cost.toFixed(2)}€</td>
                    <td>
                      <div className="row gap-3">
                        <div style={{ flex: 1 }}><Bar pct={m.share} status="ok"/></div>
                        <span className="mono" style={{ fontSize: 10, minWidth: 28, textAlign: "right" }}>{m.share}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
                {(td.byModel || []).length === 0 && (
                  <tr><td colSpan={4} className="mono dim" style={{ textAlign: "center", padding: 16 }}>
                    Sin eventos en ai_usage.jsonl
                  </td></tr>
                )}
              </tbody>
            </table>
          </Panel>

          <Panel title={<span><Icon name="grid" size={12}/> &nbsp;Por tipo</span>}>
            <div className="col gap-4">
              {(td.byKind || []).map((k) => (
                <div key={k.kind}>
                  <div className="row" style={{ justifyContent: "space-between", marginBottom: 4 }}>
                    <span className="display" style={{ fontSize: 11, letterSpacing: "0.06em", color: "var(--text-dim)" }}>{k.kind}</span>
                    <span className="mono" style={{ fontSize: 11, color: "var(--y)" }}>{k.pct}%</span>
                  </div>
                  <Bar pct={k.pct}/>
                </div>
              ))}
              {(td.byKind || []).length === 0 && (
                <div className="mono dim" style={{ fontSize: 11 }}>Sin datos</div>
              )}
            </div>
          </Panel>
        </div>
      )}

      {tab === "saldo" && (
        <div className="grid gap-8" style={{ gridTemplateColumns: "1.2fr 1fr" }}>
          <Panel title={<span><Icon name="coin" size={12}/> &nbsp;Saldos por proveedor</span>} noPad>
            <table className="tbl">
              <thead>
                <tr>
                  <th>Proveedor</th>
                  <th style={{ width: 100, textAlign: "right" }}>Recargado</th>
                  <th style={{ width: 100, textAlign: "right" }}>Gastado</th>
                  <th style={{ width: 100, textAlign: "right" }}>Saldo</th>
                  <th style={{ width: 80,  textAlign: "right" }}>Llamadas</th>
                </tr>
              </thead>
              <tbody>
                {providers.map((id) => {
                  const p = summary[id];
                  const low = p.balance < 20;
                  return (
                    <tr key={id}>
                      <td className="display" style={{ fontSize: 12 }}>{id}</td>
                      <td className="mono tabular" style={{ textAlign: "right" }}>{(p.topped_up || 0).toFixed(2)}€</td>
                      <td className="mono tabular" style={{ textAlign: "right", color: "var(--text-dim)" }}>{(p.spent || 0).toFixed(2)}€</td>
                      <td className="mono tabular" style={{ textAlign: "right", color: low ? "var(--warn)" : "var(--ok)", fontSize: 14 }}>
                        {(p.balance || 0).toFixed(2)}€
                      </td>
                      <td className="mono tabular dim" style={{ textAlign: "right" }}>{p.calls || 0}</td>
                    </tr>
                  );
                })}
                {providers.length === 0 && (
                  <tr><td colSpan={5} className="mono dim" style={{ textAlign: "center", padding: 16 }}>
                    Sin movimientos — registra una recarga para empezar.
                  </td></tr>
                )}
              </tbody>
            </table>
          </Panel>

          <Panel title={<span><Icon name="key" size={12}/> &nbsp;Histórico recargas</span>} meta={`${topups.length} en total`} noPad>
            <div className="col gap-2" style={{ padding: 12, maxHeight: 320, overflow: "auto" }}>
              {topups.map((t, i) => (
                <div key={i} className="row" style={{
                  padding: "6px 10px", border: "1px solid var(--border)", background: "var(--panel-2)",
                  fontFamily: "var(--f-mono)", fontSize: 11,
                }}>
                  <span style={{ color: "var(--text-mute)", width: 150 }}>{t.timestamp || "—"}</span>
                  <span style={{ flex: 1, color: "var(--y)" }}>{t.provider}</span>
                  <span style={{ color: "var(--ok)" }}>+{(t.amount_usd || 0).toFixed(2)}€</span>
                </div>
              ))}
              {topups.length === 0 && (
                <div className="mono dim" style={{ fontSize: 11, textAlign: "center", padding: 8 }}>
                  Sin recargas registradas.
                </div>
              )}
            </div>
            <div style={{ padding: 12, borderTop: "1px solid var(--border)", background: "var(--panel-2)" }}>
              <Btn sm kind="primary" icon={<Icon name="key" size={10}/>} onClick={registrarRecarga}>
                Registrar recarga
              </Btn>
            </div>
          </Panel>
        </div>
      )}

      {tab === "eventos" && (
        <Panel title={<span><Icon name="log" size={12}/> &nbsp;Últimos eventos</span>} meta="ai_usage.jsonl" noPad>
          <table className="tbl">
            <thead>
              <tr>
                <th style={{ width: 90 }}>T</th>
                <th>Modelo</th>
                <th>Tipo</th>
                <th style={{ width: 100, textAlign: "right" }}>Tokens</th>
                <th style={{ width: 90,  textAlign: "right" }}>Coste</th>
              </tr>
            </thead>
            <tbody>
              {aiLog.map((e, i) => (
                <tr key={i}>
                  <td className="mono dim" style={{ fontSize: 11 }}>{e.t}</td>
                  <td className="mono" style={{ color: "var(--y)" }}>{e.model}</td>
                  <td>{e.kind}</td>
                  <td className="mono tabular" style={{ textAlign: "right" }}>{(e.tok || 0).toLocaleString()}</td>
                  <td className="mono tabular" style={{ textAlign: "right", color: "var(--ok)" }}>{(e.cost || 0).toFixed(3)}€</td>
                </tr>
              ))}
              {aiLog.length === 0 && (
                <tr><td colSpan={5} className="mono dim" style={{ textAlign: "center", padding: 16 }}>
                  Sin eventos registrados.
                </td></tr>
              )}
            </tbody>
          </table>
        </Panel>
      )}
    </div>
  );
}

export { PageConsumo };
