import { Icon } from "../components";
import { getLiveProc } from "../data";
import { NAV_GROUPS, WIRED } from "../lib/nav";

export interface SidebarProps {
  current: string;
  onNav: (id: string) => void;
}

export function Sidebar({ current, onNav }: SidebarProps) {
  const liveProc = getLiveProc();
  return (
    <aside className="sb">
      <div className="sb-brand">
        <div className="sb-logo">MP</div>
        <div>
          <div className="sb-title">Maquinaria<br />Pesada</div>
          <div className="sb-sub">v0.9 · branch master</div>
        </div>
      </div>

      <div className="sb-nav">
        {NAV_GROUPS.map((g) => (
          <div key={g.label}>
            <div className="sb-group">{g.label}</div>
            {g.items.map((it) => {
              const active = current === it.id;
              const wired = WIRED.has(it.id);
              return (
                <div
                  key={it.id}
                  className={`sb-item sb-item-compact ${active ? "active" : ""}`}
                  onClick={() => wired && onNav(it.id)}
                  style={{ opacity: wired ? 1 : 0.42, cursor: wired ? "pointer" : "not-allowed" }}
                  title={wired ? "" : "Página no incluida en este prototipo"}
                >
                  <span className="sb-item-icon"><Icon name={it.icon} size={13} /></span>
                  <span style={{ flex: 1 }}>{it.label}</span>
                  {it.emph && <span style={{ fontSize: 9, fontFamily: "var(--f-mono)", color: "var(--y)" }}>●</span>}
                </div>
              );
            })}
          </div>
        ))}
      </div>

      {/* Producción en vivo — discreto */}
      <div className="sb-live">
        <div className="sb-live-hd">
          <div className="sb-live-title">
            <span className="live-dot" />
            En producción
          </div>
          <div className="sb-live-refresh">5s</div>
        </div>
        {liveProc.map((p) => (
          <div key={p.id} className="sb-live-row">
            <span className="lbl" title={p.cmd}>
              {p.cmd.length > 22 ? p.cmd.slice(0, 22) + "…" : p.cmd}
            </span>
            <span className="val ok">{p.t}</span>
          </div>
        ))}
        <div className="sb-live-row" style={{ marginTop: 6 }}>
          <span className="lbl">Hoy</span>
          <span className="val">14 archivos · 3.42€</span>
        </div>
      </div>
    </aside>
  );
}
