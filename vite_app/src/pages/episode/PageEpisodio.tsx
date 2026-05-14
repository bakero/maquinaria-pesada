// Página de detalle de un episodio (guion, pdf, escaleta, audio, vídeo,
// logs, verificaciones). Extraída del bundle como módulo ES real.
import * as React from "react";
import {
  Btn, GenGuionPanel, Icon, PageHeader, SourcePills, StatusDot,
} from "../../components";
import { getEpisode, getEpisodes, getModule } from "../../data";
import { srcFor } from "../../lib/nav";
import { SOURCES } from "../../lib/sources";
import type { NavFn, OpenAIFn, OpenFixFn } from "./types";
import { TabAudio } from "./tabs/TabAudio";
import { TabChecks } from "./tabs/TabChecks";
import { TabEscaleta } from "./tabs/TabEscaleta";
import { TabGuion } from "./tabs/TabGuion";
import { TabLogs } from "./tabs/TabLogs";
import { TabPdf } from "./tabs/TabPdf";
import { TabVideo } from "./tabs/TabVideo";

export interface PageEpisodioProps {
  onNav: NavFn;
  onOpenAI: OpenAIFn;
  onOpenFix: OpenFixFn;
  epId: string | null;
}

export function PageEpisodio({ onNav, onOpenAI, onOpenFix, epId }: PageEpisodioProps) {
  // epId viene de la selección; fallback a M3_T2 como demo.
  const ep = getEpisode(epId) || getEpisode("M3_T2") || getEpisodes()[0];
  const modName = getModule(ep.mod)?.name || ep.mod;
  const [tab, setTab] = React.useState("guion");

  const tabs = [
    { id: "guion",    label: "Guion",          icon: "doc",   status: ep.state.guion,    src: "guion" },
    { id: "pdf",      label: "PDF fuente",     icon: "doc",   status: ep.state.pdf,      src: "pdf" },
    { id: "escaleta", label: "Escaleta",       icon: "doc",   status: ep.state.escaleta, src: "escaleta" },
    { id: "audio",    label: "Audio",          icon: "play",  status: ep.state.audio,    src: "audio" },
    { id: "video",    label: "Vídeo",          icon: "play",  status: ep.state.video,    src: "video" },
    { id: "logs",     label: "Logs",           icon: "log",   status: ep.state.logs,     src: "logs" },
    { id: "checks",   label: "Verificaciones", icon: "check", status: "warn",            src: "checks" },
  ];

  return (
    <div className="content">
      <PageHeader
        title={ep.title}
        sub={`${ep.id} · Módulo ${ep.mod} — ${modName} · Tipo ${ep.kind} ${ep.kind === "T" ? "(tema corto)" : "(módulo largo)"}`}
        actions={
          <React.Fragment>
            <Btn sm kind="danger" onClick={() => onOpenFix({
              target: ep.id,
              error: "ElevenLabs 502 en bloque 4 · audio truncado en 03:14",
              id: ep.id,
            })} icon={<Icon name="wrench" size={11} />}>
              Arreglar con Claude
            </Btn>
            <Btn sm kind="primary" onClick={() => onOpenAI({ target: ep.id, purpose: "improve" })}
                 icon={<Icon name="spark" size={11} />}>
              Mejorar con IA
            </Btn>
          </React.Fragment>
        }
      />
      <SourcePills files={srcFor("episodio")} />

      {/* Generación de guion + traza de validación de ESTE episodio */}
      <div style={{ marginBottom: 16 }}>
        <GenGuionPanel epId={ep.id} />
      </div>

      {/* Banner de error */}
      <div style={{
        background: "rgba(204,34,0,0.08)",
        border: "1px solid rgba(204,34,0,0.5)",
        borderLeft: "3px solid var(--alert)",
        padding: "10px 14px",
        marginBottom: 24,
        display: "flex",
        alignItems: "center",
        gap: 12,
      }}>
        <span style={{ color: "var(--alert)", fontSize: 18, lineHeight: 1 }}>●</span>
        <div className="fill">
          <div className="display" style={{ fontSize: 12, color: "var(--alert)", letterSpacing: "0.12em" }}>
            FALLO DETECTADO · 12:14:02
          </div>
          <div className="mono" style={{ fontSize: 12, color: "var(--text)", marginTop: 2 }}>
            ElevenLabs 502 en M3_T2 · bloque 4 "Atención escalada" · 2 reintentos · audio incompleto.
          </div>
        </div>
        <Btn sm kind="danger" onClick={() => onOpenFix({
          target: ep.id,
          error: "ElevenLabs 502 en bloque 4 · audio truncado en 03:14",
          id: ep.id,
        })}>Arreglar</Btn>
      </div>

      {/* Mapa de fuentes — filesystem como única fuente de verdad */}
      <div style={{
        background: "var(--panel)",
        border: "1px solid var(--border)",
        borderLeft: "3px solid var(--y)",
        padding: "10px 14px",
        marginBottom: 16,
      }}>
        <div className="row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
          <div className="display" style={{ fontSize: 11, color: "var(--text-dim)", letterSpacing: "0.16em" }}>
            <Icon name="folder" size={11} /> &nbsp; FUENTES EN DISCO
          </div>
          <div className="mono" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.08em" }}>
            filesystem-source-of-truth · scan auto
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: 6 }}>
          {tabs.map((t) => {
            const src = SOURCES[t.src];
            const has = t.status !== "empty";
            return (
              <div
                key={t.id}
                onClick={() => setTab(t.id)}
                style={{
                  padding: "8px 10px",
                  background: tab === t.id ? "var(--y-soft)" : "var(--panel-2)",
                  border: "1px solid",
                  borderColor: tab === t.id ? "var(--y)" : "var(--border)",
                  cursor: "pointer",
                }}
              >
                <div className="row gap-3" style={{ marginBottom: 4 }}>
                  <StatusDot status={t.status === "empty" ? "empty" : t.status} sm />
                  <span className="display" style={{ fontSize: 10, letterSpacing: "0.08em", color: tab === t.id ? "var(--y)" : "var(--text)" }}>
                    {t.label}
                  </span>
                </div>
                <div className="mono" style={{ fontSize: 10, color: has ? "var(--text-dim)" : "var(--text-mute)", letterSpacing: "0.02em", wordBreak: "break-all", lineHeight: 1.3 }}>
                  {t.src === "checks"
                    ? <span style={{ fontStyle: "italic" }}>todas las anteriores</span>
                    : `${src.folder}${ep.id}${src.ext}`}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs mb-12">
        {tabs.map((t) => (
          <div key={t.id} className={`tab ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
            <Icon name={t.icon} size={11} />
            {t.label}
            <StatusDot status={t.status === "empty" ? "empty" : t.status} sm />
          </div>
        ))}
      </div>

      {tab === "guion"    && <TabGuion epId={ep.id} onOpenAI={onOpenAI} />}
      {tab === "pdf"      && <TabPdf epId={ep.id} />}
      {tab === "escaleta" && <TabEscaleta epId={ep.id} />}
      {tab === "audio"    && <TabAudio epId={ep.id} onOpenFix={onOpenFix} />}
      {tab === "video"    && <TabVideo epId={ep.id} onNav={onNav} />}
      {tab === "logs"     && <TabLogs epId={ep.id} />}
      {tab === "checks"   && <TabChecks epId={ep.id} onOpenFix={onOpenFix} />}
    </div>
  );
}
