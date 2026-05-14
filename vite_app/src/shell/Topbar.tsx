import * as React from "react";
import { Btn, Icon } from "../components";

export interface Crumb {
  label: string;
  id?: string;
}

export interface TopbarProps {
  crumbs: Crumb[];
  onCrumb: (id: string) => void;
  onOpenAI: () => void;
  onOpenFix: (() => void) | null;
}

export function Topbar({ crumbs, onCrumb, onOpenAI, onOpenFix }: TopbarProps) {
  return (
    <div className="topbar">
      <div className="crumbs">
        {crumbs.map((c, i) => (
          <React.Fragment key={i}>
            {i > 0 && <span className="sep">/</span>}
            {c.id && i < crumbs.length - 1
              ? <a onClick={() => onCrumb(c.id as string)}>{c.label}</a>
              : <span className={i === crumbs.length - 1 ? "cur" : ""}>{c.label}</span>}
          </React.Fragment>
        ))}
      </div>
      <div className="topbar-actions">
        <div className="row gap-4 dim mono" style={{ fontSize: 11, letterSpacing: "0.08em", marginRight: 8 }}>
          <span>163 <span className="muted">tests</span> <span style={{ color: "var(--ok)" }}>●</span></span>
          <span className="muted">·</span>
          <span>30bfb39</span>
        </div>
        {onOpenFix && (
          <Btn kind="danger" sm onClick={onOpenFix} icon={<Icon name="wrench" size={11} />}>
            Arreglar con Claude
          </Btn>
        )}
        <Btn kind="primary" sm onClick={onOpenAI} icon={<Icon name="spark" size={11} />}>
          Mejorar con IA
        </Btn>
      </div>
    </div>
  );
}
