import type { ReactNode, MouseEventHandler } from "react";

export type BtnKind = "default" | "primary" | "ghost" | "danger";
export type BtnSize = "sm" | "md";

export interface BtnProps {
  kind?: BtnKind;
  sm?: boolean;
  size?: BtnSize;
  onClick?: MouseEventHandler<HTMLButtonElement>;
  icon?: ReactNode;
  disabled?: boolean;
  children: ReactNode;
}

export function Btn({
  kind = "default",
  sm,
  size,
  onClick,
  icon,
  disabled,
  children,
}: BtnProps) {
  const cls = ["btn"];
  if (kind !== "default") cls.push(kind);
  if (sm || size === "sm") cls.push("sm");
  return (
    <button
      className={cls.join(" ")}
      onClick={onClick}
      disabled={disabled}
      type="button"
    >
      {icon}
      {icon ? <span style={{ marginLeft: 6 }}>{children}</span> : children}
    </button>
  );
}
