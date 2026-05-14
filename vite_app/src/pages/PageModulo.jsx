// PageModulo — extraído del monolito (Fase 1b).
import * as React from "react";
import { Btn, Icon, Panel, Kpi, KindCell, PageHeader, SourcePills, GenGuionPanel } from "../components";
import { srcFor } from "../lib/nav";
import { SOURCES, KINDS } from "../lib/sources";
import { FIXTURE_MODULES as MODULES, FIXTURE_EPISODES as EPISODES } from "../data";

function PageModulo({ onNav, onOpenAI, modId }) {
  // modId viene de la selección (sidebar/Master); fallback a M3 como demo.
  const mod = MODULES.find(m => m.id === modId)
           || MODULES.find(m => m.id === "M3")
           || MODULES[0];
  const eps = EPISODES.filter(e => e.mod === mod.id);

  return (
    <div className="content">
      <PageHeader
        title={`${mod.id} · ${mod.name}`}
        sub={mod.short}
        actions={
          <React.Fragment>
            <Btn sm kind="ghost" icon={<Icon name="folder" size={11}/>}
                 onClick={() => fetch("/api/reveal", {
                   method: "POST",
                   headers: { "Content-Type": "application/json" },
                   body: JSON.stringify({ path: `Guiones/` }),
                 }).catch(() => {})}>
              Abrir carpeta
            </Btn>
            <Btn sm kind="primary" onClick={() => onOpenAI({ target: `Módulo ${mod.id}`, purpose: "improve" })}
                 icon={<Icon name="spark" size={11}/>}>
              Mejorar con IA
            </Btn>
          </React.Fragment>
        }
      />
      <SourcePills files={srcFor("modulo")}/>

      <div className="kpi-grid mb-12" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
        <Kpi label="Progreso"      value={mod.pct} unit="%"        delta={mod.status === "ok" ? "Listo" : "En curso"} deltaDir={mod.status === "ok" ? "up" : ""}/>
        <Kpi label="Episodios"     value={eps.length} unit=""        delta={`1 M · ${eps.length - 1} T`}/>
        <Kpi label="Gasto módulo"  value="12.4" unit="€"             delta="3 generaciones de guion"/>
        <Kpi label="Última build"  value="hoy" unit="12:38"          delta="claude-sonnet-4.6" />
      </div>

      <div className="grid gap-8" style={{ gridTemplateColumns: "1.5fr 1fr" }}>
        {/* ── Tabla de episodios ── */}
        <Panel
          title={<span><Icon name="episode" size={12}/> &nbsp;Episodios</span>}
          meta={`${eps.length} contenidos`}
          noPad
        >
          <table className="tbl">
            <thead>
              <tr>
                <th style={{ width: 100 }}>Episodio</th>
                <th>Título</th>
                <th style={{ width: 60 }}>Dur.</th>
                {KINDS.map(k => <th key={k} style={{ width: 60, textAlign: "center", padding: "8px 4px" }}>
                  <div style={{ fontSize: 10 }}>{k[0].toUpperCase() + k.slice(1, 3).toLowerCase()}</div>
                  <div className="mono" style={{
                    fontSize: 9, fontWeight: 400, color: "var(--y)",
                    letterSpacing: 0, textTransform: "none", marginTop: 2, opacity: 0.7,
                  }}>
                    {SOURCES[k].folder.replace("/", "")}
                  </div>
                </th>)}
                <th style={{ width: 40, textAlign: "right" }}></th>
              </tr>
            </thead>
            <tbody>
              {eps.map(ep => {
                const hasError = Object.values(ep.state).includes("alert");
                return (
                  <tr key={ep.id} className="clickable" onClick={() => onNav("episodio", ep.id)}>
                    <td>
                      <div className="row gap-3">
                        <span className="badge" style={{
                          background: ep.kind === "M" ? "var(--y-soft)" : "var(--panel-2)",
                          color: ep.kind === "M" ? "var(--y)" : "var(--text-dim)",
                          borderColor: ep.kind === "M" ? "var(--y)" : "var(--border-2)",
                        }}>{ep.kind}</span>
                        <span className="mono" style={{ fontSize: 11 }}>{ep.id}</span>
                        {hasError && <span style={{ color: "var(--alert)" }} title="Errores detectados">●</span>}
                      </div>
                    </td>
                    <td style={{ fontSize: 13 }}>{ep.title.replace(/^Episodio M\d+ — /, "").replace(/^T\d+ — /, "")}</td>
                    <td className="mono dim" style={{ fontSize: 11 }}>{ep.dur}</td>
                    {KINDS.map(k => (
                      <td key={k} style={{ textAlign: "center" }}>
                        <div style={{ display: "inline-block" }}>
                          <KindCell status={ep.state[k]}/>
                        </div>
                      </td>
                    ))}
                    <td style={{ textAlign: "right" }}><Icon name="arrow" size={11}/></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Panel>

        {/* ── Acciones del módulo ── */}
        <div className="col gap-8">
          <GenGuionPanel epId={mod.id}/>

          <Panel title={<span><Icon name="prompt" size={12}/> &nbsp;Acciones</span>}>
            <div className="col gap-3">
              <Btn icon={<Icon name="play" size={11}/>}
                   onClick={() => onNav("lanzador")}>Generar audio pendiente</Btn>
              <Btn icon={<Icon name="check" size={11}/>}
                   onClick={() => onOpenAI && onOpenAI({ target: `Módulo ${mod.id}`, purpose: "improve",
                                                         hint: "validar módulo completo" })}>
                Validar módulo completo
              </Btn>
              <Btn kind="ghost" icon={<Icon name="doc" size={11}/>}
                   onClick={() => window.open("/files/RRSS/feed.xml", "_blank")}>
                Exportar a podcast .rss
              </Btn>
            </div>
          </Panel>

          <Panel title={<span><Icon name="log" size={12}/> &nbsp;Últimos logs</span>} meta="M3">
            <div className="col" style={{ fontSize: 11, fontFamily: "var(--f-mono)" }}>
              <div style={{ padding: "4px 0", borderBottom: "1px solid var(--border)" }}>
                <span className="muted">12:38:02 </span>
                <span style={{ color: "var(--ok)" }}>[OK] </span>
                <span>guion M3 generado · 9842 palabras</span>
              </div>
              <div style={{ padding: "4px 0", borderBottom: "1px solid var(--border)" }}>
                <span className="muted">12:33:14 </span>
                <span style={{ color: "var(--info)" }}>[INFO] </span>
                <span>dual_debate convergido (94%)</span>
              </div>
              <div style={{ padding: "4px 0", borderBottom: "1px solid var(--border)" }}>
                <span className="muted">11:58:40 </span>
                <span style={{ color: "var(--alert)" }}>[ERR] </span>
                <span>eleven 502 en M3_T2 · bloque 4</span>
              </div>
              <div style={{ padding: "4px 0" }}>
                <span className="muted">11:42:08 </span>
                <span style={{ color: "var(--warn)" }}>[WARN] </span>
                <span>vídeo M3 escena drift 1.8s @ 41:22</span>
              </div>
            </div>
          </Panel>

          <Panel title={<span><Icon name="brain" size={12}/> &nbsp;Diagnóstico IA</span>}>
            <div style={{ fontSize: 13, color: "var(--text-dim)", lineHeight: 1.55 }}>
              El módulo está al <b style={{ color: "var(--y)" }}>72%</b>. Bloqueado por
              M3_T2 (audio fallido) y vídeo M3 (drift de escena).
              Coste estimado para cerrar: <b style={{ color: "var(--text)" }}>~0.18€</b>.
            </div>
            <div className="mt-8">
              <Btn sm kind="primary" onClick={() => onOpenAI({ target: `Módulo ${mod.id}`, purpose: "improve" })}>
                <Icon name="spark" size={10}/> Sugerir plan
              </Btn>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

export { PageModulo };
