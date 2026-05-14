// pages-1.jsx — Inicio + Master + Módulo

// ════════════════════════════════════════════════════════════
// INICIO — was "Landing". Now also explains the IA reorganization.
// ════════════════════════════════════════════════════════════
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
                <Btn sm kind="ghost" onClick={() => onNav("episodio")}>ABRIR</Btn>
              </div>
              <div className="row gap-4" style={{ padding: "6px 0", fontSize: 13 }}>
                <StatusDot status="warn" sm/>
                <span className="fill">M8 · guion truncado en bloque 4</span>
                <Btn sm kind="ghost" onClick={() => onNav("modulo")}>ABRIR</Btn>
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
              <tr key={m.id} className="clickable" onClick={() => onNav("modulo")} style={{ height: rowH }}>
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
                <tr key={m.id} className="clickable" onClick={() => onNav("modulo")}>
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
                 onClick={() => onNav("modulo")}
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
function PageModulo({ onNav, onOpenAI }) {
  const mod = MODULES.find(m => m.id === "M3");
  const eps = EPISODES.filter(e => e.mod === "M3");

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
                  <tr key={ep.id} className="clickable" onClick={() => onNav("episodio")}>
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
          <Panel title={<span><Icon name="prompt" size={12}/> &nbsp;Acciones</span>}>
            <div className="col gap-3">
              <Btn icon={<Icon name="prompt" size={11}/>}
                   onClick={() => onNav("lanzador")}>Regenerar guion (todos)</Btn>
              <Btn icon={<Icon name="play" size={11}/>}
                   onClick={() => onNav("lanzador")}>Generar audio pendiente</Btn>
              <Btn icon={<Icon name="check" size={11}/>}
                   onClick={() => onOpenAI && onOpenAI({ target: "Módulo M3", purpose: "improve",
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

Object.assign(window, { PageInicio, PageMaster, PageModulo });
