// TopNav — barra superior única, sin sidebar.
//
// Cinco secciones consolidadas:
//   - Inicio       → home (dashboard + factory + IA orquestadora)
//   - Producción   → master (drill-down master → módulo → episodio)
//   - Pipeline     → lanzador + conectores (combinado)
//   - Datos        → logs + tokens + consumo + optimizar + métricas (sub-tabs)
//   - Recursos     → fuentes + previsualizar + pizarra + mapa
//
// La sección activa se infiere de la página actual via mapSectionFor().

import * as React from "react";
import { Icon } from "../components";
import { Brand } from "./Brand";
import { formatCombo } from "../lib/useHotkeys";

export interface TopNavItem {
  id: string;            // section id, used by mapSectionFor
  page: string;          // which legacy page to navigate to
  label: string;
  hint?: string;
  badge?: string;
}

export const NAV: TopNavItem[] = [
  { id: "inicio",     page: "home",     label: "Inicio" },
  { id: "produccion", page: "master",   label: "Producción", badge: "22 ep." },
  { id: "pipeline",   page: "pipeline", label: "Pipeline" },
  { id: "datos",      page: "datos",    label: "Datos" },
  { id: "recursos",   page: "recursos", label: "Recursos" },
];

// Mapea una página (de las 15 legacy) a la sección de top-nav.
export function mapSectionFor(page: string): string {
  switch (page) {
    case "home":
      return "inicio";
    case "master":
    case "modulo":
    case "episodio":
      return "produccion";
    case "lanzador":
    case "conectores":
    case "pipeline":
      return "pipeline";
    case "logs":
    case "tokens":
    case "consumo":
    case "optimizar":
    case "metricas":
    case "datos":
      return "datos";
    case "fuentes":
    case "player":
    case "pizarra":
    case "mapa":
    case "recursos":
      return "recursos";
    default:
      return "inicio";
  }
}

export interface TopNavProps {
  page: string;
  onNav: (page: string) => void;
  onOpenPalette: () => void;
  onOpenAI: () => void;
  onOpenTour: () => void;
  liveLabel?: string;
}

export function TopNav({
  page, onNav, onOpenPalette, onOpenAI, onOpenTour, liveLabel,
}: TopNavProps) {
  const section = mapSectionFor(page);

  return (
    <nav className="topnav">
      <div className="topnav-left">
        <Brand onClick={() => onNav("home")} />
        <div className="topnav-nav">
          {NAV.map((it) => (
            <button
              key={it.id}
              className={`topnav-item${section === it.id ? " active" : ""}`}
              onClick={() => onNav(it.page)}
            >
              {it.label}
              {it.badge && <span className="topnav-item-badge">{it.badge}</span>}
            </button>
          ))}
        </div>
      </div>

      <div></div>

      <div className="topnav-right">
        {liveLabel && (
          <span className="topnav-live" title="Producción en vivo">
            <span className="topnav-live-dot" />
            {liveLabel}
          </span>
        )}

        <button className="topnav-search" onClick={onOpenPalette}
                title="Buscar y ejecutar">
          <Icon name="search" size={12}/>
          <span className="topnav-search-label">Buscar o ejecutar…</span>
          <span className="topnav-search-kbd">{formatCombo("mod+k")}</span>
        </button>

        <button className="topnav-icon-btn" onClick={onOpenTour}
                title="Tour de bienvenida (?)" aria-label="Ayuda">
          <span style={{ fontFamily: "var(--f-display)", fontWeight: 600, fontSize: 14 }}>?</span>
        </button>

        <button className="topnav-cta" onClick={onOpenAI}
                title="Mejorar con IA (⌘I)">
          <Icon name="spark" size={11}/>
          Mejorar con IA
        </button>
      </div>
    </nav>
  );
}
