// Punto de estado. Usa las clases CSS .dot.<status>[.sm] de styles.css.
export interface StatusDotProps {
  status: string;
  sm?: boolean;
}

export function StatusDot({ status, sm }: StatusDotProps) {
  return <span className={`dot ${status}${sm ? " sm" : ""}`} />;
}
