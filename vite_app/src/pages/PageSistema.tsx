// PageSistema · combina conectores, lanzador, mapa, ajustes, fuentes.
// Espacio de referencia técnica + utilidades.

import * as React from "react";
import { PageConectores } from "./PageConectores";
import { PageLanzador } from "./PageLanzador";
import { PageMapa } from "./PageMapa";
import { PageAjustes } from "./PageAjustes";
import { PageFuentes } from "./PageFuentes";

export interface PageSistemaProps {
  onNav: (page: string, payload?: string) => void;
  onOpenAI: (ctx?: unknown) => void;
}

type Tab = "conectores" | "lanzador" | "fuentes" | "mapa" | "ajustes";

const TABS: { id: Tab; label: string }[] = [
  { id: "conectores", label: "Conectores" },
  { id: "lanzador",   label: "Lanzar pipeline" },
  { id: "fuentes",    label: "Fuentes" },
  { id: "mapa",       label: "Mapa" },
  { id: "ajustes",    label: "Ajustes" },
];

export function PageSistema({ onNav, onOpenAI }: PageSistemaProps) {
  const [tab, setTab] = React.useState<Tab>("conectores");
  return (
    <div className="v3-page">
      <header className="v3-hd">
        <div className="v3-hd-left">
          <span className="v3-hd-eyebrow">Sistema</span>
          <h2 className="v3-hd-title">{TABS.find((t) => t.id === tab)?.label}</h2>
        </div>
        <div className="v3-hd-right">
          {TABS.map((t) => (
            <button key={t.id}
                    className={`v3-btn sm${tab === t.id ? " primary" : " ghost"}`}
                    onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </div>
      </header>
      <div style={{ marginTop: -20 }}>
        {tab === "conectores" && <PageConectores onNav={onNav} onOpenAI={onOpenAI}/>}
        {tab === "lanzador"   && <PageLanzador   onNav={onNav} onOpenAI={onOpenAI}/>}
        {tab === "fuentes"    && <PageFuentes    onNav={onNav} onOpenAI={onOpenAI}/>}
        {tab === "mapa"       && <PageMapa       onNav={onNav} onOpenAI={onOpenAI}/>}
        {tab === "ajustes"    && <PageAjustes    onNav={onNav} onOpenAI={onOpenAI}/>}
      </div>
    </div>
  );
}
