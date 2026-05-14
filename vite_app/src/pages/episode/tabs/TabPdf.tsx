// TabPdf — PDF fuente real del episodio (Fase 2). Embebe /files/<path>.
import { Icon, Panel } from "../../../components";

export interface TabPdfProps {
  path: string | null;
}

export function TabPdf({ path }: TabPdfProps) {
  if (!path) {
    return (
      <Panel title="PDF fuente">
        <div className="mono dim" style={{ fontSize: 12, padding: "24px 0", textAlign: "center" }}>
          No se encontró el PDF fuente de este episodio en el repo.
        </div>
      </Panel>
    );
  }
  const url = `/files/${path}`;
  return (
    <div className="fv">
      <div className="fv-chrome">
        <Icon name="doc" size={11} />
        <span className="fv-path">{path}</span>
        <span className="fill" />
        <a href={url} target="_blank" rel="noopener" className="btn ghost sm"
           title="Abrir en nueva pestaña" style={{ textDecoration: "none" }}>
          <Icon name="folder" size={11} />
        </a>
      </div>
      <div style={{ background: "#525659" }}>
        <iframe
          src={`${url}#view=FitH&toolbar=1&navpanes=0`}
          style={{ width: "100%", height: 720, border: 0, display: "block" }}
          title={`PDF · ${path}`}
        />
      </div>
    </div>
  );
}
