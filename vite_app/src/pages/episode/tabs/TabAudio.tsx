// TabAudio — audio real del episodio (Fase 2). Reproduce /files/<path>.
import { Btn, Icon, Panel, SourceTitle } from "../../../components";
import type { OpenFixFn } from "../types";

export interface TabAudioProps {
  epId: string;
  path: string | null;
  onOpenFix: OpenFixFn;
}

export function TabAudio({ epId, path, onOpenFix }: TabAudioProps) {
  return (
    <Panel title={<SourceTitle kind="audio" epId={epId} customPath={path || undefined} />}
           meta={path ? "" : "no generado"}>
      {path ? (
        <div className="col gap-8">
          <div style={{
            background: "#0A0A0A", padding: "24px 20px",
            border: "1px solid var(--border)", borderLeft: "3px solid var(--y)",
          }}>
            <audio
              src={`/files/${path}`}
              controls
              preload="metadata"
              style={{ width: "100%", filter: "invert(0.92) hue-rotate(180deg)" }}
            />
          </div>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <a href={`/files/${path}`} download className="btn sm ghost" style={{ textDecoration: "none" }}>
              <Icon name="folder" size={11} /> Descargar MP3
            </a>
            <Btn sm kind="danger" onClick={() => onOpenFix({
              target: epId, error: `Revisar audio de ${epId}`, id: epId,
            })}><Icon name="wrench" size={11} /> Arreglar con Claude</Btn>
          </div>
        </div>
      ) : (
        <div className="mono dim" style={{ fontSize: 12, padding: "24px 0", textAlign: "center" }}>
          Audio no generado. Requiere guion validado primero.
        </div>
      )}
    </Panel>
  );
}
