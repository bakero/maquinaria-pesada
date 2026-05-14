// PageLogs — extraído del monolito (Fase 1b).
import * as React from "react";
import { Btn, Icon, Panel, Kpi, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";
import { SOURCE_ITEMS, LOG_LINES } from "./fixtures";

function PageLogs({ onNav, onOpenAI }) {
  const logs = SOURCE_ITEMS.logs;
  const [sel, setSel] = React.useState(logs[0].name);
  const [auto, setAuto] = React.useState(false);
  const [lines, setLines] = React.useState(LOG_LINES);
  const [filter, setFilter] = React.useState("");

  // Auto-refresh: append random line every 5s
  React.useEffect(() => {
    if (!auto) return;
    const id = setInterval(() => {
      const t = new Date().toLocaleTimeString("es-ES", { hour12: false });
      const samples = [
        `{"t":"${t}","lvl":"INFO","src":"runner","msg":"heartbeat","cpu":12,"mem":42}`,
        `{"t":"${t}","lvl":"INFO","src":"claude","msg":"token","model":"haiku-4.5","tokens":${Math.floor(Math.random()*200)+20}}`,
        `{"t":"${t}","lvl":"WARN","src":"eleven","msg":"latency high","ms":${Math.floor(Math.random()*800)+200}}`,
      ];
      setLines((l) => [...l, samples[Math.floor(Math.random() * samples.length)]]);
    }, 1500);
    return () => clearInterval(id);
  }, [auto]);

  const filtered = filter
    ? lines.filter(l => l.toLowerCase().includes(filter.toLowerCase()))
    : lines;

  const counts = lines.reduce((acc, l) => {
    if (l.includes('"ERROR"')) acc.err++;
    else if (l.includes('"WARN"')) acc.warn++;
    else acc.info++;
    return acc;
  }, { info: 0, warn: 0, err: 0 });

  return (
    <div className="content">
      <PageHeader
        title="Logs de producción"
        sub="JSONL en logs/ · auto-refresh opcional · diagnóstico IA sobre las últimas líneas"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({
            target: `Log · ${sel}`,
            purpose: "improve",
          })} icon={<Icon name="spark" size={11}/>}>Diagnóstico con IA</Btn>
        }
      />
      <SourcePills files={srcFor("logs")}/>

      <div className="kpi-grid mb-12">
        <Kpi label="Líneas"     value={lines.length} delta={`auto-refresh ${auto ? "ON" : "OFF"}`} deltaDir={auto ? "up" : ""}/>
        <Kpi label="INFO"       value={counts.info}/>
        <Kpi label="WARN"       value={counts.warn} delta={counts.warn ? "atención" : "ok"}/>
        <Kpi label="ERROR"      value={counts.err}  delta={counts.err ? "investigar" : "limpio"} deltaDir={counts.err ? "dn" : "up"}/>
      </div>

      <div className="grid gap-8" style={{ gridTemplateColumns: "280px 1fr" }}>
        <Panel title={<span><Icon name="folder" size={12}/> &nbsp;Archivos</span>} noPad>
          <div className="col gap-2" style={{ padding: 10 }}>
            {logs.map((l) => (
              <div key={l.name}
                   onClick={() => setSel(l.name)}
                   style={{
                     padding: "8px 10px",
                     border: "1px solid",
                     borderColor: sel === l.name ? "var(--y)" : "var(--border)",
                     background: sel === l.name ? "var(--y-soft)" : "var(--panel-2)",
                     cursor: "pointer",
                   }}>
                <div className="mono" style={{ fontSize: 11, color: sel === l.name ? "var(--y)" : "var(--text)", wordBreak: "break-all" }}>
                  {l.name}
                </div>
                <div className="mono dim" style={{ fontSize: 10, marginTop: 2 }}>{l.size} · {l.t}</div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel
          title={<span><Icon name="log" size={12}/> &nbsp;{sel}</span>}
          meta={auto ? "live · 1.5s" : "snapshot"}
          actions={
            <React.Fragment>
              <input className="ai-input" placeholder="Filtrar…" value={filter}
                     onChange={(e) => setFilter(e.target.value)} style={{ width: 140, fontSize: 11 }}/>
              <button className={`btn sm ${auto ? "primary" : "ghost"}`} onClick={() => setAuto(!auto)}>
                <Icon name="refresh" size={10}/> Auto
              </button>
            </React.Fragment>
          }
        >
          <pre className="code" style={{
            maxHeight: 480, overflow: "auto", fontSize: 11.5,
            borderLeftColor: auto ? "var(--info)" : "var(--y)",
          }}>
            {filtered.map((l, i) => {
              const isErr = l.includes('"ERROR"');
              const isWarn = l.includes('"WARN"');
              const color = isErr ? "var(--alert)" : isWarn ? "var(--warn)" : "var(--text-dim)";
              return (
                <div key={i} style={{ color, whiteSpace: "pre-wrap" }}>{l}</div>
              );
            })}
            {auto && <span className="ai-cursor"/>}
          </pre>
        </Panel>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · OPTIMIZAR
// ════════════════════════════════════════════════════════════

export { PageLogs };
