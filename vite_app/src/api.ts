import type { AIChatResponse, BootstrapPayload } from "./types";

const BASE = ""; // mismo origen — el dev server proxea /api a :8765

export async function fetchBootstrap(): Promise<BootstrapPayload | null> {
  try {
    const res = await fetch(`${BASE}/api/bootstrap`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as BootstrapPayload;
  } catch {
    return null;
  }
}

export async function aiChat(
  mode: "improve" | "fix",
  target: string | null,
  message: string,
): Promise<AIChatResponse> {
  try {
    const res = await fetch(`${BASE}/api/ai/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode, target, message }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return (await res.json()) as AIChatResponse;
  } catch (e) {
    return { ok: false, text: `[offline] ${String(e)}`, usage: null };
  }
}

export async function runPipeline(
  script: string,
  flags: [string, string | boolean][],
): Promise<{ ok: boolean; pid?: number; log?: string; error?: string }> {
  const res = await fetch(`${BASE}/api/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ script, flags }),
  });
  return res.json();
}

// ── Generación de guion por episodio concreto ──────────────────────────

export interface GenLog {
  ok: boolean;
  ep_id: string;
  exists: boolean;
  verdict?: "ok" | "warn" | "running";
  attempts?: number;
  hard_issues?: string[];
  soft_issues?: string[];
  saved?: boolean;
  mtime?: number;
  text?: string;
  error?: string;
}

/** Lanza la generación del guion de UN episodio (resuelve PDF + script en el server). */
export async function generateGuion(
  epId: string,
): Promise<{ ok: boolean; pid?: number; log?: string; error?: string }> {
  try {
    const res = await fetch(`${BASE}/api/episode/${encodeURIComponent(epId)}/generate`, {
      method: "POST",
    });
    return res.json();
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}

/** Lee la traza de generación/validación (intentos, issues hard/soft, veredicto). */
export async function fetchGenLog(epId: string): Promise<GenLog> {
  try {
    const res = await fetch(
      `${BASE}/api/episode/${encodeURIComponent(epId)}/gen-log`,
      { cache: "no-store" },
    );
    return (await res.json()) as GenLog;
  } catch (e) {
    return { ok: false, ep_id: epId, exists: false, error: String(e) };
  }
}
