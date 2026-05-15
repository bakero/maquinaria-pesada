// PageRecursos — combina Fuentes + Previsualizar + Pizarra + Mapa.

import * as React from "react";
import { PageHeader } from "../components";
import { PageFuentes } from "./PageFuentes";
import { PagePlayer } from "./PagePlayer";
import { PagePizarra } from "./PagePizarra";
import { PageMapa } from "./PageMapa";

export interface PageRecursosProps {
  onNav: (page: string, payload?: string) => void;
  onOpenAI: (ctx?: unknown) => void;
}

type Tab = "fuentes" | "player" | "pizarra" | "mapa";

export function PageRecursos({ onNav, onOpenAI }: PageRecursosProps) {
  const [tab, setTab] = React.useState<Tab>("fuentes");
  return (
    <div className="page">
      <PageHeader
        title="Recursos"
        sub="PDFs fuente, audios y vídeos producidos, pizarra de notas y mapa de componentes."
      />
      <div className="subnav">
        <button className={`subnav-item${tab === "fuentes" ? " active" : ""}`} onClick={() => setTab("fuentes")}>
          Fuentes
        </button>
        <button className={`subnav-item${tab === "player" ? " active" : ""}`} onClick={() => setTab("player")}>
          Previsualizar
        </button>
        <button className={`subnav-item${tab === "pizarra" ? " active" : ""}`} onClick={() => setTab("pizarra")}>
          Pizarra
        </button>
        <button className={`subnav-item${tab === "mapa" ? " active" : ""}`} onClick={() => setTab("mapa")}>
          Mapa
        </button>
      </div>
      <div style={{ marginTop: -10 }}>
        {tab === "fuentes" && <PageFuentes onNav={onNav} onOpenAI={onOpenAI}/>}
        {tab === "player"  && <PagePlayer  onNav={onNav} onOpenAI={onOpenAI}/>}
        {tab === "pizarra" && <PagePizarra onNav={onNav} onOpenAI={onOpenAI}/>}
        {tab === "mapa"    && <PageMapa    onNav={onNav} onOpenAI={onOpenAI}/>}
      </div>
    </div>
  );
}
