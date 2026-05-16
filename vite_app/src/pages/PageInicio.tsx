// PageInicio — landing editorial premium.
//
// Tres bloques:
//   1. Hero editorial · número gigante + manifesto + CTAs + factory animada.
//   2. KPI grande de 4 métricas tipográficas (sin cajas, separadores verticales).
//   3. Próxima mejor acción + semáforo de módulos + alertas — todo en cards
//      espaciosas con la nueva paleta cálida.

import * as React from "react";
import { Icon } from "../components";
import {
  FIXTURE_MODULES as MODULES,
  FIXTURE_EPISODES as EPISODES,
  getLiveProc,
} from "../data";

export interface PageInicioProps {
  onNav: (id: string, payload?: string) => void;
  onOpenAI: (ctx?: unknown) => void;
  onOpenPalette: () => void;
}

export function PageInicio({ onNav, onOpenAI, onOpenPalette }: PageInicioProps) {
  const epsComplete = EPISODES.filter(
    (e) => e.state.audio === "ok" && e.state.guion === "ok" && e.state.escaleta === "ok",
  ).length;
  const okMods    = MODULES.filter((m) => m.status === "ok").length;
  const warnMods  = MODULES.filter((m) => m.status === "warn").length;
  const emptyMods = MODULES.filter((m) => m.status === "empty" || m.status === "alert").length;
  const hoursSaved = epsComplete * 4;

  const nextAction = computeNextAction();

  return (
    <div className="page">
      {/* ════════════════════════ HERO ════════════════════════ */}
      <section className="ed-hero">
        <div className="ed-hero-left">
          <div className="ed-hero-eyebrow">Maquinaria Pesada · Cockpit</div>
          <h1 className="ed-hero-title editorial">
            <span className="num">{epsComplete}</span>{" "}
            <span className="accent">episodios</span> producidos,
            <br/>
            <span className="num">{hoursSaved}</span>{" "}
            <span className="accent">horas</span> ahorradas.
          </h1>
          <p className="ed-hero-lede">
            Un sistema de inteligencia artificial convierte PDFs académicos en
            podcasts publicados. Aquí controlas cada paso del pipeline — desde
            la generación del guion hasta la validación del audio final — con
            la trazabilidad de un sistema de software.
          </p>
          <div className="ed-hero-cta">
            <button className="btn2 primary lg" onClick={onOpenPalette}>
              <Icon name="search" size={12}/>
              Buscar o ejecutar
              <span className="kbd-inline">⌘K</span>
            </button>
            <button className="btn2 lg" onClick={() => onNav("master")}>
              Ver Producción
              <Icon name="arrow" size={10}/>
            </button>
          </div>
        </div>

        <aside className="ed-hero-aside">
          <header className="ed-hero-aside-eyebrow">
            <span className="ed-hero-aside-eyebrow-dot"/>
            Fábrica · pipeline
            <span className="ed-hero-aside-meta">en operación</span>
          </header>
          <FactoryDiagramV2 liveProc={getLiveProc()}/>
          <div className="factory2-legend">
            <span className="factory2-legend-item"><span className="factory2-legend-dot" style={{ background: "var(--ok)" }}/> listos · {okMods}</span>
            <span className="factory2-legend-item"><span className="factory2-legend-dot" style={{ background: "var(--warn)" }}/> en curso · {warnMods}</span>
            <span className="factory2-legend-item"><span className="factory2-legend-dot" style={{ background: "var(--text-faint)" }}/> pendientes · {emptyMods}</span>
          </div>
        </aside>
      </section>

      {/* ════════════════════════ KPI EDITORIAL ════════════════════════ */}
      <section className="kpi2-row">
        <div className="kpi2">
          <div className="kpi2-label">Episodios</div>
          <div className="kpi2-value">22</div>
          <div className="kpi2-trend">15 M · 7 T · 3 nuevos esta semana</div>
        </div>
        <div className="kpi2">
          <div className="kpi2-label">Producción · 30 d</div>
          <div className="kpi2-value y">142 €</div>
          <div className="kpi2-trend">56 % del budget de 250 €</div>
        </div>
        <div className="kpi2">
          <div className="kpi2-label">Tokens · 30 d</div>
          <div className="kpi2-value ok">18,4 M</div>
          <div className="kpi2-trend">−12 % vs mes anterior</div>
        </div>
        <div className="kpi2">
          <div className="kpi2-label">Tests · CI</div>
          <div className="kpi2-value ok">163 ✓</div>
          <div className="kpi2-trend">ruff clean · pytest verde</div>
        </div>
      </section>

      {/* ════════════════════════ PRÓXIMA MEJOR ACCIÓN ════════════════════════ */}
      {nextAction && (
        <section className="next2">
          <div>
            <div className="next2-eyebrow">
              <span className="next2-eyebrow-dot"/>
              Próxima mejor acción · sugerida por Claude
            </div>
            <h2 className="next2-title">{nextAction.title}</h2>
            <p className="next2-detail">{nextAction.detail}</p>
            <div className="next2-stats">
              <span><span className="lbl">coste</span> {nextAction.cost}</span>
              <span className="sep"/>
              <span><span className="lbl">duración</span> {nextAction.duration}</span>
              <span className="sep"/>
              <span><span className="lbl">pipeline</span> {nextAction.pipe}</span>
            </div>
          </div>
          <div className="next2-cta">
            <button className="btn2 primary" onClick={() => onNav("pipeline")}>
              <Icon name="play" size={11}/>
              Lanzar ahora
            </button>
            <button className="btn2 ghost sm" onClick={() => onOpenAI({ purpose: "suggest" })}>
              <Icon name="spark" size={10}/>
              Pedir consejo
            </button>
          </div>
        </section>
      )}

      {/* ════════════════════════ MÓDULOS (semáforo) ════════════════════════ */}
      <header className="section2-hd">
        <div className="section2-hd-left">
          <div className="section2-hd-eyebrow">Producción · curso</div>
          <h2 className="section2-hd-title">15 módulos del Master</h2>
        </div>
        <div className="section2-hd-right">
          <button className="btn2 sm ghost" onClick={() => onNav("master")}>
            Ver todos
            <Icon name="arrow" size={10}/>
          </button>
        </div>
      </header>
      <div className="mods2">
        {MODULES.slice(0, 15).map((m) => (
          <button key={m.id} className="mod2"
                  onClick={() => onNav("modulo", m.id)}>
            <div className="mod2-head">
              <span className="mod2-id">{m.id}</span>
              <span className={`mod2-dot ${m.status === "empty" ? "empty" : m.status}`}/>
            </div>
            <p className="mod2-name">{m.name}</p>
            <div className="mod2-meta">{m.pct}% completado</div>
            <div className="mod2-bar">
              <div className="mod2-bar-fill" style={{ width: `${m.pct}%` }}/>
            </div>
          </button>
        ))}
      </div>

      {/* ════════════════════════ ATENCIÓN ════════════════════════ */}
      <header className="section2-hd">
        <div className="section2-hd-left">
          <div className="section2-hd-eyebrow">Operación · ahora</div>
          <h2 className="section2-hd-title">Requieren atención</h2>
        </div>
      </header>
      <div>
        <div className="alert2 alert" onClick={() => onNav("episodio", "M3_T2")}>
          <span className="alert2-icon"/>
          <span className="alert2-text">
            <strong>M3_T2</strong> · audio falló (502 ElevenLabs) — reintentar bloque 7
          </span>
          <span className="alert2-action">Abrir →</span>
        </div>
        <div className="alert2 warn" onClick={() => onNav("modulo", "M8")}>
          <span className="alert2-icon"/>
          <span className="alert2-text">
            <strong>M8</strong> · guion truncado en bloque 4
          </span>
          <span className="alert2-action">Abrir →</span>
        </div>
        <div className="alert2 warn" onClick={() => onNav("datos")}>
          <span className="alert2-icon"/>
          <span className="alert2-text">
            Saldo <strong>ElevenLabs</strong>: 8,40 € restantes (recargar &lt; 10 €)
          </span>
          <span className="alert2-action">Recargar →</span>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// FactoryDiagramV2 — refined SVG factory with hairline grid & soft glow.
// ═══════════════════════════════════════════════════════════════════════════

function FactoryDiagramV2({ liveProc }: { liveProc: { cmd: string }[] }) {
  const liveStation = React.useMemo(() => {
    const cmd = (liveProc[0]?.cmd || "").toLowerCase();
    if (cmd.includes("guion")) return 1;
    if (cmd.includes("elevenlabs") || cmd.includes("episodio_v2") || cmd.includes("audio")) return 2;
    if (cmd.includes("ffmpeg") || cmd.includes("video")) return 3;
    return -1;
  }, [liveProc]);

  const STATIONS = [
    { x: 60,  label: "PDF",     color: "var(--text-mute)" },
    { x: 190, label: "CLAUDE",  color: "var(--ink)" },
    { x: 320, label: "11LABS",  color: "var(--ok)" },
    { x: 450, label: "MP3",     color: "var(--y)" },
  ];

  return (
    <svg viewBox="0 0 520 280" className="factory2-svg" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="belt-glow-v2" x1="0" x2="1">
          <stop offset="0"   stopColor="var(--y)" stopOpacity="0"/>
          <stop offset="0.5" stopColor="var(--y)" stopOpacity="0.7"/>
          <stop offset="1"   stopColor="var(--y)" stopOpacity="0"/>
        </linearGradient>
        <filter id="soft-glow-v2">
          <feGaussianBlur stdDeviation="3"/>
        </filter>
        <pattern id="grid-v2" width="10" height="10" patternUnits="userSpaceOnUse">
          <path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.012)" strokeWidth="0.5"/>
        </pattern>
      </defs>

      {/* Background grid */}
      <rect x="0" y="0" width="520" height="280" fill="url(#grid-v2)"/>

      {/* Top label */}
      <text x="260" y="22" textAnchor="middle"
            fontSize="9" fill="var(--text-mute)"
            fontFamily="var(--f-mono)" letterSpacing="0.18em">
        FUENTE  →  CLAUDE  →  ELEVENLABS  →  EPISODIO
      </text>

      {/* Belt */}
      <line x1="40" y1="100" x2="480" y2="100"
            stroke="var(--border-2)" strokeWidth="1"/>
      <line x1="40" y1="100" x2="480" y2="100"
            stroke="url(#belt-glow-v2)" strokeWidth="2">
        <animate attributeName="x1" values="40;360" dur="3.4s" repeatCount="indefinite"/>
        <animate attributeName="x2" values="160;480" dur="3.4s" repeatCount="indefinite"/>
      </line>

      {/* Stations */}
      {STATIONS.map((s, i) => {
        const live = i === liveStation;
        return (
          <g key={i}>
            {/* Soft glow when live */}
            {live && (
              <rect x={s.x - 36} y={70} width="72" height="60" rx="6"
                    fill="rgba(232,197,71,0.18)" filter="url(#soft-glow-v2)">
                <animate attributeName="opacity" values="0.3;1;0.3"
                         dur="1.6s" repeatCount="indefinite"/>
              </rect>
            )}
            <rect x={s.x - 32} y={74} width="64" height="52" rx="4"
                  fill="var(--panel)"
                  stroke={live ? "var(--y)" : "var(--border-2)"}
                  strokeWidth={live ? 1.2 : 1}/>
            {/* status led */}
            <circle cx={s.x} cy={62} r="3"
                    fill={live ? "var(--y)" : "var(--text-faint)"}>
              {live && <animate attributeName="opacity" values="0.3;1;0.3" dur="1.2s" repeatCount="indefinite"/>}
            </circle>
            {/* label */}
            <text x={s.x} y={96} textAnchor="middle"
                  fontSize="14" fill={s.color}
                  fontFamily="var(--f-display)" fontWeight="500"
                  fontStyle="italic" letterSpacing="-0.02em">
              {["F", "C", "♪", "▶"][i]}
            </text>
            <text x={s.x} y={117} textAnchor="middle"
                  fontSize="9" fill="var(--text-mute)"
                  fontFamily="var(--f-mono)" letterSpacing="0.12em">
              {s.label}
            </text>
          </g>
        );
      })}

      {/* Travelling packets */}
      {[0, 1, 2].map((i) => (
        <rect key={i} x="0" y="94" width="8" height="12" rx="2"
              fill="var(--y)" opacity="0.92">
          <animate attributeName="x" values="32;490"
                   dur="3.4s" begin={`${i * 1.13}s`} repeatCount="indefinite"/>
        </rect>
      ))}

      {/* Bottom rail · 15 modules */}
      <text x="40" y="180" fontSize="9" fill="var(--text-mute)"
            fontFamily="var(--f-mono)" letterSpacing="0.18em">
        15 MÓDULOS · M0—M14
      </text>
      <line x1="40" y1="200" x2="480" y2="200"
            stroke="var(--border)" strokeWidth="1" strokeDasharray="2 4"/>
      {Array.from({ length: 15 }, (_, i) => {
        const x = 40 + (i / 14) * 440;
        const status = i < 4 ? "ok" : i < 11 ? "warn" : "empty";
        const color = status === "ok" ? "var(--ok)"
                    : status === "warn" ? "var(--warn)" : "var(--text-faint)";
        return (
          <g key={i}>
            <circle cx={x} cy={200} r="3.5" fill={color}/>
            {status === "warn" && (
              <circle cx={x} cy={200} r="3.5" fill="none" stroke={color}>
                <animate attributeName="r" values="3.5;9;3.5" dur="2s" repeatCount="indefinite"/>
                <animate attributeName="opacity" values="0.55;0;0.55" dur="2s" repeatCount="indefinite"/>
              </circle>
            )}
          </g>
        );
      })}
      {/* Mn labels (only every 3rd to keep clean) */}
      {[0, 3, 6, 9, 12, 14].map((i) => {
        const x = 40 + (i / 14) * 440;
        return (
          <text key={i} x={x} y={222} textAnchor="middle" fontSize="8"
                fontFamily="var(--f-mono)" fill="var(--text-faint)">
            M{i}
          </text>
        );
      })}

      {/* Output */}
      <g transform="translate(420, 245)">
        <rect x="0" y="0" width="60" height="22" rx="11"
              fill="rgba(232,197,71,0.12)" stroke="rgba(232,197,71,0.32)"/>
        <text x="30" y="14" textAnchor="middle" fontSize="10"
              fontFamily="var(--f-mono)" fill="var(--y)" fontWeight="600">
          22 EPS
        </text>
      </g>
    </svg>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// computeNextAction — placeholder; in real app this comes from API.
// ═══════════════════════════════════════════════════════════════════════════

function computeNextAction() {
  const epPending = EPISODES.find(
    (e) => e.state.guion === "ok" && e.state.audio !== "ok",
  );
  if (epPending) {
    return {
      title: `Generar audio de ${epPending.id}`,
      detail: "Tiene guion completo y verificado pero falta sintetizar el audio. Es el episodio con menor coste/duración esperado de los pendientes.",
      cost: "≈ 0,18 €",
      duration: "≈ 12 min",
      pipe: "generar_episodio_v2",
    };
  }
  return null;
}
