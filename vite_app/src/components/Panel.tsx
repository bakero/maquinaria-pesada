import type { ReactNode } from "react";

export interface PanelProps {
  title?: ReactNode;
  meta?: ReactNode;
  actions?: ReactNode;
  children?: ReactNode;
  noPad?: boolean;
}

export function Panel({ title, meta, actions, children, noPad }: PanelProps) {
  return (
    <div className="panel">
      {(title || actions) && (
        <div className="panel-hd">
          <div className="panel-hd-title">
            {title}
            {meta && <span className="panel-hd-meta" style={{ marginLeft: 8 }}>{meta}</span>}
          </div>
          {actions && <div className="row gap-3">{actions}</div>}
        </div>
      )}
      <div style={{ padding: noPad ? 0 : "16px 18px" }}>{children}</div>
    </div>
  );
}
