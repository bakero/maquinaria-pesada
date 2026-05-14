import type { CSSProperties, MouseEventHandler, ReactNode } from "react";

export type BtnKind = "default" | "primary" | "ghost" | "danger";
export type BtnSize = "sm" | "md";

export interface BtnProps {
  kind?: BtnKind | string;
  sm?: boolean;
  onClick?: MouseEventHandler<HTMLButtonElement>;
  children?: ReactNode;
  icon?: ReactNode;
  title?: string;
  style?: CSSProperties;
  disabled?: boolean;
}

export function Btn({ kind, sm, onClick, children, icon, title, style, disabled }: BtnProps) {
  const cls = `btn ${kind || ""} ${sm ? "sm" : ""}`;
  return (
    <button className={cls} onClick={onClick} title={title} style={style} disabled={disabled}>
      {icon && <span style={{ fontSize: 11 }}>{icon}</span>}
      {children}
    </button>
  );
}
