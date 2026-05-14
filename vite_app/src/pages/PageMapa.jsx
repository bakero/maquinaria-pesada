// PageMapa — grafo de componentes real (Fase 2).
// Datos de /api/components-map (cockpit/components_map.json vía core).
// El layout (x/y) se calcula aquí: columna por `kind`, fila por orden.
import * as React from "react";
import { Btn, Icon, Panel, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";

const KIND_COL = { generator: 60, system: 320, generated: 600 };
const ROW_STEP = 120;
const ROW_TOP = 40;

// Asigna x/y a cada nodo: columna por kind, fila por índice dentro del kind.
function layout(nodes) {
  const seen = { generator: 0, system: 0, generated: 0 };
  return nodes.map((n) => {
    const col = KIND_COL[n.kind] ?? 320;
    const row = seen[n.kind] ?? 0;
    if (n.kind in seen) seen[n.kind] += 1;
    return { ...n, x: col, y: ROW_TOP + row * ROW_STEP };
  });
}

function PageMapa({ onNav, onOpenAI }) {
  const [hover, setHover] = React.useState(null);
  const [view, setView]   = React.useState("grafo"); // grafo | tabla
  const [data, setData]   = React.useState(null);
  const [loading, setLoading] = React.useState(true);

  const load = React.useCallback(() => {
    setLoading(true);
    fetch("/api/components-map", { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false); })
      .catch((e) => { setData({ ok: false, error: String(e), nodes: [], edges: [] }); setLoading(false); });
  }, []);

  React.useEffect(() => { load(); }, [load]);

  const KIND_COLOR = { generator: "var(--info)", system: "var(--y)", generated: "var(--ok)" };
  const KIND_LABEL = { generator: "GENERATOR · IA", system: "SYSTEM · pipeline", generated: "GENERATED · output" };

  const rawNodes = (data && data.nodes) || [];
  const edges = (data && data.edges) || [];
  const nodes = layout(rawNodes);
  const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
  const CW = 760;
  const maxRows = Math.max(
    1,
    ...["generator", "system", "generated"].map(
      (k) => rawNodes.filter((n) => n.kind === k).length,
    ),
  );
  const CH = Math.max(600, ROW_TOP + maxRows * ROW_STEP + 20);

  return (
    <div className="content">
      <PageHeader
        title="Mapa de componentes"
        sub="Grafo del cockpit · 3 tipos de nodo · cockpit/components_map.json"
        actions={
          <React.Fragment>
            <Btn sm kind="ghost" icon={<Icon name="refresh" size={11}/>}
                 onClick={load}>{loading ? "Cargando…" : "Reescanear"}</Btn>
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
          {nodes.length} nodos · {edges.length} aristas
        </div>
      </div>

      {loading ? (
        <div className="mono dim" style={{ fontSize: 12, padding: "40px 0", textAlign: "center" }}>
          Cargando grafo…
        </div>
      ) : data && !data.ok ? (
        <div className="mono" style={{ fontSize: 12, padding: "40px 0", textAlign: "center", color: "var(--alert)" }}>
          No se pudo cargar el mapa: {data.error || "error"}
        </div>
      ) : view === "grafo" ? (
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
              {edges.map((e, i) => {
                const na = byId[e.src];
                const nb = byId[e.dst];
                if (!na || !nb) return null;
                const x1 = na.x + 140, y1 = na.y + 26;
                const x2 = nb.x - 4,  y2 = nb.y + 26;
                const sel = hover && (e.src === hover || e.dst === hover);
                return (
                  <line key={i} x1={x1} y1={y1} x2={x2} y2={y2}
                        stroke="var(--y)" strokeOpacity={sel ? 0.95 : 0.35}
                        strokeWidth={sel ? 2 : 1.2} markerEnd="url(#mp-arr)"/>
                );
              })}
            </svg>

            {nodes.map((n) => (
              <div key={n.id}
                   onMouseEnter={() => setHover(n.id)}
                   onMouseLeave={() => setHover(null)}
                   title={n.description || ""}
                   style={{
                     position: "absolute", left: n.x, top: n.y,
                     width: 140, padding: "8px 10px",
                     background: "var(--panel-2)",
                     border: "1px solid var(--border-2)",
                     borderLeft: `3px solid ${KIND_COLOR[n.kind] || "var(--border-2)"}`,
                     boxShadow: hover === n.id ? `0 0 0 1px ${KIND_COLOR[n.kind]}` : "none",
                     cursor: "pointer",
                   }}>
                <div className="mono" style={{
                  fontSize: 8, letterSpacing: "0.16em",
                  color: KIND_COLOR[n.kind] || "var(--text-mute)", marginBottom: 2,
                }}>{(n.kind || "?").toUpperCase()}</div>
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
              {nodes.map((n) => {
                const ins = edges.filter((e) => e.dst === n.id).length;
                const outs = edges.filter((e) => e.src === n.id).length;
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

export { PageMapa };
