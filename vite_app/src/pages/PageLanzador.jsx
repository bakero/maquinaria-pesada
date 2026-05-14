// PageLanzador — extraído del monolito (Fase 1b).
import * as React from "react";
import { Btn, Icon, Panel, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";
import { PIPELINE_FORMS } from "./fixtures";

function PageLanzador({ onNav, onOpenAI }) {
  const ids = Object.keys(PIPELINE_FORMS);
  const [sel, setSel] = React.useState(ids[0]);
  const [vals, setVals] = React.useState({});
  const [copied, setCopied] = React.useState(false);
  const [running, setRunning] = React.useState(false);
  const [output, setOutput] = React.useState([]);

  const form = PIPELINE_FORMS[sel];

  // Reset values when changing pipeline
  React.useEffect(() => {
    const init = {};
    form.fields.forEach(f => { init[f.flag] = f.default; });
    setVals(init);
    setOutput([]);
  }, [sel]);

  const update = (flag, v) => setVals((s) => ({ ...s, [flag]: v }));

  const cmd = (() => {
    const parts = [`python ${form.script}`];
    form.fields.forEach(f => {
      const v = vals[f.flag];
      if (f.kind === "bool") { if (v) parts.push(f.flag); }
      else if (v != null && v !== "") parts.push(`${f.flag} ${JSON.stringify(v).replace(/"/g, "")}`);
    });
    return parts.join(" \\\n  ");
  })();

  const copy = () => {
    navigator.clipboard?.writeText(cmd.replace(/\\\n  /g, " "));
    setCopied(true);
    setTimeout(() => setCopied(false), 1400);
  };

  const run = async () => {
    setRunning(true);
    setOutput([`$ ${cmd.replace(/\\\n  /g, " ")}`]);
    // Construye flags como pares [flag, value] para el backend
    const flags = [];
    form.fields.forEach(f => {
      const v = vals[f.flag];
      if (f.kind === "bool") { if (v) flags.push([f.flag, true]); }
      else if (v != null && v !== "") flags.push([f.flag, v]);
    });
    try {
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ script: form.script, flags }),
      });
      const data = await res.json();
      if (data.ok) {
        setOutput((o) => [...o,
          `[${new Date().toLocaleTimeString()}] INFO  runner: lanzado en background`,
          `[${new Date().toLocaleTimeString()}] INFO  pid=${data.pid} log=${data.log}`,
          `[${new Date().toLocaleTimeString()}] INFO  consulta el log en logs/${data.log}`,
        ]);
      } else {
        setOutput((o) => [...o, `[error] ${data.error || "no se pudo lanzar"}`]);
      }
    } catch (e) {
      setOutput((o) => [...o, `[offline] ${e.message || e} — usa la cabina Streamlit`]);
    }
    setRunning(false);
  };

  return (
    <div className="content">
      <PageHeader
        title="Lanzador de pipelines"
        sub="Rellena el formulario y genera el comando · ejecuta localmente o copia a Codex"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: `Pipeline · ${form.script}`, purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Mejorar con IA</Btn>
        }
      />
      <SourcePills files={srcFor("lanzador")}/>

      <div className="grid gap-8" style={{ gridTemplateColumns: "1fr 1.2fr" }}>
        {/* LEFT — pipeline selector + form */}
        <div className="col gap-8">
          <Panel title={<span><Icon name="prompt" size={12}/> &nbsp;Pipeline</span>}>
            <div className="col gap-3">
              {ids.map((id) => (
                <div key={id}
                     onClick={() => setSel(id)}
                     style={{
                       padding: "8px 10px",
                       border: "1px solid",
                       borderColor: sel === id ? "var(--y)" : "var(--border)",
                       background: sel === id ? "var(--y-soft)" : "var(--panel-2)",
                       cursor: "pointer",
                     }}>
                  <div className="display" style={{
                    fontSize: 12, letterSpacing: "0.06em",
                    color: sel === id ? "var(--y)" : "var(--text)",
                  }}>{id}</div>
                  <div className="mono dim" style={{ fontSize: 10, marginTop: 2 }}>
                    {PIPELINE_FORMS[id].script}
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel
            title={<span><Icon name="settings" size={12}/> &nbsp;Parámetros</span>}
            meta={form.script}
          >
            <div className="mono dim mb-12" style={{ fontSize: 11, lineHeight: 1.5 }}>
              {form.description}
            </div>
            <div className="col gap-4">
              {form.fields.map((f) => (
                <div key={f.flag}>
                  <div className="row" style={{ justifyContent: "space-between", marginBottom: 4 }}>
                    <span className="display" style={{ fontSize: 11, letterSpacing: "0.08em", color: "var(--text-dim)" }}>
                      {f.label}{f.required && <span style={{ color: "var(--alert)" }}> *</span>}
                    </span>
                    <span className="mono" style={{ fontSize: 10, color: "var(--y)" }}>{f.flag}</span>
                  </div>
                  {f.kind === "bool" ? (
                    <div className="row gap-3">
                      {[true, false].map((b) => (
                        <button key={String(b)}
                                className={`btn sm ${vals[f.flag] === b ? "primary" : ""}`}
                                onClick={() => update(f.flag, b)}
                                style={{ flex: 1 }}>
                          {b ? "Sí" : "No"}
                        </button>
                      ))}
                    </div>
                  ) : f.kind === "select" ? (
                    <select className="ai-input" value={vals[f.flag] ?? ""}
                            onChange={(e) => update(f.flag, e.target.value)}
                            style={{ width: "100%" }}>
                      {f.options.map(o => <option key={o} value={o}>{o}</option>)}
                    </select>
                  ) : (
                    <input className="ai-input" value={vals[f.flag] ?? ""}
                           onChange={(e) => update(f.flag, e.target.value)}
                           placeholder={f.placeholder}
                           style={{ width: "100%" }}/>
                  )}
                  {f.help && <div className="mono" style={{ fontSize: 10, color: "var(--text-mute)", marginTop: 3 }}>{f.help}</div>}
                </div>
              ))}
            </div>
          </Panel>
        </div>

        {/* RIGHT — generated command + run */}
        <div className="col gap-8">
          <Panel
            title={<span><Icon name="doc" size={12}/> &nbsp;Comando generado</span>}
            meta="bash · listo para pegar"
            actions={
              <React.Fragment>
                <Btn sm kind="ghost" onClick={copy}>
                  {copied ? "Copiado ✓" : "Copiar"}
                </Btn>
                <Btn sm kind="primary" onClick={run} icon={<Icon name="play" size={10}/>}>
                  {running ? "Ejecutando…" : "Ejecutar"}
                </Btn>
              </React.Fragment>
            }
          >
            <pre className="code" style={{ borderLeftColor: "var(--y)", fontSize: 12.5, padding: "12px 14px" }}>
{cmd}
            </pre>
            <div className="row gap-4 mt-8 mono" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.08em" }}>
              <span>cwd: <span style={{ color: "var(--y)" }}>~/maquinaria-pesada</span></span>
              <span>·</span>
              <span>sandbox: workspace-write</span>
              <span>·</span>
              <span>timeout: 30m</span>
            </div>
          </Panel>

          <Panel
            title={<span><Icon name="log" size={12}/> &nbsp;Salida</span>}
            meta={running ? "streaming…" : output.length ? "finalizado" : "sin ejecutar"}
          >
            {output.length === 0 ? (
              <div className="mono dim" style={{ fontSize: 11, padding: "20px 0", textAlign: "center" }}>
                Pulsa <b style={{ color: "var(--y)" }}>Ejecutar</b> para lanzar el pipeline aquí.
              </div>
            ) : (
              <pre className="code" style={{ borderLeftColor: running ? "var(--info)" : "var(--ok)", maxHeight: 320, overflow: "auto" }}>
                {output.join("\n")}
                {running && <span className="ai-cursor"/>}
              </pre>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · FUENTES
// ════════════════════════════════════════════════════════════

export { PageLanzador };
