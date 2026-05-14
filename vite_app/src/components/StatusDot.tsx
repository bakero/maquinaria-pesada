import type { Status } from "../types";

const COLORS: Record<Status, string> = {
  ok:    "var(--ok)",
  warn:  "var(--warn)",
  alert: "var(--alert)",
  empty: "var(--text-mute)",
  run:   "var(--y)",
};

export function StatusDot({ status, size = 8 }: { status: Status; size?: number }) {
  return (
    <span
      style={{
        display: "inline-block",
        width: size,
        height: size,
        borderRadius: "50%",
        background: COLORS[status],
      }}
      aria-label={status}
    />
  );
}
