// Página de detalle de un episodio. Carga las rutas/estado reales de
// GET /api/episode/<id> y las reparte a cada tab (Fase 2).
import * as React from "react";
import {
  Btn, GenGuionPanel, Icon, PageHeader, SourcePills, StatusDot,
} from "../../components";
import { getEpisode, getEpisodes, getModule } from "../../data";
import { srcFor } from "../../lib/nav";
import { SOURCES } from "../../lib/sources";
import type { EpisodeDetail, NavFn, OpenAIFn, OpenFixFn } from "./types";
import { TabAudio } from "./tabs/TabAudio";
import { TabChecks } from "./tabs/TabChecks";
import { TabEscaleta } from "./tabs/TabEscaleta";
import { TabGuion } from "./tabs/TabGuion";
import { TabLogs } from "./tabs/TabLogs";
import { TabPdf } from "./tabs/TabPdf";
import { TabTimeline } from "./tabs/TabTimeline";
import { TabVideo } from "./tabs/TabVideo";

export interface PageEpisodioProps {
  onNav: NavFn;
  onOpenAI: OpenAIFn;
  onOpenFix: OpenFixFn;
  epId: string | null;
}

export function PageEpisodio({ onNav, onOpenAI, onOpenFix, epId }: PageEpisodioProps) {
  // Fallback a fixtures para id/título mientras carga el detalle real.
  const ep = getEpisode(epId) || getEpisode("M3_T2") || getEpisodes()[0];
  const modName = getModule(ep.mod)?.name || ep.mod;
  const [tab, setTab] = React.useState("timeline");
  const [detail, setDetail] = React.useState<EpisodeDetail | null>(null);

  React.useEffect(() => {
    let alive = true;
    setDetail(null);
    fetch(`/api/episode/${encodeURIComponent(ep.id)}`, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (alive) setDetail(d); })
      .catch(() => { if (alive) setDetail(null); });
    return () => { alive = false; };
  }, [ep.id]);

  const paths = detail?.paths;
  const state = detail?.state || ep.state;
  const tabs = [
    { id: "timeline", label: "Timeline",       icon: "play",  status: state.audio,    src: "audio" },
    { id: "guion",    label: "Guion",          icon: "doc",   status: state.guion,    src: "guion" },
    { id: "pdf",      label: "PDF fuente",     icon: "doc",   status: state.pdf,      src: "pdf" },
    { id: "escaleta", label: "Escaleta",       icon: "doc",   status: state.escaleta, src: "escaleta" },
    { id: "audio",    label: "Audio",          icon: "play",  status: state.audio,    src: "audio" },
    { id: "video",    label: "Vídeo",          icon: "play",  status: state.video,    src: "video" },
    { id: "logs",     label: "Logs",           icon: "log",   status: state.logs,     src: "logs" },
    { id: "checks",   label: "Verificaciones", icon: "check", status: "warn",         src: "checks" },
  ];

  return (
    <div className="content">
      <PageHeader
        title={detail?.title || ep.title}
        sub={`${ep.id} · Módulo ${ep.mod} — ${modName} · Tipo ${ep.kind} ${ep.kind === "T" ? "(tema corto)" : "(módulo largo)"}`}
        actions={
          <React.Fragment>
            <Btn sm kind="danger" onClick={() => onOpenFix({
              target: ep.id,
              error: `Revisar episodio ${ep.id}`,
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
            {detail ? "rutas reales del repo" : "cargando…"}
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(8, 1fr)", gap: 6 }}>
          {tabs.map((t) => {
            const src = SOURCES[t.src];
            const has = t.status !== "empty";
            let realPath = "";
            if (paths && t.src !== "checks") {
              const v = paths[t.src as keyof typeof paths];
              realPath = Array.isArray(v) ? `${v.length} archivo(s)` : (v || "—");
            }
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
                    : (realPath || `${src.folder}…`)}
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

      {tab === "timeline" && <TabTimeline epId={ep.id} audioPath={paths?.audio ?? null} onOpenFix={onOpenFix} />}
      {tab === "guion"    && <TabGuion epId={ep.id} path={paths?.guion ?? null} onOpenAI={onOpenAI} />}
      {tab === "pdf"      && <TabPdf path={paths?.pdf ?? null} />}
      {tab === "escaleta" && <TabEscaleta path={paths?.escaleta ?? null} />}
      {tab === "audio"    && <TabAudio epId={ep.id} path={paths?.audio ?? null} onOpenFix={onOpenFix} />}
      {tab === "video"    && <TabVideo path={paths?.video ?? null} onNav={onNav} />}
      {tab === "logs"     && <TabLogs paths={paths?.logs ?? []} />}
      {tab === "checks"   && <TabChecks epId={ep.id} onOpenFix={onOpenFix} />}
    </div>
  );
}
