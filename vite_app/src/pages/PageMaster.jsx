// PageMaster — extraído del monolito (Fase 1b).
import * as React from "react";
import { Btn, Icon, Panel, StatusDot, Bar, KindCell, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";
import { SOURCES, KINDS } from "../lib/sources";
import { FIXTURE_MODULES as MODULES, FIXTURE_EPISODES as EPISODES } from "../data";

function PageMaster({ onNav, onOpenAI, view, density }) {
  return (
    <div className="content">
      <PageHeader
        title="Master M0 — M14"
        sub="Vista global de los 15 módulos · 22 episodios"
        actions={null}
      />
      <SourcePills files={srcFor("master")}/>

      {/* View switcher */}
      <div className="row mb-8" style={{ justifyContent: "space-between" }}>
        <div className="row gap-3">
          {["lista", "matriz", "gantt"].map((v) => (
            <div
              key={v}
              className={`btn sm ${view === v ? "primary" : ""}`}
              onClick={() => window.__setMasterView && window.__setMasterView(v)}
              style={{ cursor: "pointer" }}
            >
              {v.toUpperCase()}
            </div>
          ))}
        </div>
        <div className="row gap-3">
          <Btn sm kind="ghost" icon={<Icon name="refresh" size={10}/>}
               onClick={() => window.location.reload()}>Re-scan</Btn>
          <Btn sm onClick={() => onOpenAI({ target: "Master · M0–M14", purpose: "improve" })}
               icon={<Icon name="spark" size={10}/>}>Mejorar con IA</Btn>
        </div>
      </div>

      {view === "lista" && <MasterListView onNav={onNav} density={density}/>}
      {view === "matriz"&& <MasterMatrixView onNav={onNav}/>}
      {view === "gantt" && <MasterGanttView onNav={onNav}/>}
    </div>
  );
}

// ── Master · Lista ───────────────────────────────────────
function MasterListView({ onNav, density }) {
  const rowH = density === "compact" ? 36 : density === "comfy" ? 56 : 44;
  return (
    <Panel noPad>
      <table className="tbl">
        <thead>
          <tr>
            <th style={{ width: 60 }}>ID</th>
            <th>Módulo</th>
            <th style={{ width: 100 }}>Eps.</th>
            <th style={{ width: 180 }}>Progreso</th>
            <th style={{ width: 180 }}>Estado</th>
            <th style={{ width: 70, textAlign: "right" }}></th>
          </tr>
        </thead>
        <tbody>
          {MODULES.map((m) => {
            const eps = EPISODES.filter(e => e.mod === m.id);
            return (
              <tr key={m.id} className="clickable" onClick={() => onNav("modulo", m.id)} style={{ height: rowH }}>
                <td>
                  <span className="mono" style={{ color: "var(--y)", fontSize: 13, fontWeight: 500 }}>{m.id}</span>
                </td>
                <td>
                  <div className="display" style={{ fontSize: 14, fontWeight: 500, letterSpacing: "0.04em" }}>{m.name}</div>
                  <div className="dim mono" style={{ fontSize: 10, marginTop: 2 }}>{m.short}</div>
                </td>
                <td>
                  <div className="row gap-3">
                    <span className="badge">M</span>
                    {eps.filter(e => e.kind === "T").length > 0 && (
                      <span className="badge">T×{eps.filter(e => e.kind === "T").length}</span>
                    )}
                  </div>
                </td>
                <td>
                  <div className="row gap-4">
                    <div style={{ flex: 1 }}><Bar pct={m.pct} status={m.status}/></div>
                    <span className="mono tabular" style={{ fontSize: 11, minWidth: 32, textAlign: "right" }}>{m.pct}%</span>
                  </div>
                </td>
                <td>
                  <div className="row gap-3">
                    <StatusDot status={m.status === "empty" ? "empty" : m.status}/>
                    <span className="display" style={{ fontSize: 11, letterSpacing: "0.12em" }}>
                      {m.status === "ok"    ? "Completo" :
                       m.status === "warn"  ? "En curso" :
                       m.status === "alert" ? "Bloqueado" : "Pendiente"}
                    </span>
                  </div>
                </td>
                <td style={{ textAlign: "right" }}>
                  <Icon name="arrow" size={12}/>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </Panel>
  );
}

// ── Master · Matriz (módulo × tipo de contenido) ─────────
function MasterMatrixView({ onNav }) {
  return (
    <Panel noPad>
      <div style={{ overflowX: "auto" }}>
        <table className="tbl">
          <thead>
            <tr>
              <th style={{ width: 60 }}>ID</th>
              <th>Módulo</th>
              <th style={{ width: 50 }}>Eps</th>
              {KINDS.map((k) => (
                <th key={k} style={{ width: 72, textAlign: "center", padding: "8px 6px" }}>
                  <div style={{ fontSize: 10 }}>{k.toUpperCase()}</div>
                  <div className="mono" style={{
                    fontSize: 9, fontWeight: 400, color: "var(--y)",
                    letterSpacing: 0, textTransform: "none", marginTop: 2,
                  }}>
                    {SOURCES[k].folder}
                  </div>
                </th>
              ))}
              <th style={{ width: 90 }}>%</th>
            </tr>
          </thead>
          <tbody>
            {MODULES.map((m) => {
              const eps = EPISODES.filter(e => e.mod === m.id);
              // Aggregate worst status per kind across episodes
              const agg = (k) => {
                const s = eps.map(e => e.state[k]);
                if (s.includes("alert")) return "alert";
                if (s.includes("run"))   return "run";
                if (s.includes("warn"))  return "warn";
                if (s.every(x => x === "ok")) return "ok";
                if (s.every(x => x === "empty")) return "empty";
                return "warn";
              };
              return (
                <tr key={m.id} className="clickable" onClick={() => onNav("modulo", m.id)}>
                  <td><span className="mono" style={{ color: "var(--y)" }}>{m.id}</span></td>
                  <td className="display" style={{ fontSize: 13 }}>{m.name}</td>
                  <td className="mono dim">{eps.length}</td>
                  {KINDS.map((k) => (
                    <td key={k} style={{ textAlign: "center" }}>
                      <div style={{ display: "inline-block" }}>
                        <KindCell status={agg(k)}/>
                      </div>
                    </td>
                  ))}
                  <td>
                    <div className="row gap-3">
                      <div style={{ flex: 1, minWidth: 40 }}><Bar pct={m.pct} status={m.status}/></div>
                      <span className="mono tabular" style={{ fontSize: 10 }}>{m.pct}</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="row gap-8 mono" style={{ fontSize: 10, color: "var(--text-mute)", padding: "10px 16px", borderTop: "1px solid var(--border)", letterSpacing: "0.08em" }}>
        <span><StatusDot status="ok" sm/> &nbsp;OK</span>
        <span><StatusDot status="warn" sm/> &nbsp;PARCIAL</span>
        <span><StatusDot status="alert" sm/> &nbsp;ERROR</span>
        <span><StatusDot status="run" sm/> &nbsp;CORRIENDO</span>
        <span><StatusDot status="empty" sm/> &nbsp;VACÍO</span>
      </div>
    </Panel>
  );
}

// ── Master · Gantt (cronológico, ritmo de producción) ────
function MasterGanttView({ onNav }) {
  return (
    <Panel noPad>
      <div style={{ padding: "14px 20px 18px" }}>
        {/* Header week scale */}
        <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: 16, marginBottom: 8 }}>
          <div></div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(20, 1fr)", gap: 0 }}>
            {Array.from({ length: 20 }, (_, i) => (
              <div key={i} className="mono" style={{
                fontSize: 9, color: "var(--text-mute)", textAlign: "left",
                borderLeft: i % 4 === 0 ? "1px solid var(--border-2)" : "1px solid var(--border)",
                paddingLeft: 4,
                letterSpacing: "0.06em",
              }}>
                {i % 4 === 0 ? `W${i + 1}` : ""}
              </div>
            ))}
          </div>
        </div>

        {MODULES.map((m, idx) => {
          // synthetic timeline
          const start = (idx * 1.2) % 20;
          const len   = m.status === "ok" ? 3 + (idx % 2) : m.status === "warn" ? 4 : 3;
          const color = m.status === "ok" ? "var(--ok)" :
                        m.status === "warn" ? "var(--y)" :
                        m.status === "alert" ? "var(--alert)" : "var(--border-2)";
          return (
            <div key={m.id}
                 onClick={() => onNav("modulo", m.id)}
                 style={{
                   display: "grid",
                   gridTemplateColumns: "120px 1fr",
                   gap: 16,
                   alignItems: "center",
                   padding: "5px 0",
                   borderBottom: "1px solid var(--border)",
                   cursor: "pointer",
                 }}>
              <div className="row gap-3">
                <span className="mono" style={{ color: "var(--y)", width: 30, fontSize: 12 }}>{m.id}</span>
                <span className="display" style={{ fontSize: 11, letterSpacing: "0.06em" }}>{m.name}</span>
              </div>
              <div style={{ position: "relative", height: 22 }}>
                <div style={{ position: "absolute", inset: 0, background: "var(--panel-2)" }}/>
                <div style={{
                  position: "absolute",
                  top: 3, bottom: 3,
                  left: `${(start / 20) * 100}%`,
                  width: `${(len / 20) * 100}%`,
                  background: color,
                  opacity: m.status === "empty" ? 0.3 : 0.9,
                  borderLeft: `2px solid ${color}`,
                  display: "flex",
                  alignItems: "center",
                  padding: "0 6px",
                }}>
                  <span className="mono" style={{ fontSize: 9, color: "#0D0D0D", fontWeight: 600 }}>
                    {m.status !== "empty" && `${m.pct}%`}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

// ════════════════════════════════════════════════════════════
// MÓDULO — detalle de un Mn (default M3)
// ════════════════════════════════════════════════════════════

export { PageMaster };
