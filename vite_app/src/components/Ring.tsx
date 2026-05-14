// Mini anillo de progreso (%).
export interface RingProps {
  pct: number;
  size?: number;
  color?: string;
}

export function Ring({ pct, size = 38, color }: RingProps) {
  const r = (size - 6) / 2;
  const c = 2 * Math.PI * r;
  const dash = (pct / 100) * c;
  const stroke = color || "var(--y)";
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ display: "block" }}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--panel-3)" strokeWidth="3" />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={stroke} strokeWidth="3"
              strokeDasharray={`${dash} ${c}`} strokeLinecap="butt"
              transform={`rotate(-90 ${size / 2} ${size / 2})`} />
      <text x="50%" y="52%" textAnchor="middle" dominantBaseline="middle"
            fill="var(--text)" fontFamily="var(--f-mono)" fontSize={size > 40 ? 11 : 9} fontWeight="500">
        {pct}
      </text>
    </svg>
  );
}
