import { Btn, Icon, Panel, SourceTitle, StatusDot } from "../../../components";
import type { OpenFixFn } from "../types";

export interface TabAudioProps {
  epId: string;
  onOpenFix: OpenFixFn;
}

export function TabAudio({ epId, onOpenFix }: TabAudioProps) {
  return (
    <div className="grid gap-8" style={{ gridTemplateColumns: "1.4fr 1fr" }}>
      <Panel title={<SourceTitle kind="audio" epId={epId} />} meta="ElevenLabs eleven_v3 · 4.8 MB">
        <div className="col gap-8">
          {/* Waveform mock */}
          <div style={{
            background: "#0A0A0A",
            border: "1px solid var(--border)",
            padding: "20px 16px",
            position: "relative",
            height: 120,
            display: "flex",
            alignItems: "center",
            gap: 1,
          }}>
            {Array.from({ length: 90 }).map((_, i) => {
              const isFail = i > 60;
              const h = isFail ? 4 : 12 + Math.abs(Math.sin(i * 0.4)) * 60 + Math.random() * 16;
              return (
                <div key={i} style={{
                  flex: 1,
                  height: `${h}px`,
                  background: isFail ? "var(--alert)" : "var(--y)",
                  opacity: isFail ? 0.5 : 0.85,
                }} />
              );
            })}
            <div style={{
              position: "absolute",
              left: "67%", top: 0, bottom: 0,
              width: 1, background: "var(--alert)",
            }} />
            <div style={{
              position: "absolute",
              left: "calc(67% + 6px)",
              top: 8,
              background: "var(--alert)",
              color: "#fff",
              fontFamily: "var(--f-mono)",
              fontSize: 9,
              padding: "2px 6px",
              letterSpacing: "0.1em",
            }}>FALLO @ 03:14</div>
          </div>

          <div className="row" style={{ justifyContent: "space-between" }}>
            <div className="row gap-4">
              <Btn sm onClick={() => window.open(`/files/episodios/${epId}.mp3`, "_blank")}>
                <Icon name="play" size={11} /> Play
              </Btn>
              <span className="mono dim" style={{ fontSize: 11 }}>00:00 / 03:14 (truncado)</span>
            </div>
            <Btn sm kind="danger" onClick={() => onOpenFix({
              target: epId, error: "ElevenLabs 502 en bloque 4 · audio truncado en 03:14", id: epId,
            })}><Icon name="wrench" size={11} /> Arreglar</Btn>
          </div>

          {/* Blocks */}
          <div className="col gap-3">
            <div className="h3">Bloques generados</div>
            {[
              { n: 1, ok: true,  t: "0:00 → 0:42" },
              { n: 2, ok: true,  t: "0:42 → 2:10" },
              { n: 3, ok: true,  t: "2:10 → 3:14" },
              { n: 4, ok: false, t: "3:14 → 6:20", err: "ElevenLabs 502 · 2 reintentos" },
              { n: 5, ok: null,  t: "—" },
              { n: 6, ok: null,  t: "—" },
              { n: 7, ok: null,  t: "—" },
            ].map((b) => (
              <div key={b.n} className="row" style={{
                padding: "6px 10px",
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                borderLeft: b.ok === false ? "2px solid var(--alert)" : b.ok ? "2px solid var(--ok)" : "2px solid var(--border-2)",
                fontFamily: "var(--f-mono)",
                fontSize: 11,
              }}>
                <span style={{ width: 24, color: "var(--text-mute)" }}>{b.n.toString().padStart(2, "0")}</span>
                <span style={{ flex: 1 }}>{b.t}</span>
                {b.err && <span style={{ color: "var(--alert)" }}>{b.err}</span>}
                <StatusDot status={b.ok === false ? "alert" : b.ok ? "ok" : "empty"} sm />
              </div>
            ))}
          </div>
        </div>
      </Panel>

      <Panel title="Configuración de voz">
        <div className="col gap-4">
          <div>
            <div className="h3 mb-4">Iago</div>
            <div className="mono dim" style={{ fontSize: 11 }}>voice_id: pNInz6obpgDQGcFmaJgB</div>
            <div className="mono" style={{ fontSize: 11, color: "var(--iago)" }}>stability 0.65 · similarity 0.78</div>
          </div>
          <div>
            <div className="h3 mb-4">María</div>
            <div className="mono dim" style={{ fontSize: 11 }}>voice_id: EXAVITQu4vr4xnSDxMaL</div>
            <div className="mono" style={{ fontSize: 11, color: "var(--maria)" }}>stability 0.72 · similarity 0.81</div>
          </div>
          <div style={{ borderTop: "1px solid var(--border)", paddingTop: 10, marginTop: 4 }}>
            <div className="mono dim" style={{ fontSize: 11 }}>Saldo ElevenLabs</div>
            <div className="mono" style={{ fontSize: 16, color: "var(--warn)" }}>8.40€</div>
            <div className="mono dim" style={{ fontSize: 10 }}>recargar antes de 10.00€</div>
          </div>
        </div>
      </Panel>
    </div>
  );
}
