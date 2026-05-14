// PageConectores — estado real de los conectores (Fase 2).
// Datos de /api/connectors: cada conector expone .status() real
// (services → credenciales en .env, pipelines → script existe, etc.).
import * as React from "react";
import { Btn, Icon, StatusDot, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";

const CAT_ICON = { service: "plug", pipeline: "prompt", source: "folder" };

function PageConectores({ onNav, onOpenAI }) {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);

  const load = React.useCallback(() => {
    setLoading(true);
    fetch("/api/connectors", { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false); })
      .catch((e) => { setData({ ok: false, error: String(e), connectors: [] }); setLoading(false); });
  }, []);
  React.useEffect(() => { load(); }, [load]);

  const all = (data && data.connectors) || [];
  const services  = all.filter((c) => c.category === "service");
  const pipelines = all.filter((c) => c.category === "pipeline");
  const sources   = all.filter((c) => c.category === "source");

  const card = (c, onClick) => (
    <div key={c.id} className="panel"
         style={{ padding: "14px 16px", cursor: onClick ? "pointer" : "default" }}
         onClick={onClick}>
      <div className="row gap-3" style={{ marginBottom: 6 }}>
        <Icon name={CAT_ICON[c.category] || "plug"} size={12} />
        <span className="display" style={{ fontSize: 13, letterSpacing: "0.04em" }}>{c.label}</span>
        <span style={{ marginLeft: "auto" }}>
          <StatusDot status={c.status && c.status.ok ? "ok" : "alert"} />
        </span>
      </div>
      <div className="mono dim" style={{ fontSize: 11, marginBottom: 6, minHeight: 30, lineHeight: 1.4 }}>
        {c.description || c.id}
      </div>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <span className="mono" style={{ fontSize: 10, color: c.status && c.status.ok ? "var(--ok)" : "var(--alert)" }}>
          {c.status ? (c.status.detail || (c.status.ok ? "OK" : "no disponible")) : "—"}
        </span>
        {c.script && <span className="mono" style={{ fontSize: 9, color: "var(--y)" }}>{c.script}</span>}
      </div>
    </div>
  );

  return (
    <div className="content">
      <PageHeader
        title="Conectores"
        sub="Servicios externos · pipelines del repo · fuentes de contenido"
        actions={
          <React.Fragment>
            <Btn sm kind="ghost" icon={<Icon name="refresh" size={11}/>}
                 onClick={load}>{loading ? "Cargando…" : "Re-verificar"}</Btn>
            <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Conectores", purpose: "improve" })}
                 icon={<Icon name="spark" size={11}/>}>Mejorar con IA</Btn>
          </React.Fragment>
        }
      />
      <SourcePills files={srcFor("conectores")}/>

      {loading ? (
        <div className="mono dim" style={{ fontSize: 12, padding: "40px 0", textAlign: "center" }}>
          Verificando conectores…
        </div>
      ) : data && !data.ok ? (
        <div className="mono" style={{ fontSize: 12, padding: "40px 0", textAlign: "center", color: "var(--alert)" }}>
          No se pudieron cargar los conectores: {data.error || "error"}
        </div>
      ) : (
        <React.Fragment>
          {/* Servicios */}
          <div className="h2">
            <Icon name="plug" size={14}/> Servicios externos
            <span className="mono dim" style={{ fontSize: 10, marginLeft: "auto", letterSpacing: "0.08em" }}>
              {services.length} servicios
            </span>
          </div>
          <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
            {services.map((c) => card(c))}
          </div>

          {/* Pipelines */}
          <div className="h2">
            <Icon name="prompt" size={14}/> Pipelines del repo
            <span className="mono dim" style={{ fontSize: 10, marginLeft: "auto", letterSpacing: "0.08em" }}>
              {pipelines.length} scripts
            </span>
          </div>
          <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))" }}>
            {pipelines.map((c) => (
              <div key={c.id} className="panel" style={{ padding: "14px 16px" }}>
                <div className="row gap-3" style={{ marginBottom: 6 }}>
                  <Icon name="prompt" size={12}/>
                  <span className="display" style={{ fontSize: 13, letterSpacing: "0.04em" }}>{c.label}</span>
                  <span style={{ marginLeft: "auto" }}>
                    <StatusDot status={c.status && c.status.ok ? "ok" : "alert"} />
                  </span>
                </div>
                <div className="mono" style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 8, minHeight: 32 }}>
                  {c.description || c.id}
                </div>
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <span className="mono" style={{ fontSize: 10, color: "var(--y)" }}>{c.script || c.id}</span>
                  <Btn sm onClick={() => onNav("lanzador")}>Lanzar →</Btn>
                </div>
              </div>
            ))}
          </div>

          {/* Fuentes */}
          <div className="h2">
            <Icon name="folder" size={14}/> Fuentes de contenido
            <span className="mono dim" style={{ fontSize: 10, marginLeft: "auto", letterSpacing: "0.08em" }}>
              {sources.length} tipos
            </span>
          </div>
          <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
            {sources.map((c) => card(c, () => onNav("fuentes")))}
          </div>

          {/* Distribución → métricas */}
          <div className="h2">
            <Icon name="map" size={14}/> Distribución y métricas
            <Btn sm kind="ghost" onClick={() => onNav("metricas")} icon={<Icon name="arrow" size={10}/>}>
              Ver métricas
            </Btn>
          </div>
        </React.Fragment>
      )}
    </div>
  );
}

export { PageConectores };
