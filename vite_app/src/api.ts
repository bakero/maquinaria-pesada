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
