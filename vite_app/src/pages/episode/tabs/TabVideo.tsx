import { Btn, Icon, Panel, SourceTitle } from "../../../components";
import type { NavFn } from "../types";

export interface TabVideoProps {
  epId: string;
  onNav: NavFn;
}

export function TabVideo({ epId, onNav }: TabVideoProps) {
  return (
    <Panel title={<SourceTitle kind="video" epId={epId} />} meta="Kling · pendiente">
      <div style={{
        background: "#0A0A0A",
        border: "1px dashed var(--border-2)",
        padding: 60,
        textAlign: "center",
      }}>
        <div className="display" style={{ fontSize: 14, color: "var(--text-mute)", letterSpacing: "0.16em" }}>VÍDEO NO GENERADO</div>
        <div className="mono dim" style={{ fontSize: 11, marginTop: 8 }}>Requiere audio finalizado primero · bloqueado por bloque 4</div>
        <div className="mt-12">
          <Btn sm icon={<Icon name="play" size={11} />}
               onClick={() => onNav("lanzador")}>Lanzar generación</Btn>
        </div>
      </div>
    </Panel>
  );
}
