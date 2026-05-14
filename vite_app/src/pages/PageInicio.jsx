// PageInicio — extraído del monolito (Fase 1b).
import * as React from "react";
import { Btn, Icon, Panel, StatusDot, Kpi, PageHeader, SourcePills } from "../components";
import { NAV_GROUPS, WIRED, srcFor, ghLink, REPO, REPO_REF } from "../lib/nav";
import { FIXTURE_MODULES as MODULES, FIXTURE_RECENT_FILES as RECENT_FILES } from "../data";

function PageInicio({ onNav, onOpenAI }) {
  const okMods   = MODULES.filter(m => m.status === "ok").length;
  const warnMods = MODULES.filter(m => m.status === "warn").length;
  const emptyMods= MODULES.filter(m => m.status === "empty" || m.status === "alert").length;

  return (
    <div className="content">
      <PageHeader
        title="Estado de obra"
        sub="Maquinaria Pesada · Cockpit · 12 may 2026 · 12:42:18"
      />
      <SourcePills files={srcFor("home")}/>

      {/* ── KPIs globales ── */}
      <div className="kpi-grid mb-12">
        <Kpi label="Módulos completos"  value={`${okMods}`}    unit={`/ ${MODULES.length}`} delta="+1 esta semana"        deltaDir="up" />
        <Kpi label="Episodios"           value="22"             unit="total"                 delta="15 M · 7 T"                          />
        <Kpi label="Producción · 30d"    value="142"            unit="€"                     delta="56% del budget (250€)" deltaDir="up" />
        <Kpi label="Tokens · 30d"        value="18.4"           unit="M"                     delta="-12% vs mes anterior"  deltaDir="dn" />
        <Kpi label="Tests"               value="163"            unit="✓"                     delta="ruff clean · pytest ✓" deltaDir="up" />
      </div>

      <div className="grid gap-8" style={{ gridTemplateColumns: "1.4fr 1fr" }}>
        {/* ── Mapa de la app (reorganización) ── */}
        <Panel
          title={<span><Icon name="grid" size={12}/> &nbsp;Mapa de la cabina ↔ repositorio</span>}
          meta="13 páginas conectadas con su código fuente"
          actions={<Btn sm kind="ghost" onClick={() => window.open(REPO + "/tree/" + REPO_REF + "/cockpit", "_blank")}>
            <Icon name="folder" size={10}/> Ver cockpit/
          </Btn>}
        >
          <div className="mono dim" style={{ fontSize: 11, marginBottom: 14, lineHeight: 1.6 }}>
            Cada página de la cabina apunta a los archivos del repo que la implementan. Antes: 16 páginas
            sin agrupar, "Master" oculta como #0, redundancia entre Estado/Master, chat libre como página
            y como drawer. Ahora: 5 dominios + un asistente como drawer global, todos enlazados a su
            código fuente en <span style={{ color: "var(--y)" }}>bakero/maquinaria-pesada</span>.
          </div>

          {NAV_GROUPS.map((g) => (
            <div key={g.label} style={{ marginBottom: 14 }}>
              <div className="h3" style={{ marginBottom: 6, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ width: 4, height: 12, background: "var(--y)" }}/>
                {g.label}
                <span className="muted mono" style={{ fontSize: 9, marginLeft: "auto" }}>
                  {g.items.length} {g.items.length === 1 ? "página" : "páginas"}
                </span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 6 }}>
                {g.items.map(it => {
                  const wired = WIRED.has(it.id);
                  return (
                    <div
                      key={it.id}
                      onClick={() => wired && onNav(it.id)}
                      style={{
                        border: "1px solid var(--border)",
                        background: wired ? "var(--panel-2)" : "transparent",
                        padding: "10px 12px",
                        cursor: wired ? "pointer" : "default",
                        opacity: wired ? 1 : 0.55,
                        position: "relative",
                      }}
                    >
                      <div className="row gap-3" style={{ marginBottom: 6 }}>
                        <Icon name={it.icon} size={11}/>
                        <span className="mono muted" style={{ fontSize: 9 }}>{it.num}</span>
                        <span className="display" style={{ fontSize: 11, color: wired ? "var(--text)" : "var(--text-mute)" }}>
                          {it.label}
                        </span>
                        {wired && <span className="badge y" style={{ marginLeft: "auto", padding: "0 4px", fontSize: 8 }}>LIVE</span>}
                      </div>
                      {it.src && it.src.length > 0 && (
                        <div className="col" style={{ gap: 2, paddingLeft: 22 }}>
                          {it.src.slice(0, 3).map((s) => (
                            <a key={s}
                               href={ghLink(s)}
                               target="_blank"
                               rel="noopener"
                               onClick={(e) => e.stopPropagation()}
                               className="mono"
                               style={{
                                 fontSize: 9.5,
                                 color: "var(--text-mute)",
                                 textDecoration: "none",
                                 letterSpacing: 0,
                                 wordBreak: "break-all",
                                 lineHeight: 1.35,
                               }}
                               title={`Abrir ${s} en GitHub`}
                               onMouseEnter={(e) => e.currentTarget.style.color = "var(--y)"}
                               onMouseLeave={(e) => e.currentTarget.style.color = "var(--text-mute)"}>
                              {s}
                            </a>
                          ))}
                          {it.src.length > 3 && (
                            <span className="mono" style={{ fontSize: 9, color: "var(--text-mute)", fontStyle: "italic" }}>
                              + {it.src.length - 3} más
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </Panel>

        <div className="col gap-8">
          {/* ── Semáforo módulos ── */}
          <Panel
            title={<span><Icon name="module" size={12}/> &nbsp;Semáforo de módulos</span>}
            actions={<Btn sm onClick={() => onNav("master")}><Icon name="arrow" size={10}/> Ver Master</Btn>}
          >
            <div className="grid" style={{ gridTemplateColumns: "repeat(5, 1fr)", gap: 4 }}>
              {MODULES.map((m) => (
                <div
                  key={m.id}
                  onClick={() => onNav("master")}
                  style={{
                    background: "var(--panel-2)",
                    border: "1px solid var(--border)",
                    padding: "8px 6px",
                    textAlign: "center",
                    cursor: "pointer",
                  }}
                >
                  <div className="mono" style={{ fontSize: 10, color: "var(--y)" }}>{m.id}</div>
                  <div style={{ margin: "5px auto 4px" }}>
                    <StatusDot status={m.status === "empty" ? "empty" : m.status}/>
                  </div>
                  <div className="mono dim" style={{ fontSize: 9 }}>{m.pct}%</div>
                </div>
              ))}
            </div>
            <div className="row gap-8 mt-12 mono" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.08em" }}>
              <span><StatusDot status="ok" sm/> &nbsp;{okMods} OK</span>
              <span><StatusDot status="warn" sm/> &nbsp;{warnMods} EN CURSO</span>
              <span><StatusDot status="empty" sm/> &nbsp;{emptyMods} PENDIENTE</span>
            </div>
          </Panel>

          {/* ── Últimos archivos ── */}
          <Panel
            title={<span><Icon name="folder" size={12}/> &nbsp;Recientes</span>}
            meta="auto-refresh"
          >
            {RECENT_FILES.map((f, i) => (
              <div key={i} className="row" style={{
                padding: "6px 0",
                borderBottom: i < RECENT_FILES.length - 1 ? "1px solid var(--border)" : "none",
                fontSize: 12, fontFamily: "var(--f-mono)",
              }}>
                <span style={{ flex: 1, color: "var(--text)" }}>{f.path}</span>
                <span style={{ color: "var(--text-mute)", fontSize: 10 }}>{f.t}</span>
              </div>
            ))}
          </Panel>

          {/* ── Alertas ── */}
          <Panel title={<span style={{ color: "var(--alert)" }}><Icon name="dot" size={10}/> &nbsp;Atención</span>}>
            <div className="col gap-4">
              <div className="row gap-4" style={{ padding: "6px 0", fontSize: 13 }}>
                <StatusDot status="alert" sm/>
                <span className="fill">M3_T2 · audio falló (502 ElevenLabs)</span>
                <Btn sm kind="ghost" onClick={() => onNav("episodio", "M3_T2")}>ABRIR</Btn>
              </div>
              <div className="row gap-4" style={{ padding: "6px 0", fontSize: 13 }}>
                <StatusDot status="warn" sm/>
                <span className="fill">M8 · guion truncado en bloque 4</span>
                <Btn sm kind="ghost" onClick={() => onNav("modulo", "M8")}>ABRIR</Btn>
              </div>
              <div className="row gap-4" style={{ padding: "6px 0", fontSize: 13 }}>
                <StatusDot status="warn" sm/>
                <span className="fill">Saldo ElevenLabs: 8.40€ (recargar &lt; 10€)</span>
                <Btn sm kind="ghost" onClick={() => onNav("consumo")}>RECARGAR</Btn>
              </div>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// MASTER — list/matrix/gantt views (3 variants tweakable)
// ════════════════════════════════════════════════════════════

export { PageInicio };
