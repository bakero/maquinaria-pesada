export interface BarProps {
  pct: number;
  status?: string;
}

export function Bar({ pct, status }: BarProps) {
  const color = status === "ok"    ? "var(--ok)"
              : status === "warn"  ? "var(--warn)"
              : status === "alert" ? "var(--alert)"
              : "var(--y)";
  return (
    <div className="bar">
      <div className="bar-fill" style={{ width: `${pct}%`, background: color }} />
    </div>
  );
}
