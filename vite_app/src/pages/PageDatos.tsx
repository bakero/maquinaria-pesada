// PageDatos · combina coste IA + métricas + optimización + logs.
// Versión v3 industrial con subnav arriba.

import * as React from "react";
import { PageConsumo } from "./PageConsumo";
import { PageMetricas } from "./PageMetricas";
import { PageOptimizar } from "./PageOptimizar";
import { PageLogs } from "./PageLogs";

export interface PageDatosProps {
  onNav: (page: string, payload?: string) => void;
  onOpenAI: (ctx?: unknown) => void;
}

type Tab = "consumo" | "metricas" | "optimizar" | "logs";

const TABS: { id: Tab; label: string }[] = [
  { id: "consumo",   label: "Coste IA" },
  { id: "metricas",  label: "Difusión" },
  { id: "optimizar", label: "Optimización" },
  { id: "logs",      label: "Logs" },
];

export function PageDatos({ onNav, onOpenAI }: PageDatosProps) {
  const [tab, setTab] = React.useState<Tab>("consumo");
  return (
    <div className="v3-page">
      <header className="v3-hd">
        <div className="v3-hd-left">
          <span className="v3-hd-eyebrow">Datos</span>
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
        {tab === "consumo"   && <PageConsumo   onNav={onNav} onOpenAI={onOpenAI}/>}
        {tab === "metricas"  && <PageMetricas  onNav={onNav} onOpenAI={onOpenAI}/>}
        {tab === "optimizar" && <PageOptimizar onNav={onNav} onOpenAI={onOpenAI}/>}
        {tab === "logs"      && <PageLogs      onNav={onNav} onOpenAI={onOpenAI}/>}
      </div>
    </div>
  );
}
