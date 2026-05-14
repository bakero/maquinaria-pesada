// PageFuentes — extraído del monolito (Fase 1b).
import * as React from "react";
import { Btn, Icon, Panel, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";
import { CONNECTORS, SOURCE_ITEMS, LOG_LINES } from "./fixtures";

function PageFuentes({ onNav, onOpenAI }) {
  const [src, setSrc] = React.useState("pdfs");
  const [filter, setFilter] = React.useState("");
  const [picked, setPicked] = React.useState(null);

  const source = CONNECTORS.source.find(s => s.id === src);
  const items = (SOURCE_ITEMS[src] || []).filter(it => it.name.toLowerCase().includes(filter.toLowerCase()));

  React.useEffect(() => { setPicked(items[0] || null); }, [src]);

  return (
    <div className="content">
      <PageHeader
        title="Fuentes de contenido"
        sub="Filesystem como única fuente de verdad · PDFs, guiones, escaletas, audio, vídeo, logs"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: `Fuentes · ${picked?.name}`, purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Analizar con IA</Btn>
        }
      />
      <SourcePills files={srcFor("fuentes")}/>

      {/* Source-type picker */}
      <div className="row gap-3 mb-12" style={{ flexWrap: "wrap" }}>
        {CONNECTORS.source.map((s) => (
          <div key={s.id}
               className={`btn sm ${src === s.id ? "primary" : ""}`}
               onClick={() => setSrc(s.id)}
               style={{ cursor: "pointer" }}>
            <Icon name={s.icon} size={10}/>
            {s.label}
            <span className="mono" style={{
              fontSize: 9, padding: "1px 5px",
              background: src === s.id ? "rgba(0,0,0,0.2)" : "var(--panel-2)",
              color: src === s.id ? "#0D0D0D" : "var(--text-mute)",
              borderRadius: 2,
            }}>{(SOURCE_ITEMS[s.id] || []).length}</span>
          </div>
        ))}
      </div>

      <div className="grid gap-8" style={{ gridTemplateColumns: "360px 1fr" }}>
        {/* LEFT — file list */}
        <Panel
          title={<span><Icon name="folder" size={12}/> &nbsp;{source.folder}</span>}
          meta={`${items.length}/${(SOURCE_ITEMS[src] || []).length}`}
        >
          <input className="ai-input mb-8" placeholder="Filtrar por nombre…"
                 value={filter} onChange={(e) => setFilter(e.target.value)}
                 style={{ width: "100%" }}/>
          <div className="col gap-2" style={{ maxHeight: 480, overflowY: "auto" }}>
            {items.map((it) => (
              <div key={it.name}
                   onClick={() => setPicked(it)}
                   style={{
                     padding: "8px 10px",
                     borderTop:    `1px solid ${picked?.name === it.name ? "var(--y)" : "var(--border)"}`,
                     borderRight:  `1px solid ${picked?.name === it.name ? "var(--y)" : "var(--border)"}`,
                     borderBottom: `1px solid ${picked?.name === it.name ? "var(--y)" : "var(--border)"}`,
                     borderLeft:   it.err ? "3px solid var(--alert)"
                                : picked?.name === it.name ? "3px solid var(--y)"
                                : "1px solid var(--border)",
                     background: picked?.name === it.name ? "var(--y-soft)" : "var(--panel-2)",
                     cursor: "pointer",
                   }}>
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <span className="mono" style={{
                    fontSize: 12,
                    color: picked?.name === it.name ? "var(--y)" : "var(--text)",
                    wordBreak: "break-all",
                  }}>{it.name}</span>
                </div>
                <div className="row gap-3 mt-2 mono" style={{ fontSize: 10, color: "var(--text-mute)" }}>
                  <span>{it.size}</span>
                  <span>·</span>
                  <span>{it.t}</span>
                  {it.err && <span style={{ color: "var(--alert)", marginLeft: "auto" }}>{it.err}</span>}
                </div>
              </div>
            ))}
            {!items.length && <div className="mono dim" style={{ fontSize: 11, padding: 16, textAlign: "center" }}>
              Sin items que coincidan.
            </div>}
          </div>
        </Panel>

        {/* RIGHT — viewer */}
        <Panel
          title={picked ? <span><Icon name={source.icon} size={12}/> &nbsp;{picked.name}</span>
                        : <span>Selecciona un archivo</span>}
          meta={picked ? `${picked.size} · ${picked.t}` : ""}
        >
          {picked ? (
            <div className="col gap-8">
              <div className="row gap-4">
                <div style={{ flex: 1 }}>
                  <div className="display" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.16em" }}>RUTA</div>
                  <div className="mono" style={{ fontSize: 12, color: "var(--y)", marginTop: 4 }}>{source.folder}{picked.name}</div>
                </div>
                <Btn sm kind="ghost" icon={<Icon name="folder" size={10}/>}
                     onClick={() => fetch("/api/reveal", {
                       method: "POST",
                       headers: { "Content-Type": "application/json" },
                       body: JSON.stringify({ path: source.folder + picked.name }),
                     }).catch(() => {})}>
                  Revelar
                </Btn>
                <Btn sm icon={<Icon name="doc" size={10}/>}
                     onClick={() => window.open(`/files/${source.folder}${picked.name}`, "_blank")}>
                  Descargar
                </Btn>
              </div>

              {/* Preview placeholder per source type */}
              {src === "pdfs" && (
                picked.url ? (
                  <div style={{ background: "#525659", border: "1px solid var(--border)" }}>
                    <iframe
                      key={picked.url}
                      src={picked.url + "#view=FitH&toolbar=1"}
                      style={{ width: "100%", height: 600, border: 0, display: "block" }}
                      title={picked.name}
                    />
                  </div>
                ) : (
                  <div style={{
                    background: "#F4EFE3", color: "#2A2620", padding: "40px 56px",
                    fontFamily: "Georgia, serif", fontSize: 13, lineHeight: 1.6, minHeight: 280,
                    position: "relative",
                  }}>
                    <div style={{ fontWeight: 700, textTransform: "uppercase", marginBottom: 14, letterSpacing: "0.02em" }}>
                      {picked.name.replace(".pdf", "")} · Resumen temático
                    </div>
                    <div style={{ opacity: 0.7 }}>
                      Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor
                      incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
                      nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
                    </div>
                    <div style={{
                      position: "absolute", top: 10, right: 14,
                      fontFamily: "var(--f-mono)", fontSize: 10, color: "rgba(0,0,0,0.4)",
                      letterSpacing: "0.1em",
                    }}>
                      preview · archivo no disponible localmente
                    </div>
                  </div>
                )
              )}
              {(src === "guiones" || src === "escaletas") && (
                <pre className="code" style={{ maxHeight: 320, overflow: "auto" }}>
{src === "guiones"
? `# ${picked.name}
# generado: ${picked.t}
# encoding: utf-8

[IAGO] Vale María, hoy nos metemos con...
[MARIA] Buena pregunta. Lo bonito es que...
[IAGO] Vamos a desglosarlo: query, key, value.
...`
: `# ${picked.name.replace(".md","")}
> ${picked.size} · ${picked.t}

## 01 · Apertura
- tiempo: \`0:00 → 0:42\`
- palabras: 320
- contenido: saludo, contexto, conexión con módulo anterior.

## 02 · El problema
- tiempo: \`0:42 → 2:10\`
- palabras: 680
...`}
                </pre>
              )}
              {src === "episodios" && (
                <div className="col gap-4">
                  {picked.url ? (
                    <div style={{ background: "#0A0A0A", padding: 16, border: "1px solid var(--border)" }}>
                      <audio
                        key={picked.url}
                        src={picked.url}
                        controls
                        preload="metadata"
                        style={{ width: "100%", filter: "invert(0.92) hue-rotate(180deg)" }}
                      />
                    </div>
                  ) : (
                    <React.Fragment>
                      <div style={{ background: "#0A0A0A", padding: "20px 16px", height: 100, display: "flex", alignItems: "center", gap: 1 }}>
                        {Array.from({ length: 80 }).map((_, i) => (
                          <div key={i} style={{
                            flex: 1,
                            height: `${20 + Math.abs(Math.sin(i * 0.4)) * 50}px`,
                            background: picked.err && i > 50 ? "var(--alert)" : "var(--y)",
                            opacity: 0.8,
                          }}/>
                        ))}
                      </div>
                      <div className="row gap-3">
                        <Btn sm onClick={() => window.open(`/files/${source.folder}${picked.name}`, "_blank")}>
                          <Icon name="play" size={11}/> Play
                        </Btn>
                        <span className="mono dim" style={{ fontSize: 11 }}>{picked.name}</span>
                      </div>
                    </React.Fragment>
                  )}
                </div>
              )}
              {src === "video" && (
                picked.url ? (
                  <div style={{ background: "#000", border: "1px solid var(--border)" }}>
                    <video
                      key={picked.url}
                      src={picked.url}
                      controls
                      preload="metadata"
                      style={{ width: "100%", aspectRatio: "16/9", display: "block" }}
                    />
                  </div>
                ) : (
                  <div style={{
                    background: "#0A0A0A", aspectRatio: "16/9",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    border: "1px dashed var(--border-2)",
                  }}>
                    <div className="col gap-3" style={{ textAlign: "center" }}>
                      <Icon name="play" size={28}/>
                      <div className="mono dim" style={{ fontSize: 11 }}>{picked.size} · archivo no cacheado</div>
                    </div>
                  </div>
                )
              )}
              {src === "logs" && (
                <pre className="code" style={{ maxHeight: 320, overflow: "auto", fontSize: 11 }}>
{LOG_LINES.slice(0, 8).join("\n")}
...
                </pre>
              )}
            </div>
          ) : (
            <div className="mono dim" style={{ textAlign: "center", padding: 40, fontSize: 12 }}>
              Sin selección.
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · PREVISUALIZAR (Player)
// ════════════════════════════════════════════════════════════

export { PageFuentes };
