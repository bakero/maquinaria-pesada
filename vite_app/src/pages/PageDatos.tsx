// PageDatos — combina Logs / Tokens / Consumo / Optimizar / Métricas
// bajo un subnav único. Cada sub-tab carga la página legacy.

import * as React from "react";
import { PageHeader } from "../components";
import { PageLogs } from "./PageLogs";
import { PageOptimizar } from "./PageOptimizar";
import { PageConsumo } from "./PageConsumo";
import { PageMetricas } from "./PageMetricas";
// PageTokens no existe como standalone — Tokens vive dentro de Consumo
// y Logs. Lo dejamos así para evitar duplicación.

export interface PageDatosProps {
  onNav: (page: string, payload?: string) => void;
  onOpenAI: (ctx?: unknown) => void;
}

type Tab = "logs" | "consumo" | "optimizar" | "metricas";

const TABS: { id: Tab; label: string; count?: string }[] = [
  { id: "consumo",   label: "Coste y tokens" },
  { id: "metricas",  label: "Métricas de difusión" },
  { id: "optimizar", label: "Optimizar IA" },
  { id: "logs",      label: "Logs" },
];

export function PageDatos({ onNav, onOpenAI }: PageDatosProps) {
  const [tab, setTab] = React.useState<Tab>("consumo");
  return (
    <div className="page">
      <PageHeader
        title="Datos"
        sub="Coste de IA, audiencia, optimización y trazas de producción · 5 fuentes consolidadas."
      />
      <div className="subnav">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`subnav-item${tab === t.id ? " active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
            {t.count && <span className="count">{t.count}</span>}
          </button>
        ))}
      </div>
      <div style={{ marginTop: -10 }}>
        {tab === "logs"      && <PageLogs      onNav={onNav} onOpenAI={onOpenAI}/>}
        {tab === "consumo"   && <PageConsumo   onNav={onNav} onOpenAI={onOpenAI}/>}
        {tab === "optimizar" && <PageOptimizar onNav={onNav} onOpenAI={onOpenAI}/>}
        {tab === "metricas"  && <PageMetricas  onNav={onNav} onOpenAI={onOpenAI}/>}
      </div>
    </div>
  );
}
