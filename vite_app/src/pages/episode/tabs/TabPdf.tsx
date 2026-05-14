import * as React from "react";
import { Icon, Panel } from "../../../components";
import { pathOf } from "../../../lib/sources";

export interface TabPdfProps {
  epId: string;
}

export function TabPdf({ epId }: TabPdfProps) {
  const [mode, setMode] = React.useState("embed"); // embed | text
  const [page, setPage] = React.useState(1);
  const total = 18;
  const path = pathOf("pdf", epId);
  const pdfUrl = "assets/pdf/RESUMEN_M3.pdf"; // M3 resumen como stand-in (demo)

  const pages: Record<number, any> = {
    1: {
      h1: "POSICIONALES ROTATIVOS (ROPE)",
      h2: "1. Introducción",
      paras: [
        "Las codificaciones posicionales originales (Vaswani et al., 2017) son aditivas y absolutas. Cada posición de la secuencia recibe un vector posicional que se suma al embedding del token. Esta solución es funcional pero presenta dos problemas: no extrapola bien a longitudes no vistas en entrenamiento, y rompe la simetría translacional del modelo.",
        "RoPE — introducido por Su et al. (2021) — propone una alternativa: rotar cada vector de embedding en función de su posición. La rotación se aplica en pares de dimensiones y respeta la propiedad fundamental de que el producto interno entre dos tokens depende sólo de su distancia relativa¹1.",
        "Esta propiedad tiene tres consecuencias prácticas:",
      ],
      h22: "2. Propiedades",
      paras2: [
        "(i) extrapolación natural a contextos más largos que los vistos en entrenamiento;",
        "(ii) mejor caché de K/V gracias a la invarianza translacional;",
        "(iii) integración natural con atención causal.",
      ],
    },
    2: {
      h1: "FORMULACIÓN MATEMÁTICA",
      h2: "3. Rotación 2D",
      paras: [
        "Sea x_m el vector de embedding en la posición m. RoPE aplica una rotación R_θ(m) sobre cada par de dimensiones (i, i+1). La matriz de rotación es la matriz 2D estándar parametrizada por un ángulo θ_i = 10000^(-2i/d).",
        "La elegancia del método reside en que la atención escalada Q·K^T entre las posiciones m y n se convierte naturalmente en una función de (m - n) tras aplicar las rotaciones a Q y K. Es decir: ⟨R_θ(m)·q, R_θ(n)·k⟩ depende sólo de (m - n).",
      ],
    },
    3: {
      h1: "EXTRAPOLACIÓN",
      paras: [
        "Una de las propiedades más interesantes de RoPE es que el modelo, una vez entrenado con contextos de longitud L, puede operar con contextos de longitud 2L, 4L o más sin degradación catastrófica del rendimiento. Esto contrasta con las posicionales absolutas, que producen tokens fuera de distribución para posiciones no vistas.",
      ],
    },
  };

  const pg = pages[page] || pages[1];

  return (
    <div className="grid gap-8" style={{ gridTemplateColumns: "1.4fr 1fr" }}>
      <div className="fv">
        <div className="fv-chrome">
          <Icon name="doc" size={11} />
          <span className="fv-path">{path}</span>
          <span className="fv-meta">2.4 MB · 18 páginas · v1</span>
          <span className="fill" />
          <div className="fv-toggle">
            <button className={mode === "embed" ? "on" : ""} onClick={() => setMode("embed")}>PDF</button>
            <button className={mode === "text" ? "on" : ""} onClick={() => setMode("text")}>Texto</button>
          </div>
          <a href={pdfUrl} target="_blank" rel="noopener" className="btn ghost sm" title="Abrir en nueva pestaña" style={{ textDecoration: "none" }}>
            <Icon name="folder" size={11} />
          </a>
        </div>

        {mode === "embed" ? (
          <div style={{ background: "#525659" }}>
            <iframe
              src={pdfUrl + "#view=FitH&toolbar=1&navpanes=0"}
              style={{ width: "100%", height: 720, border: 0, display: "block" }}
              title={`PDF · ${epId}`}
            />
          </div>
        ) : (
          <React.Fragment>
            <div className="fv-body paper">
              <div className="fv-page">
                <h1>{pg.h1}</h1>
                {pg.h2 && <h2>{pg.h2}</h2>}
                {pg.paras && pg.paras.map((p: string, i: number) => <p key={i}>{p}</p>)}
                {pg.h22 && <h2>{pg.h22}</h2>}
                {pg.paras2 && pg.paras2.map((p: string, i: number) => <p key={"b" + i}>{p}</p>)}
                <div className="footnum">— {page} —</div>
              </div>
            </div>

            <div className="fv-pagenav">
              <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>‹</button>
              <span className="pageof">Página</span>
              <input
                className="pageinp"
                value={page}
                onChange={(e) => {
                  const v = parseInt(e.target.value, 10);
                  if (!isNaN(v) && v >= 1 && v <= total) setPage(v);
                  else if (e.target.value === "") setPage(1);
                }}
              />
              <span className="pageof">de {total}</span>
              <button onClick={() => setPage((p) => Math.min(total, p + 1))} disabled={page >= total}>›</button>
            </div>
          </React.Fragment>
        )}
      </div>

      <Panel title="Resumen IA del PDF" meta="haiku-4.5 · 0.002€">
        <div style={{ fontSize: 13, color: "var(--text-dim)", lineHeight: 1.6 }}>
          <p style={{ marginTop: 0 }}><b style={{ color: "var(--text)" }}>Tema central:</b> codificaciones posicionales rotativas en Transformers, alternativa a las posicionales absolutas del paper original.</p>
          <p><b style={{ color: "var(--text)" }}>Conceptos clave:</b> rotación 2D por pares, distancia relativa, extrapolación, RoFormer, LLaMA, GPT-NeoX.</p>
          <p><b style={{ color: "var(--text)" }}>Recomendación para el guion:</b> empezar por la intuición geométrica antes que las fórmulas. María lleva las matemáticas; Iago pregunta desde la analogía del reloj.</p>
        </div>
        <div className="mt-8">
          <div className="h3 mb-4">Páginas con material clave</div>
          <div className="row gap-3">
            {[1, 2, 5, 9, 14].map((p) => (
              <button key={p} className="btn sm" onClick={() => setPage(p)}>{p}</button>
            ))}
          </div>
        </div>
      </Panel>
    </div>
  );
}
