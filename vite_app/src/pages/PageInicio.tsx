// PageInicio — landing rediseñada.
//
// Tres bloques verticales:
//   1. Hero · métricas de impacto + factory animada (la pieza estrella).
//   2. "Próxima mejor acción" · IA orquestadora sugiere qué hacer ahora.
//   3. Estado global · semáforo de módulos + alertas + recientes.
//
// La factory anima los 4 estadios (PDF → Claude → ElevenLabs → MP3) con
// partículas SVG que recorren la cadena. Cuando algún módulo está en
// producción real, la estación correspondiente parpadea.

import * as React from "react";
import { Btn, Icon, Panel, StatusDot } from "../components";
import {
  FIXTURE_MODULES as MODULES,
  FIXTURE_EPISODES as EPISODES,
  FIXTURE_RECENT_FILES as RECENT_FILES,
  getLiveProc,
} from "../data";

export interface PageInicioProps {
  onNav: (id: string, payload?: string) => void;
  onOpenAI: (ctx?: unknown) => void;
  onOpenPalette: () => void;
}

export function PageInicio({ onNav, onOpenAI, onOpenPalette }: PageInicioProps) {
  const okMods    = MODULES.filter((m) => m.status === "ok").length;
  const warnMods  = MODULES.filter((m) => m.status === "warn").length;
  const emptyMods = MODULES.filter((m) => m.status === "empty" || m.status === "alert").length;

  const epsComplete = EPISODES.filter(
    (e) => e.state.audio === "ok" && e.state.guion === "ok" && e.state.escaleta === "ok",
  ).length;

  // Impact metric — production hours saved.
  // Heuristic: each episode ≈ 4 h trabajo manual ahorrado. Mostrado en hero.
  const hoursSaved = epsComplete * 4;

  // Compute "next best action" — IA orquestadora.
  const nextAction = computeNextAction(MODULES, EPISODES);

  return (
    <div className="content">
      {/* ─────────────────── HERO ─────────────────── */}
      <section className="hero">
        <div className="hero-text">
          <div className="hero-eyebrow">
            <span className="hero-eyebrow-bar" />
            MaquinarIA Pesada · Cockpit
          </div>
          <h1 className="hero-title">
            <span className="hero-title-strong">{epsComplete}</span>{" "}
            <span className="hero-title-dim">episodios producidos.</span>
            <br />
            <span className="hero-title-strong">{hoursSaved} h</span>{" "}
            <span className="hero-title-dim">ahorradas a un editor.</span>
          </h1>
          <p className="hero-sub">
            Un sistema de IA convierte PDFs académicos en podcasts publicados.
            Esta cabina te da el control sobre cada paso: guion, voz,
            verificación y publicación — con la trazabilidad de un pipeline
            de software, no de un proceso editorial.
          </p>
          <div className="hero-cta">
            <Btn kind="primary" onClick={onOpenPalette}
                 icon={<Icon name="search" size={12} />}>
              Buscar o ejecutar &nbsp;
              <span className="hero-kbd">⌘K</span>
            </Btn>
            <Btn kind="ghost" onClick={() => onNav("master")}
                 icon={<Icon name="grid" size={12} />}>
              Ver Master
            </Btn>
            <Btn kind="ghost" onClick={() => onNav("lanzador")}
                 icon={<Icon name="play" size={12} />}>
              Lanzar pipeline
            </Btn>
          </div>
        </div>
        <div className="hero-side">
          <FactoryDiagram modules={MODULES} liveProc={getLiveProc()} />
        </div>
      </section>

      {/* ─────────────────── KPIs en línea ─────────────────── */}
      <div className="kpi-strip">
        <KpiStrip label="Módulos · listos / total" value={`${okMods} / ${MODULES.length}`} tone="ok"   trend={`${warnMods} en curso`} />
        <KpiStrip label="Episodios · total"        value="22"                              tone="text" trend="15 M · 7 T" />
        <KpiStrip label="Producción · 30 d"        value="142 €"                           tone="text" trend="56 % budget" />
        <KpiStrip label="Tokens · 30 d"            value="18,4 M"                          tone="ok"   trend="−12 % vs anterior" />
        <KpiStrip label="Tests · CI"               value="163 ✓"                            tone="ok"   trend="ruff clean" />
      </div>

      {/* ─────────────── PRÓXIMA MEJOR ACCIÓN ─────────────── */}
      {nextAction && (
        <NextActionCard action={nextAction} onNav={onNav} onOpenAI={onOpenAI} />
      )}

      {/* ─────────────── ESTADO GLOBAL + ALERTAS ─────────────── */}
      <div className="grid gap-8 mt-12" style={{ gridTemplateColumns: "1.4fr 1fr" }}>
        <Panel
          title={<span><Icon name="module" size={12}/> &nbsp;Semáforo de módulos</span>}
          actions={<Btn sm kind="ghost" onClick={() => onNav("master")}><Icon name="arrow" size={10}/> Master</Btn>}
        >
          <div className="grid" style={{ gridTemplateColumns: "repeat(5, 1fr)", gap: 4 }}>
            {MODULES.map((m) => (
              <div
                key={m.id}
                className="mod-tile"
                onClick={() => onNav("modulo", m.id)}
              >
                <div className="mod-tile-id">{m.id}</div>
                <div className="mod-tile-dot"><StatusDot status={m.status === "empty" ? "empty" : m.status}/></div>
                <div className="mod-tile-pct">{m.pct}%</div>
              </div>
            ))}
          </div>
          <div className="row gap-8 mt-12 mono" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.08em" }}>
            <span><StatusDot status="ok" sm/> &nbsp;{okMods} OK</span>
            <span><StatusDot status="warn" sm/> &nbsp;{warnMods} EN CURSO</span>
            <span><StatusDot status="empty" sm/> &nbsp;{emptyMods} PENDIENTE</span>
          </div>
        </Panel>

        <div className="col gap-8">
          <Panel title={<span style={{ color: "var(--alert)" }}><Icon name="dot" size={10}/> &nbsp;Atención</span>}>
            <div className="col gap-4">
              <AlertRow status="alert" text="M3_T2 · audio falló (502 ElevenLabs)"
                        action="ABRIR" onClick={() => onNav("episodio", "M3_T2")} />
              <AlertRow status="warn"  text="M8 · guion truncado en bloque 4"
                        action="ABRIR" onClick={() => onNav("modulo", "M8")} />
              <AlertRow status="warn"  text="Saldo ElevenLabs: 8,40 € (recarga < 10 €)"
                        action="RECARGAR" onClick={() => onNav("consumo")} />
            </div>
          </Panel>

          <Panel title={<span><Icon name="folder" size={12}/> &nbsp;Recientes</span>} meta="auto-refresh">
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
        </div>
      </div>
    </div>
  );
}

// ═════════════════════════════ Sub-componentes ═════════════════════════════

interface KpiStripProps {
  label: string;
  value: string;
  tone: "text" | "ok" | "warn" | "alert";
  trend: string;
}

function KpiStrip({ label, value, tone, trend }: KpiStripProps) {
  return (
    <div className="kpi-strip-item">
      <div className="kpi-strip-label">{label}</div>
      <div className={`kpi-strip-value tone-${tone}`}>{value}</div>
      <div className="kpi-strip-trend">{trend}</div>
    </div>
  );
}

interface AlertRowProps {
  status: "alert" | "warn" | "ok";
  text: string;
  action: string;
  onClick: () => void;
}

function AlertRow({ status, text, action, onClick }: AlertRowProps) {
  return (
    <div className="row gap-4" style={{ padding: "6px 0", fontSize: 13 }}>
      <StatusDot status={status} sm/>
      <span className="fill">{text}</span>
      <Btn sm kind="ghost" onClick={onClick}>{action}</Btn>
    </div>
  );
}

// ─────────────────── Factory diagram ───────────────────

interface FactoryProps {
  modules: { id: string; status: string; pct: number }[];
  liveProc: { cmd: string; t: string }[];
}

function FactoryDiagram({ modules, liveProc }: FactoryProps) {
  // Detect which station has live activity from the cmd of the running proc.
  const liveStation = React.useMemo(() => {
    const cmd = (liveProc[0]?.cmd || "").toLowerCase();
    if (cmd.includes("guion")) return 1;
    if (cmd.includes("elevenlabs") || cmd.includes("episodio_v2") || cmd.includes("audio")) return 2;
    if (cmd.includes("ffmpeg") || cmd.includes("video")) return 3;
    return -1;
  }, [liveProc]);

  const STATIONS = [
    { x: 50,  label: "PDF",    icon: "📄", color: "var(--text-mute)" },
    { x: 160, label: "Claude", icon: "✦",  color: "var(--info)" },
    { x: 270, label: "11Labs", icon: "♪",  color: "var(--ok)" },
    { x: 380, label: "MP3",    icon: "▶",  color: "var(--y)" },
  ];

  // 15 module dots across belt
  const beltY = 96;
  const moduleDots = modules.map((m, i) => ({
    x: 24 + (i / (modules.length - 1)) * 408,
    status: m.status,
    id: m.id,
  }));

  return (
    <div className="factory">
      <div className="factory-eyebrow">
        <span className="factory-eyebrow-pulse" />
        Fábrica · pipeline
        <span className="factory-eyebrow-meta">
          {liveStation >= 0 ? "en operación" : "estable"}
        </span>
      </div>

      <svg viewBox="0 0 456 220" className="factory-svg">
        <defs>
          <linearGradient id="belt-glow" x1="0" x2="1">
            <stop offset="0"   stopColor="var(--y)" stopOpacity="0"/>
            <stop offset="0.5" stopColor="var(--y)" stopOpacity="0.75"/>
            <stop offset="1"   stopColor="var(--y)" stopOpacity="0"/>
          </linearGradient>
          <linearGradient id="station-fill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stopColor="var(--panel-2)"/>
            <stop offset="1" stopColor="var(--panel)"/>
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3"/>
          </filter>
        </defs>

        {/* Top belt rail */}
        <line x1="20" y1="50" x2="436" y2="50" stroke="var(--border)" strokeWidth="1"/>
        <line x1="20" y1="50" x2="436" y2="50" stroke="url(#belt-glow)" strokeWidth="2">
          <animate attributeName="x1" values="20;320" dur="3s" repeatCount="indefinite"/>
          <animate attributeName="x2" values="120;436" dur="3s" repeatCount="indefinite"/>
        </line>

        {/* Stations */}
        {STATIONS.map((s, i) => {
          const live = i === liveStation;
          return (
            <g key={i}>
              <rect x={s.x - 30} y={28} width="60" height="44"
                    fill="url(#station-fill)"
                    stroke={live ? "var(--y)" : "var(--border)"}
                    strokeWidth={live ? 1.5 : 1}
                    rx="2"/>
              {live && (
                <rect x={s.x - 30} y={28} width="60" height="44"
                      fill="none" stroke="var(--y)" strokeWidth="2" rx="2"
                      filter="url(#glow)" opacity="0.6">
                  <animate attributeName="opacity" values="0.3;0.9;0.3" dur="1.4s" repeatCount="indefinite"/>
                </rect>
              )}
              <text x={s.x} y={49} textAnchor="middle"
                    fontSize="13" fill={s.color} fontFamily="var(--f-mono)">
                {s.icon}
              </text>
              <text x={s.x} y={64} textAnchor="middle"
                    fontSize="9" fill="var(--text-mute)"
                    fontFamily="var(--f-mono)" letterSpacing="0.08em">
                {s.label.toUpperCase()}
              </text>
              {/* status led */}
              <circle cx={s.x} cy={20} r="2.5"
                      fill={live ? "var(--y)" : "var(--text-mute)"}
                      opacity={live ? 1 : 0.4}>
                {live && <animate attributeName="opacity" values="0.3;1;0.3" dur="1s" repeatCount="indefinite"/>}
              </circle>
            </g>
          );
        })}

        {/* Travelling packets */}
        {[0, 1, 2].map((i) => (
          <rect key={i} x="0" y="44" width="9" height="12"
                fill="var(--y)" opacity="0.85" rx="1">
            <animate attributeName="x" values="14;430"
                     dur="3.2s" begin={`${i * 1.06}s`} repeatCount="indefinite"/>
          </rect>
        ))}

        {/* Bottom rail of modules */}
        <line x1="20" y1={beltY + 22} x2="436" y2={beltY + 22}
              stroke="var(--border)" strokeWidth="1" strokeDasharray="2 4"/>
        <text x="20" y={beltY + 6} fontSize="8" fill="var(--text-mute)"
              fontFamily="var(--f-mono)" letterSpacing="0.12em">
          MÓDULOS · M0 → M14
        </text>

        {moduleDots.map((m, i) => {
          const color = m.status === "ok" ? "var(--ok)"
                      : m.status === "warn" ? "var(--warn)"
                      : m.status === "alert" ? "var(--alert)"
                      : "var(--text-mute)";
          return (
            <g key={i}>
              <circle cx={m.x} cy={beltY + 22} r="4" fill={color}/>
              {(m.status === "warn" || m.status === "alert") && (
                <circle cx={m.x} cy={beltY + 22} r="4" fill="none"
                        stroke={color} strokeWidth="1">
                  <animate attributeName="r" values="4;10;4" dur="1.8s" repeatCount="indefinite"/>
                  <animate attributeName="opacity" values="0.6;0;0.6" dur="1.8s" repeatCount="indefinite"/>
                </circle>
              )}
            </g>
          );
        })}

        {/* Output bucket */}
        <g transform="translate(390, 174)">
          <rect x="0" y="0" width="44" height="26" fill="var(--panel-2)" stroke="var(--border)" rx="2"/>
          <text x="22" y="17" textAnchor="middle" fontSize="9"
                fill="var(--y)" fontFamily="var(--f-mono)">
            22 EPS
          </text>
        </g>
      </svg>
    </div>
  );
}

// ─────────────────── Next-best-action ───────────────────

interface NextAction {
  emoji: string;
  title: string;
  detail: string;
  primaryLabel: string;
  primaryTarget: () => void;
  secondaryLabel?: string;
  secondaryTarget?: () => void;
  cost?: string;
  duration?: string;
}

function computeNextAction(
  modules: { id: string; status: string; pct: number }[],
  episodes: { id: string; state: { audio: string; guion: string } }[],
): NextAction | null {
  // 1. Si hay un episodio con guion pero sin audio, sugerir generar audio.
  const epPending = episodes.find((e) => e.state.guion === "ok" && e.state.audio !== "ok");
  if (epPending) {
    return {
      emoji: "⚡",
      title: `Generar audio de ${epPending.id}`,
      detail: "Tiene guion completo y verificado pero falta sintetizar el audio.",
      primaryLabel: "Lanzar generar_episodio_v2",
      primaryTarget: () => {},
      secondaryLabel: "Abrir episodio",
      secondaryTarget: () => {},
      cost: "≈ 0,18 €",
      duration: "≈ 12 min",
    };
  }
  // 2. Si hay un módulo en alerta o warn, sugerir abrirlo.
  const modWarn = modules.find((m) => m.status === "alert" || m.status === "warn");
  if (modWarn) {
    return {
      emoji: "⚠",
      title: `Atender ${modWarn.id}`,
      detail: `Estado ${modWarn.status} · ${modWarn.pct}% de completitud. Revisa logs y verificaciones.`,
      primaryLabel: "Abrir módulo",
      primaryTarget: () => {},
      cost: "—",
      duration: "—",
    };
  }
  // 3. Si todo OK, sugerir empezar el siguiente módulo vacío.
  const modEmpty = modules.find((m) => m.status === "empty");
  if (modEmpty) {
    return {
      emoji: "▸",
      title: `Empezar ${modEmpty.id}`,
      detail: "Es el siguiente módulo sin contenido producido. Genera su PDF y guion.",
      primaryLabel: "Lanzar generar_guion",
      primaryTarget: () => {},
      cost: "≈ 0,40 €",
      duration: "≈ 4 min",
    };
  }
  return null;
}

function NextActionCard({
  action,
  onNav,
  onOpenAI,
}: {
  action: NextAction;
  onNav: (id: string, payload?: string) => void;
  onOpenAI: (ctx?: unknown) => void;
}) {
  return (
    <div className="next-action">
      <div className="next-action-meta">
        <span className="next-action-eyebrow">
          <span className="next-action-eyebrow-dot" />
          Próxima mejor acción
        </span>
        <div className="next-action-title">
          <span className="next-action-emoji">{action.emoji}</span>
          {action.title}
        </div>
        <div className="next-action-detail">{action.detail}</div>
        {(action.cost || action.duration) && (
          <div className="next-action-stats">
            {action.cost && <span><span className="mute">coste</span> {action.cost}</span>}
            {action.duration && <span><span className="mute">duración</span> {action.duration}</span>}
            <span className="mute">·</span>
            <span>Claude orquesta el flujo</span>
          </div>
        )}
      </div>
      <div className="next-action-cta">
        <Btn kind="primary" onClick={() => onNav("lanzador")}
             icon={<Icon name="play" size={11} />}>
          {action.primaryLabel}
        </Btn>
        {action.secondaryLabel && (
          <Btn kind="ghost" sm onClick={() => onOpenAI({ purpose: "suggest" })}
               icon={<Icon name="spark" size={10} />}>
            Pedir consejo a Claude
          </Btn>
        )}
      </div>
    </div>
  );
}
