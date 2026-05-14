import type { ReactNode } from "react";

export interface BadgeProps {
  kind?: string;
  children?: ReactNode;
}

export function Badge({ kind, children }: BadgeProps) {
  return <span className={`badge ${kind || ""}`}>{children}</span>;
}
