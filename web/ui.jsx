// ui.jsx — Shared atoms for Maquinaria Pesada cockpit

// ── Status dot ───────────────────────────────────────────
function StatusDot({ status, sm }) {
  const cls = `dot ${status}${sm ? " sm" : ""}`;
  return <span className={cls} />;
}

// ── Badge ────────────────────────────────────────────────
function Badge({ kind, children }) {
  return <span className={`badge ${kind || ""}`}>{children}</span>;
}

// ── Progress bar ─────────────────────────────────────────
function Bar({ pct, status }) {
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

// ── KPI card ─────────────────────────────────────────────
function Kpi({ label, value, unit, delta, deltaDir }) {
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

// ── Panel ────────────────────────────────────────────────
function Panel({ title, meta, actions, children, noPad }) {
  return (
    <div className="panel">
      {(title || actions) && (
        <div className="panel-hd">
          <div className="panel-hd-title">
            {title}
            {meta && <span className="panel-hd-meta" style={{ marginLeft: 8 }}>{meta}</span>}
          </div>
          {actions && <div className="row gap-3">{actions}</div>}
        </div>
      )}
      <div style={{ padding: noPad ? 0 : "16px 18px" }}>{children}</div>
    </div>
  );
}

// ── Button ───────────────────────────────────────────────
function Btn({ kind, sm, onClick, children, icon, title, style }) {
  const cls = `btn ${kind || ""} ${sm ? "sm" : ""}`;
  return (
    <button className={cls} onClick={onClick} title={title} style={style}>
      {icon && <span style={{ fontSize: 11 }}>{icon}</span>}
      {children}
    </button>
  );
}

// ── Page header with hazard flag ─────────────────────────
function PageHeader({ title, sub, actions }) {
  return (
    <div className="page-hd">
      <div className="page-hd-l">
        <div className="flag-bar" />
        <div>
          <h1 className="h1">{title}</h1>
          {sub && <div className="h1-sub">{sub}</div>}
        </div>
      </div>
      {actions && <div className="row gap-4">{actions}</div>}
    </div>
  );
}

// ── Hazard tape ──────────────────────────────────────────
function HazardTape() { return <div className="hazard-stripes" />; }

// ── Speaker ──────────────────────────────────────────────
function Speaker({ who }) {
  const name = who === "iago" ? "IAGO" : "MARÍA";
  return (
    <span className={`spk spk-${who}`}>
      <span className="spk-dot" />
      <span className="spk-name">{name}</span>
    </span>
  );
}

// ── Icon (tiny inline SVG, monoline) ─────────────────────
function Icon({ name, size = 14 }) {
  const s = size;
  const stroke = { stroke: "currentColor", strokeWidth: 1.5, fill: "none", strokeLinecap: "round", strokeLinejoin: "round" };
  switch (name) {
    case "home":     return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><path d="M2 7l6-5 6 5v7a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7z"/><path d="M6 14V9h4v5"/></svg>;
    case "grid":     return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><rect x="2" y="2" width="5" height="5"/><rect x="9" y="2" width="5" height="5"/><rect x="2" y="9" width="5" height="5"/><rect x="9" y="9" width="5" height="5"/></svg>;
    case "module":   return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><path d="M8 1l6 3v8l-6 3-6-3V4z"/><path d="M8 8l6-3M8 8L2 5M8 8v7"/></svg>;
    case "episode":  return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><circle cx="8" cy="8" r="6"/><path d="M6 5l5 3-5 3z" fill="currentColor"/></svg>;
    case "pipe":     return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><circle cx="3" cy="8" r="1.5"/><circle cx="13" cy="8" r="1.5"/><circle cx="8" cy="3" r="1.5"/><circle cx="8" cy="13" r="1.5"/><path d="M4.5 8h7M8 4.5v7"/></svg>;
    case "map":      return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><path d="M2 4l4-2 4 2 4-2v10l-4 2-4-2-4 2z"/><path d="M6 2v10M10 4v10"/></svg>;
    case "plug":     return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><path d="M5 8V3M11 8V3M3 8h10v3a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4z"/></svg>;
    case "prompt":   return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><path d="M2 4l3 3-3 3M7 10h7"/></svg>;
    case "folder":   return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><path d="M2 4a1 1 0 0 1 1-1h3l2 2h5a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1z"/></svg>;
    case "play":     return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><path d="M4 3l9 5-9 5z" fill="currentColor"/></svg>;
    case "log":      return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><path d="M3 2h7l3 3v9H3z"/><path d="M5 7h6M5 10h6M5 13h4"/></svg>;
    case "brain":    return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><path d="M6 3a2 2 0 0 0-2 2v1a2 2 0 0 0 0 4v1a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-1a2 2 0 0 0 0-4V5a2 2 0 0 0-2-2z"/><path d="M8 3v10"/></svg>;
    case "coin":     return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><circle cx="8" cy="8" r="6"/><path d="M8 4v8M6 6h3a1.5 1.5 0 0 1 0 3H6a1.5 1.5 0 0 0 0 3h3"/></svg>;
    case "key":      return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><circle cx="5" cy="8" r="3"/><path d="M8 8h7M12 8v3M14 8v2"/></svg>;
    case "chat":     return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><path d="M2 4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1H8l-3 3v-3H3a1 1 0 0 1-1-1z"/></svg>;
    case "settings": return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><circle cx="8" cy="8" r="2"/><path d="M8 1v2M8 13v2M1 8h2M13 8h2M3 3l1.5 1.5M11.5 11.5L13 13M3 13l1.5-1.5M11.5 4.5L13 3"/></svg>;
    case "spark":    return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><path d="M8 1l1.5 5L14 8l-4.5 1.5L8 15l-1.5-5.5L2 8l4.5-2z"/></svg>;
    case "wrench":   return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><path d="M10 3a3 3 0 1 1 3 3L7 12l-3-3z"/></svg>;
    case "close":    return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><path d="M3 3l10 10M13 3L3 13"/></svg>;
    case "arrow":    return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><path d="M3 8h10M9 4l4 4-4 4"/></svg>;
    case "check":    return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><path d="M3 8l3 3 7-7"/></svg>;
    case "dot":      return <svg width={s} height={s} viewBox="0 0 16 16"><circle cx="8" cy="8" r="3" fill="currentColor"/></svg>;
    case "search":   return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><circle cx="7" cy="7" r="4"/><path d="M10 10l4 4"/></svg>;
    case "refresh":  return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><path d="M2 8a6 6 0 0 1 10-4M14 8a6 6 0 0 1-10 4M12 4V1h3M4 12v3H1"/></svg>;
    case "doc":      return <svg width={s} height={s} viewBox="0 0 16 16" {...stroke}><path d="M3 2h7l3 3v9H3z"/></svg>;
    default:         return null;
  }
}

// ── Mini % ring ──────────────────────────────────────────
function Ring({ pct, size = 38, color }) {
  const r = (size - 6) / 2;
  const c = 2 * Math.PI * r;
  const dash = (pct / 100) * c;
  const stroke = color || "var(--y)";
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ display: "block" }}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="var(--panel-3)" strokeWidth="3"/>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={stroke} strokeWidth="3"
              strokeDasharray={`${dash} ${c}`} strokeLinecap="butt"
              transform={`rotate(-90 ${size/2} ${size/2})`}/>
      <text x="50%" y="52%" textAnchor="middle" dominantBaseline="middle"
            fill="var(--text)" fontFamily="var(--f-mono)" fontSize={size > 40 ? 11 : 9} fontWeight="500">
        {pct}
      </text>
    </svg>
  );
}

// ── Kind cell (PDF/Guion/Audio/Vídeo/Logs) ───────────────
function KindCell({ status, onClick }) {
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

// ── Source pills (link app element → repo files) ─────────
function SourcePills({ files, label = "Implementado en" }) {
  if (!files || !files.length) return null;
  const labelOf = (path) => {
    if (path.endsWith("/")) return "DIR";
    if (path.endsWith(".py")) return "PY";
    if (path.endsWith(".md")) return "MD";
    if (path.endsWith(".json")) return "JSON";
    return "FILE";
  };
  const shortOf = (path) => {
    // Strip leading cockpit/ for pages to reduce noise
    return path;
  };
  return (
    <div className="src-strip">
      <span className="src-strip-label">
        <Icon name="folder" size={10}/> {label}
      </span>
      {files.map((f) => (
        <a
          key={f}
          href={ghLink(f)}
          target="_blank"
          rel="noopener"
          className="src-pill"
          title={`Abrir ${f} en GitHub`}
        >
          <span className="kind">{labelOf(f)}</span>
          {shortOf(f)}
          <span className="gh">↗</span>
        </a>
      ))}
      <span style={{ marginLeft: "auto", color: "var(--text-mute)", fontSize: 10, letterSpacing: "0.08em" }}>
        bakero/maquinaria-pesada @ {REPO_REF}
      </span>
    </div>
  );
}

Object.assign(window, {
  StatusDot, Badge, Bar, Kpi, Panel, Btn, PageHeader, HazardTape,
  Speaker, Icon, Ring, KindCell, SourcePills,
});
