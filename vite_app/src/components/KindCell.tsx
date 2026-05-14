import type { MouseEventHandler } from "react";
import { StatusDot } from "./StatusDot";

export interface KindCellProps {
  status: string;
  onClick?: MouseEventHandler<HTMLDivElement>;
}

export function KindCell({ status, onClick }: KindCellProps) {
  return (
    <div onClick={onClick} style={{
      width: 26, height: 26, display: "flex", alignItems: "center", justifyContent: "center",
      background: status === "empty" ? "transparent" : "var(--panel-2)",
      border: status === "empty" ? "1px dashed var(--border-2)" : "1px solid var(--border)",
      cursor: onClick ? "pointer" : "default",
    }}>
      <StatusDot status={status === "empty" ? "empty" : status} sm />
    </div>
  );
}
