// Enlaza un elemento de la app con los archivos del repo que lo implementan.
import { ghLink, REPO_REF } from "../lib/nav";
import { Icon } from "./Icon";

export interface SourcePillsProps {
  files?: string[];
  label?: string;
}

function labelOf(path: string): string {
  if (path.endsWith("/")) return "DIR";
  if (path.endsWith(".py")) return "PY";
  if (path.endsWith(".md")) return "MD";
  if (path.endsWith(".json")) return "JSON";
  return "FILE";
}

export function SourcePills({ files, label = "Implementado en" }: SourcePillsProps) {
  if (!files || !files.length) return null;
  return (
    <div className="src-strip">
      <span className="src-strip-label">
        <Icon name="folder" size={10} /> {label}
      </span>
      {files.map((f) => (
        <a key={f} href={ghLink(f)} target="_blank" rel="noopener"
           className="src-pill" title={`Abrir ${f} en GitHub`}>
          <span className="kind">{labelOf(f)}</span>
          {f}
          <span className="gh">↗</span>
        </a>
      ))}
      <span style={{ marginLeft: "auto", color: "var(--text-mute)", fontSize: 10, letterSpacing: "0.08em" }}>
        bakero/maquinaria-pesada @ {REPO_REF}
      </span>
    </div>
  );
}
