// Título de panel con la ruta explícita del archivo en disco.
import { SOURCES } from "../lib/sources";
import { Icon } from "./Icon";

export interface SourceTitleProps {
  kind: string;
  epId: string;
  customPath?: string;
}

export function SourceTitle({ kind, epId, customPath }: SourceTitleProps) {
  const src = SOURCES[kind];
  const path = customPath || (src ? `${src.folder}${epId}${src.ext}` : "");
  return (
    <span className="row gap-4" style={{ alignItems: "baseline" }}>
      <Icon name={src ? src.icon : "doc"} size={12} />
      <span>{src ? src.label : kind}</span>
      <span style={{
        marginLeft: 8,
        fontFamily: "var(--f-mono)",
        fontSize: 11,
        fontWeight: 400,
        letterSpacing: 0,
        textTransform: "none",
        color: "var(--y)",
        background: "var(--y-soft)",
        padding: "2px 8px",
        border: "1px solid rgba(245,196,0,0.3)",
        borderRadius: 2,
      }}>
        {path}
      </span>
    </span>
  );
}
