// PagePipeline — combina Conectores + Lanzador.

import * as React from "react";
import { PageHeader } from "../components";
import { PageConectores } from "./PageConectores";
import { PageLanzador } from "./PageLanzador";

export interface PagePipelineProps {
  onNav: (page: string, payload?: string) => void;
  onOpenAI: (ctx?: unknown) => void;
}

type Tab = "lanzar" | "conectores";

export function PagePipeline({ onNav, onOpenAI }: PagePipelineProps) {
  const [tab, setTab] = React.useState<Tab>("lanzar");
  return (
    <div className="page">
      <PageHeader
        title="Pipeline"
        sub="Lanza generadores y consulta el catálogo de conectores disponibles."
      />
      <div className="subnav">
        <button className={`subnav-item${tab === "lanzar" ? " active" : ""}`} onClick={() => setTab("lanzar")}>
          Lanzar pipeline
        </button>
        <button className={`subnav-item${tab === "conectores" ? " active" : ""}`} onClick={() => setTab("conectores")}>
          Conectores <span className="count">9</span>
        </button>
      </div>
      <div style={{ marginTop: -10 }}>
        {tab === "lanzar"     && <PageLanzador   onNav={onNav} onOpenAI={onOpenAI}/>}
        {tab === "conectores" && <PageConectores onNav={onNav} onOpenAI={onOpenAI}/>}
      </div>
    </div>
  );
}
