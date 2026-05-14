// Icono inline mínimo (monoline). Catálogo cerrado y tipado.
export type IconName =
  | "home" | "grid" | "module" | "episode" | "pipe" | "map" | "plug"
  | "prompt" | "folder" | "play" | "log" | "brain" | "coin" | "key"
  | "chat" | "settings" | "spark" | "wrench" | "close" | "arrow"
  | "check" | "dot" | "search" | "refresh" | "doc";

export interface IconProps {
  name: IconName | string;
  size?: number;
}

export function Icon({ name, size = 14 }: IconProps) {
  const s = size;
  const stroke = {
    stroke: "currentColor", strokeWidth: 1.5, fill: "none",
    strokeLinecap: "round" as const, strokeLinejoin: "round" as const,
  };
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
