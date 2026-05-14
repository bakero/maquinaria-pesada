// PagePlayer — extraído del monolito (Fase 1b).
import * as React from "react";
import { Btn, Icon, Panel, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";
import { SOURCE_ITEMS } from "./fixtures";

function PagePlayer({ onNav, onOpenAI }) {
  const [tab, setTab] = React.useState("audio");
  const items = tab === "audio" ? SOURCE_ITEMS.episodios : SOURCE_ITEMS.video;
  const [pick, setPick] = React.useState(items[0]?.name);
  React.useEffect(() => { setPick((tab === "audio" ? SOURCE_ITEMS.episodios : SOURCE_ITEMS.video)[0]?.name); }, [tab]);

  const sel = items.find(i => i.name === pick) || items[0];

  return (
    <div className="content">
      <PageHeader
        title="Previsualizar"
        sub="Audio y vídeo generados · escucha y revisa antes de publicar"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: `Preview · ${sel?.name}`, purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Sugerir checks</Btn>
        }
      />
      <SourcePills files={srcFor("player")}/>

      <div className="tabs mb-12">
        {[{ id: "audio", icon: "play", label: "Audio" }, { id: "video", icon: "play", label: "Vídeo" }].map((t) => (
          <div key={t.id} className={`tab ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
            <Icon name={t.icon} size={11}/>
            {t.label}
            <span className="badge" style={{ marginLeft: 4 }}>{tab === "audio" ? SOURCE_ITEMS.episodios.length : SOURCE_ITEMS.video.length}</span>
          </div>
        ))}
      </div>

      <div className="grid gap-8" style={{ gridTemplateColumns: "280px 1fr" }}>
        <Panel title={<span><Icon name="folder" size={12}/> &nbsp;Cola</span>} noPad>
          <div className="col gap-2" style={{ padding: 10 }}>
            {items.map((it) => (
              <div key={it.name}
                   onClick={() => setPick(it.name)}
                   style={{
                     padding: "8px 10px",
                     borderTop:    `1px solid ${pick === it.name ? "var(--y)" : "var(--border)"}`,
                     borderRight:  `1px solid ${pick === it.name ? "var(--y)" : "var(--border)"}`,
                     borderBottom: `1px solid ${pick === it.name ? "var(--y)" : "var(--border)"}`,
                     borderLeft:   it.err ? "3px solid var(--alert)"
                                : pick === it.name ? "3px solid var(--y)"
                                : "1px solid var(--border)",
                     background: pick === it.name ? "var(--y-soft)" : "var(--panel-2)",
                     cursor: "pointer",
                   }}>
                <div className="mono" style={{ fontSize: 12, color: pick === it.name ? "var(--y)" : "var(--text)" }}>{it.name}</div>
                <div className="mono dim" style={{ fontSize: 10, marginTop: 2 }}>{it.size} · {it.t}</div>
                {it.err && <div className="mono" style={{ fontSize: 10, color: "var(--alert)", marginTop: 2 }}>{it.err}</div>}
              </div>
            ))}
          </div>
        </Panel>

        <Panel
          title={<span><Icon name="play" size={12}/> &nbsp;{sel?.name}</span>}
          meta={`${sel?.size} · ${sel?.t}`}
        >
          {tab === "audio" ? (
            <div className="col gap-8">
              {sel?.url ? (
                <div style={{
                  background: "#0A0A0A", padding: "24px 20px", border: "1px solid var(--border)",
                  borderLeft: "3px solid var(--y)",
                }}>
                  {/* Waveform decorative */}
                  <div style={{ position: "relative", height: 80, display: "flex", alignItems: "center", gap: 1, marginBottom: 16 }}>
                    {Array.from({ length: 120 }).map((_, i) => {
                      const h = 12 + Math.abs(Math.sin(i * 0.32)) * 60 + (i % 3) * 6;
                      return (
                        <div key={i} style={{
                          flex: 1, height: `${h}px`,
                          background: "var(--y)", opacity: 0.6,
                        }}/>
                      );
                    })}
                  </div>
                  <audio
                    key={sel.url}
                    src={sel.url}
                    controls
                    preload="metadata"
                    style={{ width: "100%", filter: "invert(0.92) hue-rotate(180deg)" }}
                  />
                </div>
              ) : (
                <div style={{
                  background: "#0A0A0A", padding: "24px 16px", position: "relative",
                  height: 160, display: "flex", alignItems: "center", gap: 1,
                }}>
                  {Array.from({ length: 120 }).map((_, i) => {
                    const fail = sel?.err && i > 80;
                    const h = fail ? 6 : 16 + Math.abs(Math.sin(i * 0.32)) * 80 + (i % 3) * 8;
                    return (
                      <div key={i} style={{
                        flex: 1, height: `${h}px`,
                        background: fail ? "var(--alert)" : "var(--y)",
                        opacity: fail ? 0.5 : 0.85,
                      }}/>
                    );
                  })}
                  <div style={{ position: "absolute", left: "30%", top: 0, bottom: 0, width: 1, background: "var(--y)" }}/>
                  <div style={{
                    position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center",
                    background: "rgba(13,13,13,0.7)",
                  }}>
                    <div className="mono" style={{ fontSize: 11, color: "var(--text-mute)", letterSpacing: "0.16em" }}>
                      ARCHIVO NO CACHEADO LOCALMENTE
                    </div>
                  </div>
                </div>
              )}

              <div className="row" style={{ justifyContent: "space-between" }}>
                <div className="row gap-4">
                  <span className="mono dim" style={{ fontSize: 12 }}>
                    {sel?.url ? "▶ controles HTML5 nativos" : (sel?.err ? "03:14 (truncado)" : "—")}
                  </span>
                </div>
                {sel?.url && (
                  <a href={sel.url} download={sel.name} className="btn sm ghost" style={{ textDecoration: "none" }}>
                    <Icon name="folder" size={11}/> Descargar MP3
                  </a>
                )}
              </div>

              {/* Spec checks */}
              <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
                {[
                  { label: "LUFS",      v: "-15.8", ok: true },
                  { label: "Duración",  v: sel?.err ? "03:14" : "11:08", ok: !sel?.err },
                  { label: "Silencios", v: sel?.err ? "1 (4.2s)" : "0", ok: !sel?.err },
                ].map((s) => (
                  <div key={s.label} className="panel" style={{ padding: "10px 12px", borderLeft: `3px solid ${s.ok ? "var(--ok)" : "var(--alert)"}` }}>
                    <div className="display" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.14em" }}>{s.label}</div>
                    <div className="mono" style={{ fontSize: 18, color: s.ok ? "var(--ok)" : "var(--alert)", marginTop: 4 }}>{s.v}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="col gap-8">
              {sel?.url ? (
                <div style={{ background: "#000", border: "1px solid var(--border)", borderLeft: "3px solid var(--y)" }}>
                  <video
                    key={sel.url}
                    src={sel.url}
                    controls
                    preload="metadata"
                    style={{ width: "100%", aspectRatio: "16/9", display: "block", background: "#000" }}
                  />
                </div>
              ) : (
                <div style={{
                  background: "#0A0A0A", aspectRatio: "16/9",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  position: "relative", border: "1px dashed var(--border-2)",
                }}>
                  <div style={{ position: "absolute", inset: 12, border: "1px solid var(--border)", opacity: 0.4 }}/>
                  <div className="col gap-3" style={{ textAlign: "center" }}>
                    <div style={{ width: 64, height: 64, borderRadius: "50%", background: "var(--y)",
                                  display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto" }}>
                      <span style={{ color: "#0D0D0D", fontSize: 24, marginLeft: 4 }}>▶</span>
                    </div>
                    <div className="mono dim" style={{ fontSize: 11 }}>{sel?.size} · archivo no cacheado</div>
                    {sel?.err && <div className="mono" style={{ fontSize: 11, color: "var(--alert)" }}>{sel.err}</div>}
                  </div>
                </div>
              )}

              <div className="row" style={{ justifyContent: "space-between" }}>
                <span className="mono dim" style={{ fontSize: 12 }}>
                  {sel?.url ? "▶ controles HTML5 nativos · 1920×1080" : "—"}
                </span>
                {sel?.url && (
                  <a href={sel.url} download={sel.name} className="btn sm ghost" style={{ textDecoration: "none" }}>
                    <Icon name="folder" size={11}/> Descargar MP4
                  </a>
                )}
              </div>
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · LOGS
// ════════════════════════════════════════════════════════════

export { PagePlayer };
