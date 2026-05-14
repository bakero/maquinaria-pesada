// PageMapa — extraído del monolito (Fase 1b).
import * as React from "react";
import { Btn, Icon, Panel, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";
import { MAP_NODES, MAP_EDGES } from "./fixtures";

function PageMapa({ onNav, onOpenAI }) {
  const [hover, setHover] = React.useState(null);
  const [view, setView]   = React.useState("grafo"); // grafo | tabla

  const KIND_COLOR = { generator: "var(--info)", system: "var(--y)", generated: "var(--ok)" };
  const KIND_LABEL = { generator: "GENERATOR · IA", system: "SYSTEM · pipeline", generated: "GENERATED · output" };

  const CW = 760, CH = 600;

  return (
    <div className="content">
      <PageHeader
        title="Mapa de componentes"
        sub="Grafo del cockpit · 3 tipos de nodo · persistido en components_map.json"
        actions={
          <React.Fragment>
            <Btn sm kind="ghost" icon={<Icon name="refresh" size={11}/>}
                 onClick={() => window.location.reload()}>Reescanear</Btn>
            <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Mapa de componentes", purpose: "improve" })}
                 icon={<Icon name="spark" size={11}/>}>Mejorar con IA</Btn>
          </React.Fragment>
        }
      />
      <SourcePills files={srcFor("mapa")}/>

      <div className="row mb-8" style={{ justifyContent: "space-between" }}>
        <div className="row gap-3">
          {["grafo", "tabla"].map((v) => (
            <div key={v} className={`btn sm ${view === v ? "primary" : ""}`}
                 onClick={() => setView(v)} style={{ cursor: "pointer" }}>
              {v.toUpperCase()}
            </div>
          ))}
        </div>
        <div className="mono dim" style={{ fontSize: 11, letterSpacing: "0.08em" }}>
          {MAP_NODES.length} nodos · {MAP_EDGES.length} aristas
        </div>
      </div>

      {view === "grafo" ? (
        <Panel
          title={<span><Icon name="map" size={12}/> &nbsp;Grafo de componentes</span>}
          meta="cockpit/components_map.json"
          noPad
        >
          <div style={{
            background: "#0A0A0A",
            backgroundImage:
              "linear-gradient(rgba(245,196,0,0.04) 1px, transparent 1px)," +
              "linear-gradient(90deg, rgba(245,196,0,0.04) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
            position: "relative",
            height: CH,
            overflow: "hidden",
          }}>
            {/* Column labels */}
            {[
              { x: 60,  label: "GENERATORS" },
              { x: 320, label: "SYSTEMS" },
              { x: 600, label: "GENERATED" },
            ].map((c) => (
              <div key={c.label} style={{
                position: "absolute", left: c.x, top: 10,
                fontFamily: "var(--f-display)", fontSize: 10, color: "var(--y)",
                letterSpacing: "0.2em", opacity: 0.7,
              }}>{c.label}</div>
            ))}

            <svg viewBox={`0 0 ${CW} ${CH}`} preserveAspectRatio="none"
                 style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }}>
              <defs>
                <marker id="mp-arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto">
                  <path d="M0 0 L10 5 L0 10 z" fill="var(--y)"/>
                </marker>
              </defs>
              {MAP_EDGES.map(([a, b], i) => {
                const na = MAP_NODES.find(n => n.id === a);
                const nb = MAP_NODES.find(n => n.id === b);
                if (!na || !nb) return null;
                const x1 = na.x + 140, y1 = na.y + 26;
                const x2 = nb.x - 4,  y2 = nb.y + 26;
                const sel = hover && (a === hover || b === hover);
                return (
                  <line key={i} x1={x1} y1={y1} x2={x2} y2={y2}
                        stroke="var(--y)" strokeOpacity={sel ? 0.95 : 0.35}
                        strokeWidth={sel ? 2 : 1.2} markerEnd="url(#mp-arr)"/>
                );
              })}
            </svg>

            {MAP_NODES.map((n) => (
              <div key={n.id}
                   onMouseEnter={() => setHover(n.id)}
                   onMouseLeave={() => setHover(null)}
                   style={{
                     position: "absolute", left: n.x, top: n.y,
                     width: 140, padding: "8px 10px",
                     background: "var(--panel-2)",
                     border: "1px solid var(--border-2)",
                     borderLeft: `3px solid ${KIND_COLOR[n.kind]}`,
                     boxShadow: hover === n.id ? `0 0 0 1px ${KIND_COLOR[n.kind]}` : "none",
                     cursor: "pointer",
                   }}>
                <div className="mono" style={{
                  fontSize: 8, letterSpacing: "0.16em",
                  color: KIND_COLOR[n.kind], marginBottom: 2,
                }}>{n.kind.toUpperCase()}</div>
                <div className="display" style={{
                  fontSize: 11, letterSpacing: "0.04em",
                  color: "var(--text)", lineHeight: 1.2,
                }}>{n.label}</div>
              </div>
            ))}

            <div style={{
              position: "absolute", left: 12, bottom: 12,
              background: "rgba(0,0,0,0.7)",
              border: "1px solid var(--border)",
              padding: "8px 12px",
              fontFamily: "var(--f-mono)",
              fontSize: 10,
              color: "var(--text-dim)",
              display: "flex", flexDirection: "column", gap: 4,
              letterSpacing: "0.08em",
            }}>
              {["generator","system","generated"].map((k) => (
                <div key={k} className="row gap-3">
                  <span style={{ width: 12, height: 12, background: "var(--panel-2)", borderLeft: `3px solid ${KIND_COLOR[k]}` }}/>
                  {KIND_LABEL[k]}
                </div>
              ))}
            </div>
          </div>
        </Panel>
      ) : (
        <Panel noPad>
          <table className="tbl">
            <thead>
              <tr>
                <th style={{ width: 200 }}>ID</th>
                <th>Label</th>
                <th style={{ width: 140 }}>Tipo</th>
                <th style={{ width: 70, textAlign: "right" }}>Aristas</th>
              </tr>
            </thead>
            <tbody>
              {MAP_NODES.map((n) => {
                const ins = MAP_EDGES.filter(([_, b]) => b === n.id).length;
                const outs = MAP_EDGES.filter(([a, _]) => a === n.id).length;
                return (
                  <tr key={n.id}>
                    <td><span className="mono" style={{ fontSize: 11, color: "var(--y)" }}>{n.id}</span></td>
                    <td className="display" style={{ fontSize: 13 }}>{n.label}</td>
                    <td>
                      <span className="badge" style={{ color: KIND_COLOR[n.kind], borderColor: KIND_COLOR[n.kind] }}>
                        {n.kind}
                      </span>
                    </td>
                    <td className="mono dim" style={{ textAlign: "right", fontSize: 11 }}>{ins} ← · {outs} →</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Panel>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · CONECTORES
// ════════════════════════════════════════════════════════════

export { PageMapa };
