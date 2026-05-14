import type { ReactNode } from "react";

export interface PanelProps {
  title: ReactNode;
  meta?: ReactNode;
  actions?: ReactNode;
  children?: ReactNode;
}

export function Panel({ title, meta, actions, children }: PanelProps) {
  return (
    <section className="panel">
      <header className="panel-hd">
        <div className="panel-title">{title}</div>
        {meta && <div className="panel-meta">{meta}</div>}
        {actions && <div className="panel-actions">{actions}</div>}
      </header>
      <div className="panel-body">{children}</div>
    </section>
  );
}
