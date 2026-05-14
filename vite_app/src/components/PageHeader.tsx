import type { ReactNode } from "react";

export interface PageHeaderProps {
  title: ReactNode;
  sub?: ReactNode;
  actions?: ReactNode;
}

export function PageHeader({ title, sub, actions }: PageHeaderProps) {
  return (
    <div className="page-hd">
      <div className="page-hd-l">
        <div className="flag-bar" />
        <div>
          <h1 className="h1">{title}</h1>
          {sub && <div className="h1-sub">{sub}</div>}
        </div>
      </div>
      {actions && <div className="row gap-4">{actions}</div>}
    </div>
  );
}
