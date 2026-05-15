// TopNav — barra superior única. Industrial sobrio. Sin emojis.
//
// Tres secciones:
//   Producción  ← master + módulos + temas (el operativo)
//   Datos       ← coste IA + métricas difusión + optimización + logs
//   Sistema     ← conectores + ajustes + mapa
//
// La sección activa se infiere de la página actual via mapSectionFor().

import * as React from "react";
import { Icon } from "../components";
import { formatCombo } from "../lib/useHotkeys";

export interface TopNavItem {
  id: string;            // section id, used by mapSectionFor
  page: string;          // which page to navigate to
  label: string;
}

export const NAV: TopNavItem[] = [
  { id: "produccion", page: "produccion", label: "Producción" },
  { id: "datos",      page: "datos",      label: "Datos" },
  { id: "sistema",    page: "sistema",    label: "Sistema" },
];

// Mapea una página a su sección de top-nav.
export function mapSectionFor(page: string): string {
  switch (page) {
    case "home":
    case "produccion":
    case "master":
    case "modulo":
    case "tema":
    case "episodio":
      return "produccion";
    case "datos":
    case "logs":
    case "tokens":
    case "consumo":
    case "optimizar":
    case "metricas":
      return "datos";
    case "sistema":
    case "conectores":
    case "lanzador":
    case "pipeline":
    case "mapa":
    case "pizarra":
    case "ajustes":
    case "recursos":
    case "fuentes":
    case "player":
      return "sistema";
    default:
      return "produccion";
  }
}

export interface TopNavProps {
  page: string;
  onNav: (page: string) => void;
  onOpenPalette: () => void;
  onOpenAI: () => void;
  liveCount?: number;       // procesos en producción
  liveLabel?: string;       // texto del proceso activo si lo hay
}

export function TopNav({
  page, onNav, onOpenPalette, onOpenAI, liveCount = 0, liveLabel,
}: TopNavProps) {
  const section = mapSectionFor(page);

  return (
    <nav className="topnav3">
      {/* Brand: mark + wordmark mono */}
      <div className="topnav3-brand" onClick={() => onNav("produccion")}
           role="button" tabIndex={0}
           onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onNav("produccion")}>
        <span className="topnav3-mark" aria-hidden>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <rect x="0"  y="0"  width="2" height="14" fill="currentColor"/>
            <rect x="4"  y="0"  width="2" height="14" fill="currentColor"/>
            <rect x="8"  y="0"  width="2" height="14" fill="currentColor" opacity="0.55"/>
            <rect x="12" y="0"  width="2" height="14" fill="currentColor" opacity="0.25"/>
          </svg>
        </span>
        <span className="topnav3-wordmark">MAQUINARIA·PESADA</span>
        <span className="topnav3-build">v0.9 — master</span>
      </div>

      {/* Sections */}
      <div className="topnav3-nav">
        {NAV.map((it) => (
          <button
            key={it.id}
            className={`topnav3-item${section === it.id ? " active" : ""}`}
            onClick={() => onNav(it.page)}
          >
            {it.label}
          </button>
        ))}
      </div>

      {/* Right cluster */}
      <div className="topnav3-right">
        {liveCount > 0 && (
          <span className="topnav3-live" title="Procesos en producción ahora">
            <span className="topnav3-live-dot" />
            <span className="topnav3-live-label">
              {liveCount} en proceso{liveLabel ? ` — ${liveLabel}` : ""}
            </span>
          </span>
        )}

        <button className="topnav3-search" onClick={onOpenPalette}
                title="Buscar y ejecutar">
          <Icon name="search" size={11}/>
          <span className="topnav3-search-label">Buscar o ejecutar</span>
          <span className="topnav3-search-kbd">{formatCombo("mod+k")}</span>
        </button>

        <button className="topnav3-ai" onClick={onOpenAI}
                title="Asistente IA">
          IA
        </button>
      </div>
    </nav>
  );
}
