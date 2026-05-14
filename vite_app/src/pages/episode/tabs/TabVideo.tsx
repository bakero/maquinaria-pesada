// TabVideo — vídeo real del episodio (Fase 2). Reproduce /files/<path>.
import { Btn, Icon, Panel } from "../../../components";
import type { NavFn } from "../types";

export interface TabVideoProps {
  path: string | null;
  onNav: NavFn;
}

export function TabVideo({ path, onNav }: TabVideoProps) {
  return (
    <Panel title={<span><Icon name="play" size={12} /> &nbsp;Vídeo{path ? ` · ${path}` : ""}</span>}
           meta={path ? "" : "pendiente"}>
      {path ? (
        <div style={{ background: "#000", border: "1px solid var(--border)" }}>
          <video
            src={`/files/${path}`}
            controls
            preload="metadata"
            style={{ width: "100%", aspectRatio: "16/9", display: "block", background: "#000" }}
          />
        </div>
      ) : (
        <div style={{
          background: "#0A0A0A",
          border: "1px dashed var(--border-2)",
          padding: 60,
          textAlign: "center",
        }}>
          <div className="display" style={{ fontSize: 14, color: "var(--text-mute)", letterSpacing: "0.16em" }}>
            VÍDEO NO GENERADO
          </div>
          <div className="mono dim" style={{ fontSize: 11, marginTop: 8 }}>
            Requiere audio finalizado primero.
          </div>
          <div className="mt-12">
            <Btn sm icon={<Icon name="play" size={11} />}
                 onClick={() => onNav("lanzador")}>Lanzar generación</Btn>
          </div>
        </div>
      )}
    </Panel>
  );
}
