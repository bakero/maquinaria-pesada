import * as React from "react";
import { Btn, Icon, Panel, Speaker } from "../../../components";
import { GUION_PREVIEW } from "../../../data";
import { pathOf } from "../../../lib/sources";
import type { OpenAIFn } from "../types";

export interface TabGuionProps {
  epId: string;
  onOpenAI: OpenAIFn;
}

export function TabGuion({ epId, onOpenAI }: TabGuionProps) {
  const [mode, setMode] = React.useState("read"); // read | raw
  const path = pathOf("guion", epId);

  const rawLines: string[] = [];
  rawLines.push(`# ${epId} · guion`);
  rawLines.push(`# generado: 2026-05-12 12:11`);
  rawLines.push(`# turnos: 142 · palabras: 9842`);
  rawLines.push(``);
  GUION_PREVIEW.forEach((line) => {
    rawLines.push(`[${line.who.toUpperCase()}] ${line.text}`);
    rawLines.push(``);
  });
  rawLines.push(`# … 136 turnos más …`);

  return (
    <div className="grid gap-8" style={{ gridTemplateColumns: "1.8fr 1fr" }}>
      <div className="fv">
        <div className="fv-chrome">
          <Icon name="doc" size={11} />
          <span className="fv-path">{path}</span>
          <span className="fv-meta">9842 palabras · 142 turnos · 38.4 KB</span>
          <span className="fill" />
          <div className="fv-toggle">
            <button className={mode === "read" ? "on" : ""} onClick={() => setMode("read")}>Lectura</button>
            <button className={mode === "raw" ? "on" : ""} onClick={() => setMode("raw")}>Raw</button>
          </div>
        </div>

        {mode === "read" ? (
          <div className="fv-body" style={{ padding: "20px 28px" }}>
            <div className="col gap-6" style={{ fontFamily: "var(--f-body)", fontSize: 15, lineHeight: 1.6 }}>
              {GUION_PREVIEW.map((line, i) => (
                <div key={i} style={{ display: "grid", gridTemplateColumns: "92px 1fr", gap: 14, padding: "8px 0", borderBottom: "1px dashed var(--border)" }}>
                  <Speaker who={line.who} />
                  <div>{line.text}</div>
                </div>
              ))}
              <div className="mono dim" style={{ fontSize: 11, textAlign: "center", marginTop: 8, padding: "8px 0" }}>
                … 136 turnos más en el archivo …
              </div>
            </div>
          </div>
        ) : (
          <div className="fv-body fv-text">
            <div className="ln">
              {rawLines.map((_, i) => <div key={i}>{i + 1}</div>)}
            </div>
            <div>
              {rawLines.map((raw, i) => {
                let cls = "lc";
                let tag: React.ReactNode = null;
                let l = raw;
                if (l.startsWith("[IAGO]"))  { cls += " spk-iago";  tag = <span className="tag iago">IAGO</span>;  l = l.slice(6).trim(); }
                if (l.startsWith("[MARIA]")) { cls += " spk-maria"; tag = <span className="tag maria">MARIA</span>; l = l.slice(7).trim(); }
                if (l.startsWith("#")) cls = "lc";
                return (
                  <div key={i} className={cls} style={{ color: l.startsWith("#") ? "var(--text-mute)" : undefined }}>
                    {tag}{l || " "}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <div className="col gap-8">
        <Panel title="Métricas del guion">
          <div className="col gap-4 mono" style={{ fontSize: 13 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="muted">Palabras totales</span><span>9 842</span>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="muted">Turnos</span><span>142</span>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="muted">Balance Iago/María</span>
              <span style={{ color: "var(--ok)" }}>48% / 52%</span>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="muted">Duración estimada</span><span>11:08</span>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="muted">Coste generación</span><span>0.198€</span>
            </div>
            <div className="row" style={{ justifyContent: "space-between", borderTop: "1px solid var(--border)", paddingTop: 8, marginTop: 4 }}>
              <span className="muted">Modificado</span><span>hoy 12:11</span>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="muted">SHA</span><span style={{ color: "var(--text-dim)" }}>a4e1f8c</span>
            </div>
          </div>
        </Panel>
        <Panel title="Acciones">
          <div className="col gap-3">
            <Btn icon={<Icon name="prompt" size={11} />}
                 onClick={() => onOpenAI({ target: `Guion ${epId}`, purpose: "improve",
                                           hint: "regenerar preservando tono" })}>
              Regenerar (preservar tono)
            </Btn>
            <Btn kind="ghost" icon={<Icon name="check" size={11} />}
                 onClick={() => onOpenAI({ target: `Guion ${epId}`, purpose: "improve",
                                           hint: "validación dual Claude vs GPT" })}>
              Validar con GPT (dual)
            </Btn>
            <Btn kind="ghost" icon={<Icon name="doc" size={11} />}
                 onClick={() => window.open(`/files/${path}`, "_blank")}>
              Exportar .txt
            </Btn>
          </div>
        </Panel>
      </div>
    </div>
  );
}
