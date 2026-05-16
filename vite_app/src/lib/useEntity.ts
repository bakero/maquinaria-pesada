// Hooks de datos para v3 industrial.
//
// Conectan los componentes (PageModuloTema, LivePanel) a los endpoints reales
// del web_server (load_episode_detail, load_module_detail, /api/stream SSE).
//
// Todos los hooks tienen estado loading/error y, cuando es posible, degradan
// elegantemente a fixtures si no hay backend.

import * as React from "react";

// ───────────────────────── tipos del backend ─────────────────────────

export interface SlotMeta {
  kind: "pdf" | "guion" | "escaleta" | "audio" | "video";
  exists: boolean;
  path: string | null;
  size: number | null;
  size_human: string;
  mtime: number | null;
  mtime_human: string;
  log_path: string | null;
  log_mtime: number | null;
  log_mtime_human: string;
  tail: string;
}

export interface EpisodeDetail {
  id: string;
  mod: string;
  kind: "M" | "T";
  number: number | null;
  slug: string | null;
  title: string;
  dur: string;
  state: { pdf: string; guion: string; escaleta: string; audio: string; video: string; logs: string };
  progress: unknown | null;
  slots: Record<SlotMeta["kind"], SlotMeta>;
  paths: { pdf: string|null; guion: string|null; escaleta: string|null; audio: string|null; video: string|null; logs: string[] };
}

export interface ModuleChild {
  id: string;
  kind: "M" | "T";
  title: string;
  dur: string;
  state: Record<string, string>;
  done: number;
  total: number;
}

export interface ModuleDetail {
  id: string;
  name: string;
  short: string;
  status: "ok"|"warn"|"alert"|"empty";
  pct: number;
  totals: { total: number; done: number; warn: number; alert: number };
  children: ModuleChild[];
}

export interface LiveProcess {
  id: string;
  cmd: string;
  pid: number;
  t: string;
  cost: string;
}

export interface RecentFile {
  path: string;
  t: string;
  by: string;
  mtime: number;
}

export interface StreamSnapshot {
  ts: number;
  live: LiveProcess[];
  recent: RecentFile[];
}

// ───────────────────────── helper fetch ─────────────────────────

async function fetchJSON<T>(url: string, signal?: AbortSignal): Promise<T | null> {
  try {
    const r = await fetch(url, { signal });
    if (!r.ok) return null;
    return await r.json();
  } catch {
    return null;
  }
}

// ───────────────────────── useEntity ─────────────────────────

/** Carga el detalle completo de un módulo/tema desde /api/episode/<id>. */
export function useEntity(entityId: string | null) {
  const [data, setData] = React.useState<EpisodeDetail | null>(null);
  const [loading, setLoading] = React.useState<boolean>(!!entityId);
  const [error, setError] = React.useState<string | null>(null);
  const [version, setVersion] = React.useState(0);

  React.useEffect(() => {
    if (!entityId) {
      setData(null); setLoading(false); setError(null);
      return;
    }
    const ctrl = new AbortController();
    setLoading(true); setError(null);
    fetchJSON<EpisodeDetail>(`/api/episode/${encodeURIComponent(entityId)}`, ctrl.signal)
      .then((d) => { setData(d); setLoading(false); if (d == null) setError("not_found"); });
    return () => ctrl.abort();
  }, [entityId, version]);

  const refresh = React.useCallback(() => setVersion((v) => v + 1), []);
  return { data, loading, error, refresh };
}

// ───────────────────────── useModule ─────────────────────────

/** Detalle agregado del módulo (M + temas + progreso) desde /api/module/<id>. */
export function useModule(modId: string | null) {
  const [data, setData] = React.useState<ModuleDetail | null>(null);
  const [loading, setLoading] = React.useState<boolean>(!!modId);
  const [version, setVersion] = React.useState(0);

  React.useEffect(() => {
    if (!modId) {
      setData(null); setLoading(false);
      return;
    }
    const ctrl = new AbortController();
    setLoading(true);
    fetchJSON<ModuleDetail>(`/api/module/${encodeURIComponent(modId)}`, ctrl.signal)
      .then((d) => { setData(d); setLoading(false); });
    return () => ctrl.abort();
  }, [modId, version]);

  const refresh = React.useCallback(() => setVersion((v) => v + 1), []);
  return { data, loading, refresh };
}

// ───────────────────────── useLiveStream ─────────────────────────

/** Suscripción al SSE /api/stream para procesos vivos + actividad reciente.
 *
 *  Reconecta automáticamente si la conexión se cierra. Si EventSource no
 *  está disponible (entornos SSR / tests), devuelve estado vacío.
 */
export function useLiveStream() {
  const [snapshot, setSnapshot] = React.useState<StreamSnapshot>({ ts: 0, live: [], recent: [] });
  const [connected, setConnected] = React.useState(false);

  React.useEffect(() => {
    if (typeof EventSource === "undefined") return;
    let es: EventSource | null = null;
    let cancelled = false;
    let retryMs = 1000;

    const connect = () => {
      if (cancelled) return;
      es = new EventSource("/api/stream");
      es.onopen = () => { setConnected(true); retryMs = 1000; };
      es.onmessage = (ev) => {
        try {
          const partial = JSON.parse(ev.data);
          setSnapshot((prev) => ({
            ts:     partial.ts ?? prev.ts,
            live:   partial.live   !== undefined ? partial.live   : prev.live,
            recent: partial.recent !== undefined ? partial.recent : prev.recent,
          }));
        } catch { /* ignore */ }
      };
      es.onerror = () => {
        setConnected(false);
        es?.close();
        es = null;
        // backoff exponencial hasta 16s
        retryMs = Math.min(retryMs * 2, 16_000);
        setTimeout(connect, retryMs);
      };
    };
    connect();
    return () => { cancelled = true; es?.close(); };
  }, []);

  return { snapshot, connected };
}

// ───────────────────────── runPipeline ─────────────────────────

/** POST /api/run para lanzar un pipeline con flags. */
export async function runPipeline(script: string, flags: string[]): Promise<{ pid?: number; cmd?: string; error?: string }> {
  try {
    const r = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ script, flags }),
    });
    return await r.json();
  } catch (e) {
    return { error: String(e) };
  }
}

// ───────────────────────── generateSlot ─────────────────────────

/** Lanza la generación de un slot (PDF excluido) para una entidad. */
export async function generateSlot(entityId: string, kind: SlotMeta["kind"]) {
  // Para el slot 'guion' usamos el endpoint dedicado (mejor tracking).
  if (kind === "guion") {
    try {
      const r = await fetch(`/api/episode/${encodeURIComponent(entityId)}/generate`, {
        method: "POST",
      });
      return await r.json();
    } catch (e) {
      return { error: String(e) };
    }
  }
  // Solo permitimos slots cuyo pipeline existe realmente en el repo y está
  // en la whitelist ALLOWED_SCRIPTS de web_server.py. PDF no se genera
  // (es source); escaleta y vídeo no tienen pipeline propio aún —
  // devolvemos un error explícito que el UI mostrará como toast.
  const scriptMap: Partial<Record<SlotMeta["kind"], string>> = {
    audio: "generar_episodio_v2.py",
  };
  const script = scriptMap[kind];
  if (!script) {
    return {
      error: kind === "pdf"
        ? "El PDF es la fuente; no se genera desde la app"
        : `Pipeline para ${kind} no disponible aún en el repo`,
    };
  }
  return runPipeline(script, ["--ep", entityId]);
}

// ───────────────────────── useEntityLogLines ─────────────────────────

export interface LogEntry {
  day: string;     // "2026-05-16"
  line: string;    // raw daylog line
}

export interface LogLinesPayload {
  ok: boolean;
  entity_id?: string;
  days_scanned?: number;
  count?: number;
  entries: LogEntry[];
  error?: string;
}

/** Filtra el daylog por menciones a `entityId` (M3, M3_T1, etc.). */
export function useEntityLogLines(entityId: string | null, days = 7, limit = 300) {
  const [data, setData] = React.useState<LogLinesPayload>({ ok: false, entries: [] });
  const [loading, setLoading] = React.useState<boolean>(!!entityId);
  const [version, setVersion] = React.useState(0);

  React.useEffect(() => {
    if (!entityId) {
      setData({ ok: false, entries: [] });
      setLoading(false);
      return;
    }
    const ctrl = new AbortController();
    setLoading(true);
    fetchJSON<LogLinesPayload>(
      `/api/entity/${encodeURIComponent(entityId)}/log-lines?days=${days}&limit=${limit}`,
      ctrl.signal,
    ).then((d) => {
      setData(d ?? { ok: false, entries: [] });
      setLoading(false);
    });
    return () => ctrl.abort();
  }, [entityId, days, limit, version]);

  const refresh = React.useCallback(() => setVersion((v) => v + 1), []);
  return { data, loading, refresh };
}
