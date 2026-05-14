// PageConectores — extraído del monolito (Fase 1b).
import * as React from "react";
import { Btn, Icon, StatusDot, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";
import { CONNECTORS, PIPELINE_FORMS } from "./fixtures";

function PageConectores({ onNav, onOpenAI }) {
  return (
    <div className="content">
      <PageHeader
        title="Conectores"
        sub="Servicios externos · pipelines del repo · fuentes de contenido"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Conectores", purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Mejorar con IA</Btn>
        }
      />
      <SourcePills files={srcFor("conectores")}/>

      {/* Servicios IA */}
      <div className="h2">
        <Icon name="plug" size={14}/> Servicios IA
        <span className="mono dim" style={{ fontSize: 10, marginLeft: "auto", letterSpacing: "0.08em" }}>
          {CONNECTORS.service.filter(s => s.kind !== "distribution").length} servicios
        </span>
      </div>
      <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
        {CONNECTORS.service.filter(s => s.kind !== "distribution").map((c) => (
          <div key={c.id} className="panel" style={{ padding: "14px 16px" }}>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
              <div className="display" style={{ fontSize: 13, letterSpacing: "0.06em" }}>{c.label}</div>
              <StatusDot status={c.status}/>
            </div>
            <div className="mono dim" style={{ fontSize: 11, marginBottom: 6 }}>{c.detail}</div>
            <div className="row" style={{ justifyContent: "space-between", marginTop: 8 }}>
              <span className="badge">{c.env}</span>
              <span className="mono" style={{ fontSize: 10, color: "var(--text-mute)" }}>
                {c.latency}ms
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Distribución — Spotify / iVoox / LinkedIn */}
      <div className="h2">
        <Icon name="map" size={14}/> Distribución y métricas
        <Btn sm kind="ghost" onClick={() => onNav("metricas")} icon={<Icon name="arrow" size={10}/>}>
          Ver métricas
        </Btn>
      </div>
      <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
        {CONNECTORS.service.filter(s => s.kind === "distribution").map((c) => (
          <div key={c.id} className="panel"
               style={{ padding: "14px 16px", cursor: "pointer", borderLeft: "3px solid var(--info)" }}
               onClick={() => onNav("metricas")}>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
              <div className="display" style={{ fontSize: 13, letterSpacing: "0.06em" }}>{c.label}</div>
              <StatusDot status={c.status}/>
            </div>
            <div className="mono dim" style={{ fontSize: 11, marginBottom: 6 }}>{c.detail}</div>
            <div className="row" style={{ justifyContent: "space-between", marginTop: 8 }}>
              <span className="badge">{c.env}</span>
              <span className="mono" style={{ fontSize: 10, color: "var(--text-mute)" }}>
                {c.latency}ms
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Pipelines */}
      <div className="h2">
        <Icon name="prompt" size={14}/> Pipelines del repo
        <span className="mono dim" style={{ fontSize: 10, marginLeft: "auto", letterSpacing: "0.08em" }}>
          {CONNECTORS.pipeline.length} scripts
        </span>
      </div>
      <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))" }}>
        {CONNECTORS.pipeline.map((c) => (
          <div key={c.id} className="panel" style={{ padding: "14px 16px" }}>
            <div className="row gap-3" style={{ marginBottom: 6 }}>
              <Icon name={c.icon} size={12}/>
              <span className="display" style={{ fontSize: 13, letterSpacing: "0.04em" }}>{c.label}</span>
            </div>
            <div className="mono" style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 8, minHeight: 32 }}>
              {c.description}
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="mono" style={{ fontSize: 10, color: "var(--y)" }}>{c.script}</span>
              {PIPELINE_FORMS[c.id]
                ? <Btn sm onClick={() => onNav("lanzador")}>Lanzar →</Btn>
                : <span className="mono" style={{ fontSize: 9, color: "var(--text-mute)" }}>sin form</span>}
            </div>
          </div>
        ))}
      </div>

      {/* Fuentes */}
      <div className="h2">
        <Icon name="folder" size={14}/> Fuentes de contenido
        <span className="mono dim" style={{ fontSize: 10, marginLeft: "auto", letterSpacing: "0.08em" }}>
          {CONNECTORS.source.length} tipos
        </span>
      </div>
      <div className="grid gap-8" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
        {CONNECTORS.source.map((c) => (
          <div key={c.id} className="panel"
               style={{ padding: "14px 16px", cursor: "pointer" }}
               onClick={() => onNav("fuentes")}>
            <div className="row gap-3" style={{ marginBottom: 6 }}>
              <Icon name={c.icon} size={12}/>
              <span className="display" style={{ fontSize: 13, letterSpacing: "0.04em" }}>{c.label}</span>
              <span style={{ marginLeft: "auto", color: "var(--y)", fontFamily: "var(--f-mono)", fontSize: 13 }}>
                {c.count}
              </span>
            </div>
            <div className="mono" style={{ fontSize: 10, color: "var(--y)" }}>{c.folder}<span className="dim">{c.ext}</span></div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · LANZADOR (Generar prompt para Codex)
// ════════════════════════════════════════════════════════════

export { PageConectores };
