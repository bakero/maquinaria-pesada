// Brand — minimal wordmark with refined mark (no "MP" block).
//
// El mark es un símbolo de tres barras paralelas que evocan "pipeline"
// + un punto de salida — geometría simple, asociable a producción.

import * as React from "react";

export interface BrandProps {
  onClick?: () => void;
}

export function Brand({ onClick }: BrandProps) {
  return (
    <a className="brand" onClick={onClick} role="button" tabIndex={0}
       onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onClick?.()}>
      <span className="brand-mark" aria-hidden>
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <rect x="3" y="4" width="9" height="1.6" fill="#0E0D0B" rx="0.8"/>
          <rect x="3" y="9.2" width="11" height="1.6" fill="#0E0D0B" rx="0.8"/>
          <rect x="3" y="14.4" width="7" height="1.6" fill="#0E0D0B" rx="0.8"/>
          <circle cx="16" cy="14.4" r="2" fill="#0E0D0B"/>
        </svg>
      </span>
      <span className="brand-wordmark">
        <span className="brand-wordmark-1">Maquinaria Pesada</span>
        <span className="brand-wordmark-2">Cockpit · IA</span>
      </span>
    </a>
  );
}
