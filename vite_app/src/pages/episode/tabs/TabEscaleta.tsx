import * as React from "react";
import { Icon, Panel, StatusDot } from "../../../components";
import { pathOf } from "../../../lib/sources";

export interface TabEscaletaProps {
  epId: string;
}

export function TabEscaleta({ epId }: TabEscaletaProps) {
  const [mode, setMode] = React.useState("render");
  const path = pathOf("escaleta", epId);

  const blocks = [
    { n: 1, title: "Apertura",               t: "0:00 → 0:42",   w: 320,  body: "Saludo, contexto del episodio, conexión con M3 (Transformers)." },
    { n: 2, title: "El problema posicional", t: "0:42 → 2:10",   w: 680,  body: "Por qué las posicionales absolutas fallan en extrapolación. María pone el ejemplo numérico." },
    { n: 3, title: "Rotación 2D por pares",  t: "2:10 → 4:30",   w: 1240, body: "Intuición geométrica primero (reloj que gira), después la matriz 2D." },
    { n: 4, title: "Atención escalada",      t: "4:30 → 6:20",   w: 1010, body: "Producto interno como medida de similitud, distancia relativa emerge naturalmente." },
    { n: 5, title: "Distancia relativa",     t: "6:20 → 8:15",   w: 980,  body: "Por qué (m - n) es lo único que importa. Implicaciones para caché K/V." },
    { n: 6, title: "Extrapolación",          t: "8:15 → 10:00",  w: 920,  body: "Demostrar que un modelo con RoPE puede operar a 2× o 4× la longitud sin re-training." },
    { n: 7, title: "Cierre y siguiente",     t: "10:00 → 11:08", w: 380,  body: "Recap, enlace al próximo episodio (M4 · LLMs y emergencia)." },
  ];

  const rawMd =
`# Escaleta · M3_T2 — Posicionales rotativos (RoPE)
> duración total: 11:08 · 7 bloques · 5530 palabras

` + blocks.map((b) =>
`## ${b.n.toString().padStart(2, "0")} · ${b.title}
- tiempo: \`${b.t}\`
- palabras: \`${b.w}\`
- contenido: ${b.body}
`).join("\n");

  return (
    <div className="grid gap-8" style={{ gridTemplateColumns: "1.5fr 1fr" }}>
      <div className="fv">
        <div className="fv-chrome">
          <Icon name="doc" size={11} />
          <span className="fv-path">{path}</span>
          <span className="fv-meta">7 bloques · 5 530 palabras · 11.2 KB</span>
          <span className="fill" />
          <div className="fv-toggle">
            <button className={mode === "render" ? "on" : ""} onClick={() => setMode("render")}>Render</button>
            <button className={mode === "raw" ? "on" : ""} onClick={() => setMode("raw")}>Raw</button>
          </div>
        </div>

        {mode === "render" ? (
          <div className="fv-body fv-md">
            <h1>Escaleta · M3_T2 — Posicionales rotativos (RoPE)</h1>
            <div className="meta">duración total: 11:08 · 7 bloques · 5530 palabras</div>
            {blocks.map((b) => (
              <div key={b.n}>
                <h2>{b.n.toString().padStart(2, "0")} · {b.title}</h2>
                <ul>
                  <li>tiempo: <code>{b.t}</code></li>
                  <li>palabras: <code>{b.w}</code></li>
                  <li>contenido: {b.body}</li>
                </ul>
              </div>
            ))}
          </div>
        ) : (
          <div className="fv-body fv-text">
            <div className="ln">
              {rawMd.split("\n").map((_, i) => <div key={i}>{i + 1}</div>)}
            </div>
            <div>
              {rawMd.split("\n").map((l, i) => {
                const cls = "lc";
                const style: React.CSSProperties = {};
                if (l.startsWith("# ")) { style.color = "var(--y)"; style.fontWeight = 600; }
                else if (l.startsWith("## ")) { style.color = "var(--y)"; }
                else if (l.startsWith("> ")) { style.color = "var(--text-mute)"; style.fontStyle = "italic"; }
                else if (l.startsWith("- ")) { style.color = "var(--text-dim)"; }
                return <div key={i} className={cls} style={style}>{l || " "}</div>;
              })}
            </div>
          </div>
        )}
      </div>

      <Panel title="Visión global">
        <div className="col gap-3">
          {blocks.map((b) => (
            <div key={b.n} className="row" style={{
              padding: "8px 10px",
              border: "1px solid var(--border)",
              background: "var(--panel-2)",
              borderLeft: "3px solid var(--y)",
              gap: 10,
            }}>
              <span className="mono" style={{ color: "var(--y)", fontSize: 11, width: 22 }}>{b.n.toString().padStart(2, "0")}</span>
              <div className="fill">
                <div className="display" style={{ fontSize: 12, letterSpacing: "0.04em" }}>{b.title}</div>
                <div className="mono dim" style={{ fontSize: 10, marginTop: 1 }}>{b.t} · {b.w} pal.</div>
              </div>
              <StatusDot status="ok" sm />
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
