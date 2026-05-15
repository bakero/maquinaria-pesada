// Command palette — ⌘K / Ctrl+K
//
// Linear/Raycast-style: opens centered, fuzzy search across all actions,
// keyboard navigation (↑↓ Enter Esc), grouped sections, hints.
//
// Actions are registered by the caller. Each action has an id, label,
// optional hint, optional section, optional shortcut display.

import * as React from "react";
import { Icon } from "../components";
import { formatCombo } from "../lib/useHotkeys";

export interface PaletteAction {
  id: string;
  label: string;
  hint?: string;
  section?: string;
  shortcut?: string;
  icon?: string;
  keywords?: string[];
  perform: () => void;
}

export interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  actions: PaletteAction[];
}

// Fuzzy score: lower is better. Matches if all chars of query appear in
// order in target. Penalises distance between matches and rewards
// consecutive runs + prefix matches.
function fuzzyScore(query: string, target: string): number | null {
  if (!query) return 0;
  const q = query.toLowerCase();
  const t = target.toLowerCase();
  let qi = 0;
  let score = 0;
  let lastIdx = -1;
  let streak = 0;
  for (let i = 0; i < t.length && qi < q.length; i++) {
    if (t[i] === q[qi]) {
      score += lastIdx >= 0 ? (i - lastIdx) : i; // distance penalty
      if (lastIdx === i - 1) {
        streak++;
        score -= streak * 2; // consecutive bonus
      } else {
        streak = 0;
      }
      lastIdx = i;
      qi++;
    }
  }
  return qi === q.length ? score : null;
}

function rankActions(actions: PaletteAction[], q: string): PaletteAction[] {
  if (!q.trim()) return actions;
  const scored: { a: PaletteAction; s: number }[] = [];
  for (const a of actions) {
    const fields = [a.label, ...(a.keywords || []), a.section || "", a.hint || ""].join(" ");
    const s = fuzzyScore(q, fields);
    if (s !== null) scored.push({ a, s });
  }
  scored.sort((x, y) => x.s - y.s);
  return scored.map((x) => x.a);
}

export function CommandPalette({ open, onClose, actions }: CommandPaletteProps) {
  const [q, setQ] = React.useState("");
  const [idx, setIdx] = React.useState(0);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const listRef = React.useRef<HTMLDivElement>(null);

  const filtered = React.useMemo(() => rankActions(actions, q), [q, actions]);

  React.useEffect(() => {
    if (open) {
      setQ("");
      setIdx(0);
      // Focus the input once mounted
      const t = setTimeout(() => inputRef.current?.focus(), 30);
      return () => clearTimeout(t);
    }
  }, [open]);

  React.useEffect(() => {
    if (idx >= filtered.length) setIdx(Math.max(0, filtered.length - 1));
  }, [filtered, idx]);

  React.useEffect(() => {
    if (!open) return;
    const node = listRef.current?.querySelector<HTMLDivElement>(`[data-cmd-idx="${idx}"]`);
    node?.scrollIntoView({ block: "nearest" });
  }, [idx, open]);

  if (!open) return null;

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setIdx((i) => Math.min(filtered.length - 1, i + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setIdx((i) => Math.max(0, i - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const sel = filtered[idx];
      if (sel) {
        onClose();
        // micro-defer so onClose unmounts before perform navigates
        requestAnimationFrame(() => sel.perform());
      }
    } else if (e.key === "Escape") {
      e.preventDefault();
      onClose();
    }
  }

  // Group filtered by section in original order
  const grouped: Record<string, PaletteAction[]> = {};
  const sectionsOrder: string[] = [];
  for (const a of filtered) {
    const s = a.section || "Acciones";
    if (!grouped[s]) {
      grouped[s] = [];
      sectionsOrder.push(s);
    }
    grouped[s].push(a);
  }

  // Build flat index map for highlight
  const flat: PaletteAction[] = [];
  for (const s of sectionsOrder) flat.push(...grouped[s]);

  return (
    <div className="cmdp-backdrop" onClick={onClose}>
      <div className="cmdp" onClick={(e) => e.stopPropagation()}>
        <div className="cmdp-input">
          <Icon name="search" size={14} />
          <input
            ref={inputRef}
            placeholder="Buscar páginas, episodios, acciones…"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setIdx(0);
            }}
            onKeyDown={onKeyDown}
          />
          <span className="cmdp-esc">Esc</span>
        </div>

        <div className="cmdp-list" ref={listRef}>
          {flat.length === 0 ? (
            <div className="cmdp-empty">
              <div className="cmdp-empty-title">Sin resultados para "{q}"</div>
              <div className="cmdp-empty-hint">
                Prueba con "M3", "audio", "logs", "validar" o el nombre de una página.
              </div>
            </div>
          ) : (
            sectionsOrder.map((s) => (
              <div key={s} className="cmdp-group">
                <div className="cmdp-group-label">{s}</div>
                {grouped[s].map((a) => {
                  const i = flat.indexOf(a);
                  const active = i === idx;
                  return (
                    <div
                      key={a.id}
                      data-cmd-idx={i}
                      className={`cmdp-item${active ? " active" : ""}`}
                      onMouseEnter={() => setIdx(i)}
                      onClick={() => {
                        onClose();
                        requestAnimationFrame(() => a.perform());
                      }}
                    >
                      {a.icon && (
                        <span className="cmdp-item-icon">
                          <Icon name={a.icon} size={13} />
                        </span>
                      )}
                      <div className="cmdp-item-text">
                        <div className="cmdp-item-label">{a.label}</div>
                        {a.hint && <div className="cmdp-item-hint">{a.hint}</div>}
                      </div>
                      {a.shortcut && (
                        <span className="cmdp-item-shortcut">{formatCombo(a.shortcut)}</span>
                      )}
                    </div>
                  );
                })}
              </div>
            ))
          )}
        </div>

        <div className="cmdp-footer">
          <span className="cmdp-foot-key">↑↓</span>
          <span className="cmdp-foot-label">navegar</span>
          <span className="cmdp-foot-key">↵</span>
          <span className="cmdp-foot-label">ejecutar</span>
          <span className="cmdp-foot-key">esc</span>
          <span className="cmdp-foot-label">cerrar</span>
          <span className="cmdp-foot-spacer" />
          <span className="cmdp-foot-brand">MaquinarIA Pesada · Cockpit</span>
        </div>
      </div>
    </div>
  );
}
