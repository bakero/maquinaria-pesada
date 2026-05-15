// useHotkeys — global keyboard shortcuts hook.
//
// Registers a handler against the document. Supports:
//   - "mod" → ⌘ on macOS, Ctrl elsewhere.
//   - chord sequences like "g m" (press g, then m within 1.2 s).
//   - single keys ("?", "Escape").
//
// All bindings are skipped if the user is currently typing in an input,
// textarea or contentEditable — so shortcuts never hijack form typing.

import { useEffect, useRef } from "react";

type Handler = (e: KeyboardEvent) => void;

const isMac = typeof navigator !== "undefined" && /Mac|iPod|iPhone|iPad/.test(navigator.platform);

function isTyping(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  if (target.isContentEditable) return true;
  return false;
}

function matches(combo: string, e: KeyboardEvent): boolean {
  const parts = combo.toLowerCase().split("+").map((p) => p.trim());
  const key = parts.pop()!;
  const needMod = parts.includes("mod");
  const needShift = parts.includes("shift");
  const needAlt = parts.includes("alt");
  const modPressed = isMac ? e.metaKey : e.ctrlKey;

  if (needMod !== modPressed) return false;
  if (needShift !== e.shiftKey) return false;
  if (needAlt !== e.altKey) return false;
  if (key.length === 1) return e.key.toLowerCase() === key;
  return e.key === key || e.code === key;
}

export interface Hotkey {
  combo: string;             // e.g. "mod+k", "?", "Escape", "g m" (chord)
  handler: Handler;
  allowInInputs?: boolean;   // by default skipped when typing
  description?: string;
}

export function useHotkeys(bindings: Hotkey[]) {
  const chordRef = useRef<{ key: string; ts: number } | null>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      for (const b of bindings) {
        if (!b.allowInInputs && isTyping(e.target)) continue;

        // Chord support: "g m"
        if (b.combo.includes(" ") && !b.combo.includes("+")) {
          const [first, second] = b.combo.toLowerCase().split(" ");
          const now = performance.now();
          const ch = chordRef.current;
          if (!ch || now - ch.ts > 1200) {
            if (e.key.toLowerCase() === first && !e.metaKey && !e.ctrlKey) {
              chordRef.current = { key: first, ts: now };
              e.preventDefault();
              return;
            }
          } else if (ch.key === first && e.key.toLowerCase() === second) {
            chordRef.current = null;
            e.preventDefault();
            b.handler(e);
            return;
          }
          continue;
        }

        if (matches(b.combo, e)) {
          e.preventDefault();
          b.handler(e);
          return;
        }
      }
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [bindings]);
}

export function formatCombo(combo: string): string {
  return combo
    .split("+")
    .map((p) => {
      const s = p.trim().toLowerCase();
      if (s === "mod") return isMac ? "⌘" : "Ctrl";
      if (s === "shift") return isMac ? "⇧" : "Shift";
      if (s === "alt") return isMac ? "⌥" : "Alt";
      if (s === "escape") return "Esc";
      if (s.length === 1) return s.toUpperCase();
      return s;
    })
    .join("+")
    .replace(/\+ /g, " ");
}
