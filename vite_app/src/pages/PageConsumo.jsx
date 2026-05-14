// PageConsumo — extraído del monolito (Fase 1b).
import * as React from "react";
import { Btn, Icon, Panel, Kpi, Bar, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";
import { FIXTURE_TOKEN_DATA as TOKEN_DATA, FIXTURE_AI_LOG as AI_LOG } from "../data";
import { PROVIDER_BALANCE, TOPUPS } from "./fixtures";

function PageConsumo({ onNav, onOpenAI }) {
  const [tab, setTab] = React.useState("uso");
  const totalBalance = PROVIDER_BALANCE.reduce((s, p) => s + (p.topped - p.spent), 0);

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
        <Kpi label="Tokens · 30d"   value="18.4" unit="M" delta="−12% vs mes anterior" deltaDir="dn"/>
        <Kpi label="Gasto · 30d"    value="142.18" unit="€" delta="57% del budget (250€)"/>
        <Kpi label="Saldo global"   value={totalBalance.toFixed(2)} unit="€" delta={`${PROVIDER_BALANCE.length} proveedores`} deltaDir="up"/>
        <Kpi label="Llamadas · 30d" value="2 402" delta="ø 53/día"/>
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
                {TOKEN_DATA.byModel.map((m) => (
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
              </tbody>
            </table>
          </Panel>

          <Panel title={<span><Icon name="grid" size={12}/> &nbsp;Por tipo</span>}>
            <div className="col gap-4">
              {TOKEN_DATA.byKind.map((k) => (
                <div key={k.kind}>
                  <div className="row" style={{ justifyContent: "space-between", marginBottom: 4 }}>
                    <span className="display" style={{ fontSize: 11, letterSpacing: "0.06em", color: "var(--text-dim)" }}>{k.kind}</span>
                    <span className="mono" style={{ fontSize: 11, color: "var(--y)" }}>{k.pct}%</span>
                  </div>
                  <Bar pct={k.pct}/>
                </div>
              ))}
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
                {PROVIDER_BALANCE.map((p) => {
                  const bal = p.topped - p.spent;
                  const low = bal < 20;
                  return (
                    <tr key={p.id}>
                      <td className="display" style={{ fontSize: 12 }}>{p.id}</td>
                      <td className="mono tabular" style={{ textAlign: "right" }}>{p.topped.toFixed(2)}€</td>
                      <td className="mono tabular" style={{ textAlign: "right", color: "var(--text-dim)" }}>{p.spent.toFixed(2)}€</td>
                      <td className="mono tabular" style={{ textAlign: "right", color: low ? "var(--warn)" : "var(--ok)", fontSize: 14 }}>
                        {bal.toFixed(2)}€
                      </td>
                      <td className="mono tabular dim" style={{ textAlign: "right" }}>{p.calls}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Panel>

          <Panel title={<span><Icon name="key" size={12}/> &nbsp;Histórico recargas</span>} meta={`${TOPUPS.length} en total`} noPad>
            <div className="col gap-2" style={{ padding: 12, maxHeight: 320, overflow: "auto" }}>
              {TOPUPS.map((t, i) => (
                <div key={i} className="row" style={{
                  padding: "6px 10px", border: "1px solid var(--border)", background: "var(--panel-2)",
                  fontFamily: "var(--f-mono)", fontSize: 11,
                }}>
                  <span style={{ color: "var(--text-mute)", width: 110 }}>{t.t}</span>
                  <span style={{ flex: 1, color: "var(--y)" }}>{t.provider}</span>
                  <span style={{ color: "var(--ok)" }}>+{t.amount.toFixed(2)}€</span>
                </div>
              ))}
            </div>
            <div style={{ padding: 12, borderTop: "1px solid var(--border)", background: "var(--panel-2)" }}>
              <Btn sm kind="primary" icon={<Icon name="key" size={10}/>}
                   onClick={async () => {
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
                     if (data.ok) window.location.reload();
                     else window.alert("Error: " + (data.error || "desconocido"));
                   }}>
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
              {AI_LOG.map((e, i) => (
                <tr key={i}>
                  <td className="mono dim" style={{ fontSize: 11 }}>{e.t}</td>
                  <td className="mono" style={{ color: "var(--y)" }}>{e.model}</td>
                  <td>{e.kind}</td>
                  <td className="mono tabular" style={{ textAlign: "right" }}>{e.tok.toLocaleString()}</td>
                  <td className="mono tabular" style={{ textAlign: "right", color: "var(--ok)" }}>{e.cost.toFixed(3)}€</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · AJUSTES (API Keys + sandbox)
// ════════════════════════════════════════════════════════════

export { PageConsumo };
