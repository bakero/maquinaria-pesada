export interface KpiProps {
  label: string;
  value: string | number;
  unit?: string;
  delta?: string;
  deltaDir?: "up" | "dn" | "";
}

export function Kpi({ label, value, unit, delta, deltaDir }: KpiProps) {
  return (
    <div className="kpi">
      <div className="kpi-lbl">{label}</div>
      <div className="kpi-val">
        {value}
        {unit && <span className="kpi-unit">{unit}</span>}
      </div>
      {delta && <div className={`kpi-delta ${deltaDir || ""}`}>{delta}</div>}
    </div>
  );
}
