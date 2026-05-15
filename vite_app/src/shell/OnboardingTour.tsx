// OnboardingTour — first-run guided tour.
//
// 5 steps presented as a centered modal with a translucent backdrop.
// The tour auto-launches on first visit (LS key set on completion or skip)
// and can be re-launched manually from the Topbar question button.

import * as React from "react";
import { Btn, Icon } from "../components";
import { formatCombo } from "../lib/useHotkeys";

const STORAGE_KEY = "mp:onboarding:v1:done";

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
    title: "Tu cabina de producción.",
    body: (
      <>
        Un sistema de IA convierte PDFs académicos en episodios de podcast
        producidos automáticamente. La cabina te da control sobre cada paso
        — desde la generación del guion hasta la validación del audio
        final — sin perder de vista el coste, los logs ni los errores.
      </>
    ),
    illustration: <FactoryMini />,
  },
  {
    eyebrow: "Navegación",
    title: "Cinco dominios, una barra lateral.",
    body: (
      <>
        <strong>Producción</strong> (Inicio · Master · Módulo · Episodio),{" "}
        <strong>Diseño</strong> (Pizarra · Mapa), <strong>Pipeline</strong>{" "}
        (Conectores · Lanzador), <strong>Recursos</strong> (Fuentes · Player
        · Métricas) y <strong>Sistema</strong> (Logs · Optimizar · Consumo).
        Las migas de pan superiores siempre indican dónde estás.
      </>
    ),
  },
  {
    eyebrow: "Atajo estrella",
    title: <>Pulsa <kbd>{formatCombo("mod+k")}</kbd> para todo.</>,
    body: (
      <>
        El paleta de comandos abre desde cualquier página y te lleva a
        episodios, módulos o acciones (generar audio, validar, abrir logs)
        sin hacer scroll. Hay más atajos: <kbd>g m</kbd> para Master,{" "}
        <kbd>g e</kbd> para Episodio, <kbd>?</kbd> para esta ayuda,{" "}
        <kbd>Esc</kbd> para cerrar cualquier modal.
      </>
    ),
    illustration: <PaletteMini />,
  },
  {
    eyebrow: "Acción contextual",
    title: "El botón cambia según lo que falta.",
    body: (
      <>
        Cada Episodio expone una <em>action bar</em> con solo las acciones
        viables: si falta el guion, ofrece "Generar guion"; si hay guion
        pero no audio, "Generar audio"; si hay audio, "Validar" y
        "Regenerar". Cuando hay errores aparece el botón rojo{" "}
        <strong>Arreglar con Claude</strong>, que pasa el contexto del
        episodio (logs + verificaciones) al modelo y propone un fix.
      </>
    ),
  },
  {
    eyebrow: "Seguridad",
    title: "Sandbox IA por defecto.",
    body: (
      <>
        Las sesiones de Claude lanzadas desde la cabina solo pueden escribir
        en <code>Guiones/</code>, <code>episodios/</code>,{" "}
        <code>escaletas/</code> y el mapa de componentes.{" "}
        <strong>Nunca</strong> tocan el código del cockpit ni los pipelines
        top-level. Lo enforce <code>cockpit/core/sandbox.py</code> antes de
        aplicar cualquier cambio.
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
              ← Anterior
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
      {/* belt */}
      <line x1="20" y1="50" x2="300" y2="50" stroke="var(--border)" strokeWidth="2"/>
      <line x1="20" y1="50" x2="300" y2="50" stroke="url(#onb-grad)" strokeWidth="2">
        <animate attributeName="x1" values="20;200" dur="2.4s" repeatCount="indefinite"/>
        <animate attributeName="x2" values="120;300" dur="2.4s" repeatCount="indefinite"/>
      </line>
      {/* stations */}
      {[60, 130, 200, 270].map((cx, i) => (
        <g key={i}>
          <rect x={cx - 22} y={30} width="44" height="40" fill="var(--panel-2)" stroke="var(--border)" />
          <text x={cx} y={54} textAnchor="middle" fontSize="9" fill="var(--text-mute)" fontFamily="var(--f-mono)">
            {["PDF", "Claude", "11Labs", "MP3"][i]}
          </text>
          <circle cx={cx} cy={20} r="2" fill="var(--y)">
            <animate attributeName="opacity" values="0.3;1;0.3" dur="1.6s" begin={`${i * 0.4}s`} repeatCount="indefinite"/>
          </circle>
        </g>
      ))}
      {/* package */}
      <rect x="0" y="44" width="10" height="12" fill="var(--y)" rx="1">
        <animate attributeName="x" values="0;310" dur="2.4s" repeatCount="indefinite"/>
      </rect>
    </svg>
  );
}

function PaletteMini() {
  return (
    <svg viewBox="0 0 320 100" className="onb-svg">
      <rect x="40" y="14" width="240" height="72" rx="6" fill="var(--panel)" stroke="var(--border)" />
      <rect x="40" y="14" width="240" height="22" fill="var(--panel-2)" />
      <circle cx="55" cy="25" r="3" fill="var(--text-mute)" stroke="var(--text-mute)" strokeWidth="1" fillOpacity="0" />
      <text x="68" y="29" fontSize="10" fill="var(--text-mute)" fontFamily="var(--f-mono)">generar audio M3_T2</text>
      <rect x="218" y="19" width="46" height="12" rx="2" fill="var(--panel)" stroke="var(--border)"/>
      <text x="241" y="28" textAnchor="middle" fontSize="9" fill="var(--text-mute)" fontFamily="var(--f-mono)">Esc</text>

      <rect x="48" y="42" width="224" height="14" rx="2" fill="var(--y-soft)" />
      <text x="56" y="52" fontSize="9" fill="var(--y)" fontFamily="var(--f-mono)">
        ▸  M3_T2 · generar audio (12 min · €0,18)
      </text>
      <text x="56" y="68" fontSize="9" fill="var(--text-mute)" fontFamily="var(--f-mono)">
        ◦  M3_T2 · validar episodio
      </text>
      <text x="56" y="80" fontSize="9" fill="var(--text-mute)" fontFamily="var(--f-mono)">
        ◦  Abrir M3_T2_produccion.log
      </text>
    </svg>
  );
}
