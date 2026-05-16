// TabTimeline — vista DAW del episodio.
//
// Una timeline tipo Adobe Audition con:
//   - Waveform SVG generado a partir del audio (mock realista si no hay datos).
//   - Bloques del guion sincronizados (NARRADOR, IAGO, MARIA por colores).
//   - Markers de verificaciones como pins clicables.
//   - Cursor de reproducción + scrub + play/pause.
//
// Click en bloque → seek + scroll a esa fila del guion.
// Click en marker → abre detalle de la verificación + sugerencia de fix.

import * as React from "react";
import { Btn, Icon, StatusDot } from "../../../components";
import type { OpenFixFn } from "../types";

// ────────────────────── Tipos del modelo ──────────────────────

interface Block {
  id: string;
  start: number;       // segundos
  end: number;
  speaker: "narrador" | "iago" | "maria";
  text: string;
}

interface Marker {
  id: string;
  at: number;          // segundos
  kind: "warn" | "alert" | "info";
  label: string;
  detail: string;
}

export interface TabTimelineProps {
  epId: string;
  audioPath: string | null;
  onOpenFix: OpenFixFn;
}

// ────────────────────── Fixtures por episodio (mock realista) ──────────────────────

function mockBlocks(epId: string, durSec: number): Block[] {
  const blocks: Block[] = [];
  const speakers: Block["speaker"][] = ["narrador", "iago", "maria"];
  const lines = [
    "Bienvenidas a Maquinaria Pesada, el podcast donde montamos máquinas que aprenden.",
    "Hoy abrimos la pieza que más se vende mal: los transformers.",
    "Pero antes, recuerda que detrás de cada modelo hay decisiones de ingeniería, no magia.",
    "Empezamos por la atención. El truco no es lo que enseña, sino lo que decide ignorar.",
    "Si pensamos en una llave inglesa: la pones donde aprieta. La atención hace exactamente eso.",
    "Vamos a abrir el motor. Coge un cuello de botella, un cuello de pollo y multiplicación matricial.",
    "Cada token mira a todos los demás. Pero no por igual. Pondera.",
    "Y aquí entra la frecuencia: por qué los transformers escalan mejor que las redes recurrentes.",
    "Quedaos con esto: paralelismo masivo + atención decidida = entrenamiento factible.",
    "En el siguiente bloque, miramos por qué el coste cuadrático no asustó a nadie en 2017.",
    "Termino con una pista para el próximo episodio: el truco de la posición.",
    "Os esperamos en la próxima. Nos vemos en la fábrica.",
  ];
  let t = 0;
  for (let i = 0; i < lines.length; i++) {
    const len = 8 + Math.random() * 10; // 8-18 s
    if (t + len > durSec - 5) break;
    blocks.push({
      id: `${epId}-b${i}`,
      start: t,
      end: t + len,
      speaker: speakers[i % speakers.length],
      text: lines[i],
    });
    t += len + 0.5; // gap
  }
  return blocks;
}

function mockMarkers(epId: string): Marker[] {
  return [
    {
      id: "m1", at: 38, kind: "warn",
      label: "Bloque corto",
      detail: "Bloque dura 7,2 s; mínimo recomendado 8 s. ElevenLabs puede cortar la entonación.",
    },
    {
      id: "m2", at: 124, kind: "alert",
      label: "Voz inconsistente",
      detail: "MARIA cambia de tono medio entre bloques 5 y 6 (Δ pitch > 35 Hz).",
    },
    {
      id: "m3", at: 210, kind: "info",
      label: "Transición sugerida",
      detail: "Claude propone un puente de 1 s con silencio + pista ambiente.",
    },
  ];
}

// Generates a pseudo-random but stable waveform shape from the episode id.
function generateWaveform(epId: string, samples = 400): number[] {
  // Mulberry32 PRNG seeded from epId
  let h = 0;
  for (let i = 0; i < epId.length; i++) h = (h * 31 + epId.charCodeAt(i)) | 0;
  let s = h >>> 0;
  function rand() {
    s |= 0; s = (s + 0x6D2B79F5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  const out: number[] = [];
  for (let i = 0; i < samples; i++) {
    const env = Math.sin((i / samples) * Math.PI * 1.4) * 0.7 + 0.3; // envelope
    const burst = 0.15 + 0.85 * rand();
    out.push(env * burst);
  }
  return out;
}

const SPEAKER_COLOR = {
  narrador: "var(--text-mute)",
  iago: "var(--info)",
  maria: "var(--y)",
};

const SPEAKER_LABEL = {
  narrador: "NARRADOR",
  iago: "IAGO",
  maria: "MARIA",
};

// ────────────────────── Componente principal ──────────────────────

export function TabTimeline({ epId, audioPath, onOpenFix }: TabTimelineProps) {
  const durSec = 248;                            // ≈ 4:08
  const blocks = React.useMemo(() => mockBlocks(epId, durSec), [epId]);
  const markers = React.useMemo(() => mockMarkers(epId), [epId]);
  const wave = React.useMemo(() => generateWaveform(epId), [epId]);
  const [cursor, setCursor] = React.useState(0);
  const [playing, setPlaying] = React.useState(false);
  const [hoverPin, setHoverPin] = React.useState<string | null>(null);

  // Faux playback
  React.useEffect(() => {
    if (!playing) return;
    const t = setInterval(() => {
      setCursor((c) => (c + 0.5 >= durSec ? 0 : c + 0.5));
    }, 250);
    return () => clearInterval(t);
  }, [playing, durSec]);

  // Helpers
  const fmt = (s: number) =>
    `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
  const xOf = (s: number) => (s / durSec) * 100; // % of width

  function onScrub(e: React.MouseEvent<SVGSVGElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const t = Math.max(0, Math.min(durSec, (x / rect.width) * durSec));
    setCursor(t);
  }

  const activeBlock = blocks.find((b) => cursor >= b.start && cursor < b.end);

  return (
    <div className="dawtl">
      {/* ──────── Transport ──────── */}
      <div className="dawtl-transport">
        <div className="dawtl-tcontrols">
          <button
            className="dawtl-btn dawtl-btn-primary"
            onClick={() => setPlaying((p) => !p)}
            title={playing ? "Pausa (espacio)" : "Reproducir (espacio)"}
          >
            {playing ? "❚❚" : "▶"}
          </button>
          <button
            className="dawtl-btn"
            onClick={() => setCursor(0)}
            title="Volver al inicio"
          >
            ◀◀
          </button>
          <div className="dawtl-time mono">
            <span className="dawtl-time-cur">{fmt(cursor)}</span>
            <span className="dawtl-time-sep">/</span>
            <span className="dawtl-time-tot">{fmt(durSec)}</span>
          </div>
        </div>

        <div className="dawtl-meta">
          <span className="dawtl-meta-item">
            <span className="dawtl-meta-label">EP</span> {epId}
          </span>
          <span className="dawtl-meta-item">
            <span className="dawtl-meta-label">BLOQUES</span> {blocks.length}
          </span>
          <span className="dawtl-meta-item dawtl-meta-warn">
            <span className="dawtl-meta-label">MARKERS</span> {markers.length}
          </span>
        </div>

        <div className="dawtl-actions">
          {audioPath && (
            <Btn sm kind="ghost" onClick={() => window.open(`/file/${audioPath}`)}>
              <Icon name="folder" size={10}/> MP3
            </Btn>
          )}
          <Btn sm kind="primary"
               onClick={() => onOpenFix({ target: epId, error: "Revisar markers timeline", id: epId })}
               icon={<Icon name="wrench" size={11}/>}>
            Resolver con Claude
          </Btn>
        </div>
      </div>

      {/* ──────── Waveform + cursor + markers ──────── */}
      <div className="dawtl-stage">
        <svg
          viewBox="0 0 1000 160"
          preserveAspectRatio="none"
          className="dawtl-svg"
          onClick={onScrub}
        >
          {/* Background grid */}
          <defs>
            <linearGradient id="dawtl-bg" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0" stopColor="var(--panel-2)"/>
              <stop offset="1" stopColor="var(--panel)"/>
            </linearGradient>
          </defs>
          <rect x="0" y="0" width="1000" height="160" fill="url(#dawtl-bg)"/>

          {/* Time grid every 30s */}
          {Array.from({ length: Math.ceil(durSec / 30) + 1 }, (_, i) => i * 30).map((t) => (
            <g key={t}>
              <line x1={xOf(t) * 10} y1={0} x2={xOf(t) * 10} y2={160}
                    stroke="var(--border)" strokeWidth="1" strokeDasharray="2 4"/>
              <text x={xOf(t) * 10 + 4} y={12}
                    fontSize="9" fill="var(--text-mute)"
                    fontFamily="var(--f-mono)">
                {fmt(t)}
              </text>
            </g>
          ))}

          {/* Waveform — mirrored, with speaker-tinted segments */}
          {wave.map((v, i) => {
            const x = (i / wave.length) * 1000;
            const t = (i / wave.length) * durSec;
            const blk = blocks.find((b) => t >= b.start && t < b.end);
            const color = blk ? SPEAKER_COLOR[blk.speaker] : "var(--text-mute)";
            const past = t <= cursor;
            const h = v * 56;
            return (
              <line key={i}
                    x1={x} y1={80 - h} x2={x} y2={80 + h}
                    stroke={color}
                    strokeWidth="2"
                    opacity={past ? 0.95 : 0.45}/>
            );
          })}

          {/* Cursor */}
          <g style={{ pointerEvents: "none" }}>
            <line x1={xOf(cursor) * 10} y1={0}
                  x2={xOf(cursor) * 10} y2={160}
                  stroke="var(--y)" strokeWidth="1.5"/>
            <polygon
              points={`${xOf(cursor) * 10 - 5},0 ${xOf(cursor) * 10 + 5},0 ${xOf(cursor) * 10},6`}
              fill="var(--y)"/>
          </g>

          {/* Markers */}
          {markers.map((m) => {
            const x = xOf(m.at) * 10;
            const color = m.kind === "alert" ? "var(--alert)"
                        : m.kind === "warn" ? "var(--warn)"
                        : "var(--info)";
            const hover = hoverPin === m.id;
            return (
              <g key={m.id}
                 style={{ cursor: "pointer" }}
                 onMouseEnter={() => setHoverPin(m.id)}
                 onMouseLeave={() => setHoverPin(null)}
                 onClick={(e) => {
                   e.stopPropagation();
                   setCursor(m.at);
                 }}>
                <line x1={x} y1="0" x2={x} y2="160" stroke={color}
                      strokeWidth="1" strokeDasharray="3 3"
                      opacity={hover ? 0.9 : 0.6}/>
                <polygon
                  points={`${x},2 ${x - 7},14 ${x + 7},14`}
                  fill={color}/>
                {hover && (
                  <g>
                    <rect x={x - 110} y={20}
                          width="220" height="44"
                          fill="var(--panel)" stroke={color}
                          rx="3"/>
                    <text x={x} y={36} textAnchor="middle"
                          fontSize="10" fontWeight="700"
                          fill={color} fontFamily="var(--f-display)">
                      {m.label.toUpperCase()}
                    </text>
                    <foreignObject x={x - 100} y={40} width="200" height="22">
                      <div style={{
                        fontSize: 10, lineHeight: 1.3,
                        color: "var(--text-dim)",
                        fontFamily: "var(--f-body)",
                        textAlign: "center",
                      }}>
                        {m.detail}
                      </div>
                    </foreignObject>
                  </g>
                )}
              </g>
            );
          })}

          {/* Block boundaries (faint vertical ticks) */}
          {blocks.map((b) => (
            <line key={b.id}
                  x1={xOf(b.end) * 10} y1={140}
                  x2={xOf(b.end) * 10} y2={160}
                  stroke="var(--border)" strokeWidth="1"/>
          ))}
        </svg>

        {/* Currently playing block bubble */}
        {activeBlock && (
          <div className="dawtl-now">
            <div className="dawtl-now-meta">
              <span className="dawtl-now-speaker"
                    style={{ background: SPEAKER_COLOR[activeBlock.speaker] }}>
                {SPEAKER_LABEL[activeBlock.speaker]}
              </span>
              <span className="dawtl-now-range mono">
                {fmt(activeBlock.start)} → {fmt(activeBlock.end)}
              </span>
            </div>
            <div className="dawtl-now-text">{activeBlock.text}</div>
          </div>
        )}
      </div>

      {/* ──────── Bloques debajo (script con highlight sincronizado) ──────── */}
      <div className="dawtl-blocks">
        <div className="dawtl-blocks-hd">
          <span className="dawtl-blocks-title">Bloques del guion</span>
          <span className="dawtl-blocks-meta">Click sobre un bloque para reproducir desde ese punto</span>
        </div>
        <div className="dawtl-blocks-list">
          {blocks.map((b) => {
            const active = cursor >= b.start && cursor < b.end;
            return (
              <div
                key={b.id}
                className={`dawtl-block${active ? " active" : ""}`}
                onClick={() => setCursor(b.start)}
              >
                <div className="dawtl-block-side"
                     style={{ background: SPEAKER_COLOR[b.speaker] }} />
                <div className="dawtl-block-meta">
                  <span className="dawtl-block-speaker"
                        style={{ color: SPEAKER_COLOR[b.speaker] }}>
                    {SPEAKER_LABEL[b.speaker]}
                  </span>
                  <span className="dawtl-block-time mono">
                    {fmt(b.start)} – {fmt(b.end)}
                  </span>
                  <span className="dawtl-block-dur mono">
                    {(b.end - b.start).toFixed(1)} s
                  </span>
                </div>
                <div className="dawtl-block-text">{b.text}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ──────── Markers list ──────── */}
      <div className="dawtl-markers">
        <div className="dawtl-markers-hd">
          <span className="dawtl-markers-title">Markers · verificaciones automáticas</span>
        </div>
        {markers.map((m) => {
          const color = m.kind === "alert" ? "var(--alert)"
                      : m.kind === "warn" ? "var(--warn)"
                      : "var(--info)";
          return (
            <div key={m.id} className="dawtl-marker"
                 onClick={() => setCursor(m.at)}>
              <StatusDot status={m.kind === "info" ? "warn" : m.kind} sm/>
              <span className="dawtl-marker-at mono" style={{ color }}>
                {fmt(m.at)}
              </span>
              <span className="dawtl-marker-label">{m.label}</span>
              <span className="dawtl-marker-detail">{m.detail}</span>
              <Btn sm kind="ghost"
                   onClick={(e) => {
                     e.stopPropagation();
                     onOpenFix({ target: epId, error: `${m.label} @ ${fmt(m.at)}`, id: epId });
                   }}>
                Resolver
              </Btn>
            </div>
          );
        })}
      </div>
    </div>
  );
}
