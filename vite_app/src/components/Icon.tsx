// Iconos line-art mínimos. Catálogo cerrado y tipado.
export type IconName =
  | "home" | "grid" | "module" | "episode" | "pipe" | "map" | "plug"
  | "prompt" | "folder" | "play" | "log" | "brain" | "coin" | "settings"
  | "spark" | "wrench" | "doc" | "arrow" | "close" | "check";

export interface IconProps {
  name: IconName;
  size?: number;
}

const PATHS: Record<IconName, string> = {
  home: "M3 11l9-8 9 8v10a2 2 0 0 1-2 2h-4v-7H9v7H5a2 2 0 0 1-2-2z",
  grid: "M3 3h8v8H3zM13 3h8v8h-8zM3 13h8v8H3zM13 13h8v8h-8z",
  module: "M4 6h16M4 12h16M4 18h16",
  episode: "M5 4v16l14-8z",
  pipe: "M4 12h6m4 0h6M10 8v8m4-8v8",
  map: "M9 4l-6 3v13l6-3 6 3 6-3V4l-6 3z",
  plug: "M6 7v4a6 6 0 0 0 12 0V7M9 3v4M15 3v4",
  prompt: "M4 6h16M4 12h10M4 18h16",
  folder: "M3 6a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
  play: "M6 4l14 8-14 8z",
  log: "M5 4h14v16H5zM8 8h8M8 12h8M8 16h5",
  brain: "M8 4a4 4 0 0 0-4 4v8a4 4 0 0 0 4 4M16 4a4 4 0 0 1 4 4v8a4 4 0 0 1-4 4",
  coin: "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zM12 6v12M9 9h6M9 15h6",
  settings: "M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2",
  spark: "M12 2l2 7 7 2-7 2-2 7-2-7-7-2 7-2z",
  wrench: "M14 4a4 4 0 0 1 4 6l-2-2-2 2-2-2 2-2-2-2a4 4 0 0 1 2 0z",
  doc: "M6 2h9l5 5v15H6zM15 2v6h5",
  arrow: "M4 12h14M14 6l6 6-6 6",
  close: "M6 6l12 12M18 6L6 18",
  check: "M5 12l5 5 9-11",
};

export function Icon({ name, size = 14 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="square"
      aria-hidden
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
