// OnboardingTour — first-run guided tour.
//
// 5 steps presented as a centered modal with a translucent backdrop.
// The tour auto-launches on first visit (LS key set on completion or skip)
// and can be re-launched manually via ? key.

import * as React from "react";
import { Btn, Icon } from "../components";
import { formatCombo } from "../lib/useHotkeys";

const STORAGE_KEY = "mp:onboarding:v3:done";

export function hasSeenOnboarding(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

export function markOnboardingSeen() {
  try {
    localStorage.setItem(STORAGE_KEY, "1");
  } catch { /* private mode */ }
}

interface Step {
  eyebrow: string;
  title: React.ReactNode;
  body: React.ReactNode;
  illustration?: React.ReactNode;
}

const STEPS: Step[] = [
  {
    eyebrow: "Bienvenida",
    title: "Cabina de producción de podcasts con IA.",
    body: (
      <>
        Maquinaria Pesada convierte PDFs académicos en episodios de podcast
        (y videopodcast) producidos por IA. Esta cabina te da el control de
        cada paso del pipeline — guion, audio, escaleta, vídeo — con la
        trazabilidad de un sistema de software.
      </>
    ),
    illustration: <FactoryMini />,
  },
  {
    eyebrow: "Estructura",
    title: "Master, módulos, temas.",
    body: (
      <>
        El curso es un <strong>Master</strong> con 15 <strong>módulos</strong>{" "}
        (M0–M14). Cada módulo tiene su episodio largo y N <strong>temas</strong>{" "}
        cortos (Mn_Tk). Módulos y temas usan la misma página: 5 contenidos
        (PDF · guion · escaleta · audio · vídeo) + sus trazas de generación.
      </>
    ),
  },
  {
    eyebrow: "Navegación",
    title: "Tres secciones. Nada más.",
    body: (
      <>
        <strong>Producción</strong> es donde se trabaja:
        master → módulo → tema, con todos los contenidos y trazas en una sola pantalla.{" "}
        <strong>Datos</strong> reúne coste IA, métricas de difusión, optimización y logs.{" "}
        <strong>Sistema</strong> contiene conectores, lanzador de pipelines, fuentes y ajustes.
      </>
    ),
  },
  {
    eyebrow: "Atajo estrella",
    title: <>Pulsa <kbd>{formatCombo("mod+k")}</kbd> para todo.</>,
    body: (
      <>
        La paleta de comandos te lleva a cualquier módulo, tema o acción sin
        navegar manualmente. Otros atajos: <kbd>g p</kbd> Producción,{" "}
        <kbd>g d</kbd> Datos, <kbd>g s</kbd> Sistema, <kbd>?</kbd> esta ayuda,{" "}
        <kbd>Esc</kbd> cierra cualquier panel.
      </>
    ),
    illustration: <PaletteMini />,
  },
  {
    eyebrow: "Operativa",
    title: "Un click por contenido.",
    body: (
      <>
        En la página de un módulo o tema, cada uno de los 5 slots tiene su
        botón <strong>Generar</strong> que ejecuta el pipeline con parámetros
        sensatos pre-rellenados. El log empieza a fluir en el panel{" "}
        <strong>Live stream</strong> a la derecha. Para tocar flags avanzados,
        pulsa el botón <kbd>…</kbd> al lado.
      </>
    ),
  },
];

export interface OnboardingTourProps {
  open: boolean;
  onClose: () => void;
}

export function OnboardingTour({ open, onClose }: OnboardingTourProps) {
  const [step, setStep] = React.useState(0);

  React.useEffect(() => {
    if (open) setStep(0);
  }, [open]);

  if (!open) return null;
  const s = STEPS[step];
  const last = step === STEPS.length - 1;

  function finish() {
    markOnboardingSeen();
    onClose();
  }

  return (
    <div className="onb-backdrop" onClick={finish}>
      <div className="onb" onClick={(e) => e.stopPropagation()}>
        <div className="onb-progress">
          {STEPS.map((_, i) => (
            <span key={i} className={`onb-dot${i === step ? " active" : i < step ? " done" : ""}`} />
          ))}
        </div>

        {s.illustration && <div className="onb-illu">{s.illustration}</div>}

        <div className="onb-eyebrow">{s.eyebrow}</div>
        <h2 className="onb-title">{s.title}</h2>
        <div className="onb-body">{s.body}</div>

        <div className="onb-actions">
          <Btn kind="ghost" sm onClick={finish}>Saltar</Btn>
          <div className="onb-actions-spacer" />
          {step > 0 && (
            <Btn kind="ghost" sm onClick={() => setStep((i) => i - 1)}>
              Anterior
            </Btn>
          )}
          {!last ? (
            <Btn kind="primary" sm onClick={() => setStep((i) => i + 1)}
                 icon={<Icon name="arrow" size={11} />}>
              Siguiente
            </Btn>
          ) : (
            <Btn kind="primary" sm onClick={finish}
                 icon={<Icon name="check" size={11} />}>
              Empezar
            </Btn>
          )}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────── illustrations ───────────────────────────

function FactoryMini() {
  return (
    <svg viewBox="0 0 320 100" className="onb-svg">
      <defs>
        <linearGradient id="onb-grad" x1="0" x2="1">
          <stop offset="0" stopColor="var(--y)" stopOpacity="0" />
          <stop offset="0.5" stopColor="var(--y)" stopOpacity="0.55" />
          <stop offset="1" stopColor="var(--y)" stopOpacity="0" />
        </linearGradient>
      </defs>
      <line x1="20" y1="50" x2="300" y2="50" stroke="var(--border-2)" strokeWidth="1"/>
      <line x1="20" y1="50" x2="300" y2="50" stroke="url(#onb-grad)" strokeWidth="2">
        <animate attributeName="x1" values="20;200" dur="2.4s" repeatCount="indefinite"/>
        <animate attributeName="x2" values="120;300" dur="2.4s" repeatCount="indefinite"/>
      </line>
      {[60, 130, 200, 270].map((cx, i) => (
        <g key={i}>
          <rect x={cx - 22} y={30} width="44" height="40" fill="var(--panel)" stroke="var(--border-2)" />
          <text x={cx} y={54} textAnchor="middle" fontSize="9" fill="var(--text-mute)" fontFamily="var(--f-mono)" letterSpacing="0.1em">
            {["PDF", "GUION", "AUDIO", "MP3"][i]}
          </text>
          <circle cx={cx} cy={20} r="2" fill="var(--y)">
            <animate attributeName="opacity" values="0.3;1;0.3" dur="1.6s" begin={`${i * 0.4}s`} repeatCount="indefinite"/>
          </circle>
        </g>
      ))}
      <rect x="0" y="44" width="10" height="12" fill="var(--y)">
        <animate attributeName="x" values="0;310" dur="2.4s" repeatCount="indefinite"/>
      </rect>
    </svg>
  );
}

function PaletteMini() {
  return (
    <svg viewBox="0 0 320 100" className="onb-svg">
      <rect x="40" y="14" width="240" height="72" fill="var(--panel)" stroke="var(--border-2)" />
      <rect x="40" y="14" width="240" height="22" fill="var(--bg-2)" />
      <circle cx="55" cy="25" r="3" stroke="var(--text-mute)" strokeWidth="1" fill="none" />
      <text x="68" y="29" fontSize="10" fill="var(--text-mute)" fontFamily="var(--f-mono)" letterSpacing="-0.005em">
        generar audio M3_T2
      </text>
      <rect x="218" y="19" width="46" height="12" fill="var(--bg-2)" stroke="var(--border-2)"/>
      <text x="241" y="28" textAnchor="middle" fontSize="9" fill="var(--text-mute)" fontFamily="var(--f-mono)">⌘K</text>

      <rect x="40" y="40" width="240" height="14" fill="var(--y-soft)" />
      <rect x="40" y="40" width="2" height="14" fill="var(--y)" />
      <text x="52" y="50" fontSize="9" fill="var(--y)" fontFamily="var(--f-mono)">
        Generar audio · M3_T2 · 12 min · 0,18 €
      </text>
      <text x="52" y="66" fontSize="9" fill="var(--text-mute)" fontFamily="var(--f-mono)">
        Generar guion · M3_T1
      </text>
      <text x="52" y="78" fontSize="9" fill="var(--text-mute)" fontFamily="var(--f-mono)">
        Abrir M3_T2_produccion.log
      </text>
    </svg>
  );
}
