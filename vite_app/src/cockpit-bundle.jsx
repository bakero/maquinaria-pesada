// @ts-nocheck
// Cockpit bundle — concatenacion de los archivos legacy de web/.
// Adaptado al entry-point ESM de Vite: React 18 (createRoot),
// JSX automatico, mount al final via app.jsx. NO editar a mano:
// los originales viven en web/. Regenera con scripts/build-bundle.py
import * as React from 'react';
import { createRoot } from 'react-dom/client';
// Expone React al window por compat con codigo legacy que usa React.useState etc.
if (typeof window !== 'undefined') { window.React = React; }

// ── Módulos extraídos del monolito (Fase 1a) ─────────────────────────
import {
  Btn, Icon, Panel, StatusDot, Kpi, Bar, Badge, Ring, Speaker, HazardTape,
  KindCell, PageHeader, SourcePills, SourceTitle, GenGuionPanel,
} from "./components";
import { NAV_GROUPS, WIRED, srcFor, ghLink, REPO, REPO_REF } from "./lib/nav";
import { SOURCES, KINDS, pathOf } from "./lib/sources";
import {
  FIXTURE_MODULES as MODULES, FIXTURE_EPISODES as EPISODES,
  GUION_PREVIEW, CHECKS_M3, applyBootstrap,
} from "./data";
import { PageEpisodio } from "./pages/episode/PageEpisodio";


// ============================ tweaks-panel.jsx ============================


// tweaks-panel.jsx
// Reusable Tweaks shell + form-control helpers.
//
// Owns the host protocol (listens for __activate_edit_mode / __deactivate_edit_mode,
// posts __edit_mode_available / __edit_mode_set_keys / __edit_mode_dismissed) so
// individual prototypes don't re-roll it. Ships a consistent set of controls so you
// don't hand-draw <input type="range">, segmented radios, steppers, etc.
//
// Usage (in an HTML file that loads React + Babel):
//
//   const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
//     "primaryColor": "#D97757",
//     "palette": ["#D97757", "#29261b", "#f6f4ef"],
//     "fontSize": 16,
//     "density": "regular",
//     "dark": false
//   }/*EDITMODE-END*/;
//
//   function App() {
//     const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
//     return (
//       <div style={{ fontSize: t.fontSize, color: t.primaryColor }}>
//         Hello
//         <TweaksPanel>
//           <TweakSection label="Typography" />
//           <TweakSlider label="Font size" value={t.fontSize} min={10} max={32} unit="px"
//                        onChange={(v) => setTweak('fontSize', v)} />
//           <TweakRadio  label="Density" value={t.density}
//                        options={['compact', 'regular', 'comfy']}
//                        onChange={(v) => setTweak('density', v)} />
//           <TweakSection label="Theme" />
//           <TweakColor  label="Primary" value={t.primaryColor}
//                        options={['#D97757', '#2A6FDB', '#1F8A5B', '#7A5AE0']}
//                        onChange={(v) => setTweak('primaryColor', v)} />
//           <TweakColor  label="Palette" value={t.palette}
//                        options={[['#D97757', '#29261b', '#f6f4ef'],
//                                  ['#475569', '#0f172a', '#f1f5f9']]}
//                        onChange={(v) => setTweak('palette', v)} />
//           <TweakToggle label="Dark mode" value={t.dark}
//                        onChange={(v) => setTweak('dark', v)} />
//         </TweaksPanel>
//       </div>
//     );
//   }
//
// ─────────────────────────────────────────────────────────────────────────────

const __TWEAKS_STYLE = `
  .twk-panel{position:fixed;right:16px;bottom:16px;z-index:2147483646;width:280px;
    max-height:calc(100vh - 32px);display:flex;flex-direction:column;
    transform:scale(var(--dc-inv-zoom,1));transform-origin:bottom right;
    background:rgba(250,249,247,.78);color:#29261b;
    -webkit-backdrop-filter:blur(24px) saturate(160%);backdrop-filter:blur(24px) saturate(160%);
    border:.5px solid rgba(255,255,255,.6);border-radius:14px;
    box-shadow:0 1px 0 rgba(255,255,255,.5) inset,0 12px 40px rgba(0,0,0,.18);
    font:11.5px/1.4 ui-sans-serif,system-ui,-apple-system,sans-serif;overflow:hidden}
  .twk-hd{display:flex;align-items:center;justify-content:space-between;
    padding:10px 8px 10px 14px;cursor:move;user-select:none}
  .twk-hd b{font-size:12px;font-weight:600;letter-spacing:.01em}
  .twk-x{appearance:none;border:0;background:transparent;color:rgba(41,38,27,.55);
    width:22px;height:22px;border-radius:6px;cursor:default;font-size:13px;line-height:1}
  .twk-x:hover{background:rgba(0,0,0,.06);color:#29261b}
  .twk-body{padding:2px 14px 14px;display:flex;flex-direction:column;gap:10px;
    overflow-y:auto;overflow-x:hidden;min-height:0;
    scrollbar-width:thin;scrollbar-color:rgba(0,0,0,.15) transparent}
  .twk-body::-webkit-scrollbar{width:8px}
  .twk-body::-webkit-scrollbar-track{background:transparent;margin:2px}
  .twk-body::-webkit-scrollbar-thumb{background:rgba(0,0,0,.15);border-radius:4px;
    border:2px solid transparent;background-clip:content-box}
  .twk-body::-webkit-scrollbar-thumb:hover{background:rgba(0,0,0,.25);
    border:2px solid transparent;background-clip:content-box}
  .twk-row{display:flex;flex-direction:column;gap:5px}
  .twk-row-h{flex-direction:row;align-items:center;justify-content:space-between;gap:10px}
  .twk-lbl{display:flex;justify-content:space-between;align-items:baseline;
    color:rgba(41,38,27,.72)}
  .twk-lbl>span:first-child{font-weight:500}
  .twk-val{color:rgba(41,38,27,.5);font-variant-numeric:tabular-nums}

  .twk-sect{font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
    color:rgba(41,38,27,.45);padding:10px 0 0}
  .twk-sect:first-child{padding-top:0}

  .twk-field{appearance:none;box-sizing:border-box;width:100%;min-width:0;height:26px;padding:0 8px;
    border:.5px solid rgba(0,0,0,.1);border-radius:7px;
    background:rgba(255,255,255,.6);color:inherit;font:inherit;outline:none}
  .twk-field:focus{border-color:rgba(0,0,0,.25);background:rgba(255,255,255,.85)}
  select.twk-field{padding-right:22px;
    background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'><path fill='rgba(0,0,0,.5)' d='M0 0h10L5 6z'/></svg>");
    background-repeat:no-repeat;background-position:right 8px center}

  .twk-slider{appearance:none;-webkit-appearance:none;width:100%;height:4px;margin:6px 0;
    border-radius:999px;background:rgba(0,0,0,.12);outline:none}
  .twk-slider::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;
    width:14px;height:14px;border-radius:50%;background:#fff;
    border:.5px solid rgba(0,0,0,.12);box-shadow:0 1px 3px rgba(0,0,0,.2);cursor:default}
  .twk-slider::-moz-range-thumb{width:14px;height:14px;border-radius:50%;
    background:#fff;border:.5px solid rgba(0,0,0,.12);box-shadow:0 1px 3px rgba(0,0,0,.2);cursor:default}

  .twk-seg{position:relative;display:flex;padding:2px;border-radius:8px;
    background:rgba(0,0,0,.06);user-select:none}
  .twk-seg-thumb{position:absolute;top:2px;bottom:2px;border-radius:6px;
    background:rgba(255,255,255,.9);box-shadow:0 1px 2px rgba(0,0,0,.12);
    transition:left .15s cubic-bezier(.3,.7,.4,1),width .15s}
  .twk-seg.dragging .twk-seg-thumb{transition:none}
  .twk-seg button{appearance:none;position:relative;z-index:1;flex:1;border:0;
    background:transparent;color:inherit;font:inherit;font-weight:500;min-height:22px;
    border-radius:6px;cursor:default;padding:4px 6px;line-height:1.2;
    overflow-wrap:anywhere}

  .twk-toggle{position:relative;width:32px;height:18px;border:0;border-radius:999px;
    background:rgba(0,0,0,.15);transition:background .15s;cursor:default;padding:0}
  .twk-toggle[data-on="1"]{background:#34c759}
  .twk-toggle i{position:absolute;top:2px;left:2px;width:14px;height:14px;border-radius:50%;
    background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.25);transition:transform .15s}
  .twk-toggle[data-on="1"] i{transform:translateX(14px)}

  .twk-num{display:flex;align-items:center;box-sizing:border-box;min-width:0;height:26px;padding:0 0 0 8px;
    border:.5px solid rgba(0,0,0,.1);border-radius:7px;background:rgba(255,255,255,.6)}
  .twk-num-lbl{font-weight:500;color:rgba(41,38,27,.6);cursor:ew-resize;
    user-select:none;padding-right:8px}
  .twk-num input{flex:1;min-width:0;height:100%;border:0;background:transparent;
    font:inherit;font-variant-numeric:tabular-nums;text-align:right;padding:0 8px 0 0;
    outline:none;color:inherit;-moz-appearance:textfield}
  .twk-num input::-webkit-inner-spin-button,.twk-num input::-webkit-outer-spin-button{
    -webkit-appearance:none;margin:0}
  .twk-num-unit{padding-right:8px;color:rgba(41,38,27,.45)}

  .twk-btn{appearance:none;height:26px;padding:0 12px;border:0;border-radius:7px;
    background:rgba(0,0,0,.78);color:#fff;font:inherit;font-weight:500;cursor:default}
  .twk-btn:hover{background:rgba(0,0,0,.88)}
  .twk-btn.secondary{background:rgba(0,0,0,.06);color:inherit}
  .twk-btn.secondary:hover{background:rgba(0,0,0,.1)}

  .twk-swatch{appearance:none;-webkit-appearance:none;width:56px;height:22px;
    border:.5px solid rgba(0,0,0,.1);border-radius:6px;padding:0;cursor:default;
    background:transparent;flex-shrink:0}
  .twk-swatch::-webkit-color-swatch-wrapper{padding:0}
  .twk-swatch::-webkit-color-swatch{border:0;border-radius:5.5px}
  .twk-swatch::-moz-color-swatch{border:0;border-radius:5.5px}

  .twk-chips{display:flex;gap:6px}
  .twk-chip{position:relative;appearance:none;flex:1;min-width:0;height:46px;
    padding:0;border:0;border-radius:6px;overflow:hidden;cursor:default;
    box-shadow:0 0 0 .5px rgba(0,0,0,.12),0 1px 2px rgba(0,0,0,.06);
    transition:transform .12s cubic-bezier(.3,.7,.4,1),box-shadow .12s}
  .twk-chip:hover{transform:translateY(-1px);
    box-shadow:0 0 0 .5px rgba(0,0,0,.18),0 4px 10px rgba(0,0,0,.12)}
  .twk-chip[data-on="1"]{box-shadow:0 0 0 1.5px rgba(0,0,0,.85),
    0 2px 6px rgba(0,0,0,.15)}
  .twk-chip>span{position:absolute;top:0;bottom:0;right:0;width:34%;
    display:flex;flex-direction:column;box-shadow:-1px 0 0 rgba(0,0,0,.1)}
  .twk-chip>span>i{flex:1;box-shadow:0 -1px 0 rgba(0,0,0,.1)}
  .twk-chip>span>i:first-child{box-shadow:none}
  .twk-chip svg{position:absolute;top:6px;left:6px;width:13px;height:13px;
    filter:drop-shadow(0 1px 1px rgba(0,0,0,.3))}
`;

// ── useTweaks ───────────────────────────────────────────────────────────────
// Single source of truth for tweak values. setTweak persists via the host
// (__edit_mode_set_keys → host rewrites the EDITMODE block on disk).
function useTweaks(defaults) {
  const [values, setValues] = React.useState(defaults);
  // Accepts either setTweak('key', value) or setTweak({ key: value, ... }) so a
  // useState-style call doesn't write a "[object Object]" key into the persisted
  // JSON block.
  const setTweak = React.useCallback((keyOrEdits, val) => {
    const edits = typeof keyOrEdits === 'object' && keyOrEdits !== null
      ? keyOrEdits : { [keyOrEdits]: val };
    setValues((prev) => ({ ...prev, ...edits }));
    window.parent.postMessage({ type: '__edit_mode_set_keys', edits }, '*');
    // Same-window signal so in-page listeners (deck-stage rail thumbnails)
    // can react — the parent message only reaches the host, not peers.
    window.dispatchEvent(new CustomEvent('tweakchange', { detail: edits }));
  }, []);
  return [values, setTweak];
}

// ── TweaksPanel ─────────────────────────────────────────────────────────────
// Floating shell. Registers the protocol listener BEFORE announcing
// availability — if the announce ran first, the host's activate could land
// before our handler exists and the toolbar toggle would silently no-op.
// The close button posts __edit_mode_dismissed so the host's toolbar toggle
// flips off in lockstep; the host echoes __deactivate_edit_mode back which
// is what actually hides the panel.
function TweaksPanel({ title = 'Tweaks', noDeckControls = false, children }) {
  const [open, setOpen] = React.useState(false);
  const dragRef = React.useRef(null);
  // Auto-inject a rail toggle when a <deck-stage> is on the page. The
  // toggle drives the deck's per-viewer _railVisible via window message;
  // state is mirrored from the same localStorage key the deck reads so
  // the control reflects reality across reloads. The mechanism is the
  // message — authors who want custom placement can post it directly
  // and pass noDeckControls to suppress this one.
  const hasDeckStage = React.useMemo(
    () => typeof document !== 'undefined' && !!document.querySelector('deck-stage'),
    [],
  );
  // deck-stage enables its rail in connectedCallback, but this panel can
  // mount before that element has upgraded. The initial read catches the
  // common case; the listener covers mounting first. (Older deck-stage.js
  // copies still wait for the host's __omelette_rail_enabled postMessage —
  // same listener handles those.)
  const [railEnabled, setRailEnabled] = React.useState(
    () => hasDeckStage && !!document.querySelector('deck-stage')?._railEnabled,
  );
  React.useEffect(() => {
    if (!hasDeckStage || railEnabled) return undefined;
    const onMsg = (e) => {
      if (e.data && e.data.type === '__omelette_rail_enabled') setRailEnabled(true);
    };
    window.addEventListener('message', onMsg);
    return () => window.removeEventListener('message', onMsg);
  }, [hasDeckStage, railEnabled]);
  const [railVisible, setRailVisible] = React.useState(() => {
    try { return localStorage.getItem('deck-stage.railVisible') !== '0'; } catch (e) { return true; }
  });
  const toggleRail = (on) => {
    setRailVisible(on);
    window.postMessage({ type: '__deck_rail_visible', on }, '*');
  };
  const offsetRef = React.useRef({ x: 16, y: 16 });
  const PAD = 16;

  const clampToViewport = React.useCallback(() => {
    const panel = dragRef.current;
    if (!panel) return;
    const w = panel.offsetWidth, h = panel.offsetHeight;
    const maxRight = Math.max(PAD, window.innerWidth - w - PAD);
    const maxBottom = Math.max(PAD, window.innerHeight - h - PAD);
    offsetRef.current = {
      x: Math.min(maxRight, Math.max(PAD, offsetRef.current.x)),
      y: Math.min(maxBottom, Math.max(PAD, offsetRef.current.y)),
    };
    panel.style.right = offsetRef.current.x + 'px';
    panel.style.bottom = offsetRef.current.y + 'px';
  }, []);

  React.useEffect(() => {
    if (!open) return;
    clampToViewport();
    if (typeof ResizeObserver === 'undefined') {
      window.addEventListener('resize', clampToViewport);
      return () => window.removeEventListener('resize', clampToViewport);
    }
    const ro = new ResizeObserver(clampToViewport);
    ro.observe(document.documentElement);
    return () => ro.disconnect();
  }, [open, clampToViewport]);

  React.useEffect(() => {
    const onMsg = (e) => {
      const t = e?.data?.type;
      if (t === '__activate_edit_mode') setOpen(true);
      else if (t === '__deactivate_edit_mode') setOpen(false);
    };
    window.addEventListener('message', onMsg);
    window.parent.postMessage({ type: '__edit_mode_available' }, '*');
    return () => window.removeEventListener('message', onMsg);
  }, []);

  const dismiss = () => {
    setOpen(false);
    window.parent.postMessage({ type: '__edit_mode_dismissed' }, '*');
  };

  const onDragStart = (e) => {
    const panel = dragRef.current;
    if (!panel) return;
    const r = panel.getBoundingClientRect();
    const sx = e.clientX, sy = e.clientY;
    const startRight = window.innerWidth - r.right;
    const startBottom = window.innerHeight - r.bottom;
    const move = (ev) => {
      offsetRef.current = {
        x: startRight - (ev.clientX - sx),
        y: startBottom - (ev.clientY - sy),
      };
      clampToViewport();
    };
    const up = () => {
      window.removeEventListener('mousemove', move);
      window.removeEventListener('mouseup', up);
    };
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', up);
  };

  if (!open) return null;
  return (
    <>
      <style>{__TWEAKS_STYLE}</style>
      <div ref={dragRef} className="twk-panel" data-noncommentable=""
           style={{ right: offsetRef.current.x, bottom: offsetRef.current.y }}>
        <div className="twk-hd" onMouseDown={onDragStart}>
          <b>{title}</b>
          <button className="twk-x" aria-label="Close tweaks"
                  onMouseDown={(e) => e.stopPropagation()}
                  onClick={dismiss}>✕</button>
        </div>
        <div className="twk-body">
          {children}
          {hasDeckStage && railEnabled && !noDeckControls && (
            <TweakSection label="Deck">
              <TweakToggle label="Thumbnail rail" value={railVisible} onChange={toggleRail} />
            </TweakSection>
          )}
        </div>
      </div>
    </>
  );
}

// ── Layout helpers ──────────────────────────────────────────────────────────

function TweakSection({ label, children }) {
  return (
    <>
      <div className="twk-sect">{label}</div>
      {children}
    </>
  );
}

function TweakRow({ label, value, children, inline = false }) {
  return (
    <div className={inline ? 'twk-row twk-row-h' : 'twk-row'}>
      <div className="twk-lbl">
        <span>{label}</span>
        {value != null && <span className="twk-val">{value}</span>}
      </div>
      {children}
    </div>
  );
}

// ── Controls ────────────────────────────────────────────────────────────────

function TweakSlider({ label, value, min = 0, max = 100, step = 1, unit = '', onChange }) {
  return (
    <TweakRow label={label} value={`${value}${unit}`}>
      <input type="range" className="twk-slider" min={min} max={max} step={step}
             value={value} onChange={(e) => onChange(Number(e.target.value))} />
    </TweakRow>
  );
}

function TweakToggle({ label, value, onChange }) {
  return (
    <div className="twk-row twk-row-h">
      <div className="twk-lbl"><span>{label}</span></div>
      <button type="button" className="twk-toggle" data-on={value ? '1' : '0'}
              role="switch" aria-checked={!!value}
              onClick={() => onChange(!value)}><i /></button>
    </div>
  );
}

function TweakRadio({ label, value, options, onChange }) {
  const trackRef = React.useRef(null);
  const [dragging, setDragging] = React.useState(false);
  // The active value is read by pointer-move handlers attached for the lifetime
  // of a drag — ref it so a stale closure doesn't fire onChange for every move.
  const valueRef = React.useRef(value);
  valueRef.current = value;

  // Segments wrap mid-word once per-segment width runs out. The track is
  // ~248px (280 panel − 28 body pad − 4 seg pad), each button loses 12px
  // to its own padding, and 11.5px system-ui averages ~6.3px/char — so 2
  // options fit ~16 chars each, 3 fit ~10. Past that (or >3 options), fall
  // back to a dropdown rather than wrap.
  const labelLen = (o) => String(typeof o === 'object' ? o.label : o).length;
  const maxLen = options.reduce((m, o) => Math.max(m, labelLen(o)), 0);
  const fitsAsSegments = maxLen <= ({ 2: 16, 3: 10 }[options.length] ?? 0);
  if (!fitsAsSegments) {
    // <select> emits strings — map back to the original option value so the
    // fallback stays type-preserving (numbers, booleans) like the segment path.
    const resolve = (s) => {
      const m = options.find((o) => String(typeof o === 'object' ? o.value : o) === s);
      return m === undefined ? s : typeof m === 'object' ? m.value : m;
    };
    return <TweakSelect label={label} value={value} options={options}
                        onChange={(s) => onChange(resolve(s))} />;
  }
  const opts = options.map((o) => (typeof o === 'object' ? o : { value: o, label: o }));
  const idx = Math.max(0, opts.findIndex((o) => o.value === value));
  const n = opts.length;

  const segAt = (clientX) => {
    const r = trackRef.current.getBoundingClientRect();
    const inner = r.width - 4;
    const i = Math.floor(((clientX - r.left - 2) / inner) * n);
    return opts[Math.max(0, Math.min(n - 1, i))].value;
  };

  const onPointerDown = (e) => {
    setDragging(true);
    const v0 = segAt(e.clientX);
    if (v0 !== valueRef.current) onChange(v0);
    const move = (ev) => {
      if (!trackRef.current) return;
      const v = segAt(ev.clientX);
      if (v !== valueRef.current) onChange(v);
    };
    const up = () => {
      setDragging(false);
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  };

  return (
    <TweakRow label={label}>
      <div ref={trackRef} role="radiogroup" onPointerDown={onPointerDown}
           className={dragging ? 'twk-seg dragging' : 'twk-seg'}>
        <div className="twk-seg-thumb"
             style={{ left: `calc(2px + ${idx} * (100% - 4px) / ${n})`,
                      width: `calc((100% - 4px) / ${n})` }} />
        {opts.map((o) => (
          <button key={o.value} type="button" role="radio" aria-checked={o.value === value}>
            {o.label}
          </button>
        ))}
      </div>
    </TweakRow>
  );
}

function TweakSelect({ label, value, options, onChange }) {
  return (
    <TweakRow label={label}>
      <select className="twk-field" value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((o) => {
          const v = typeof o === 'object' ? o.value : o;
          const l = typeof o === 'object' ? o.label : o;
          return <option key={v} value={v}>{l}</option>;
        })}
      </select>
    </TweakRow>
  );
}

function TweakText({ label, value, placeholder, onChange }) {
  return (
    <TweakRow label={label}>
      <input className="twk-field" type="text" value={value} placeholder={placeholder}
             onChange={(e) => onChange(e.target.value)} />
    </TweakRow>
  );
}

function TweakNumber({ label, value, min, max, step = 1, unit = '', onChange }) {
  const clamp = (n) => {
    if (min != null && n < min) return min;
    if (max != null && n > max) return max;
    return n;
  };
  const startRef = React.useRef({ x: 0, val: 0 });
  const onScrubStart = (e) => {
    e.preventDefault();
    startRef.current = { x: e.clientX, val: value };
    const decimals = (String(step).split('.')[1] || '').length;
    const move = (ev) => {
      const dx = ev.clientX - startRef.current.x;
      const raw = startRef.current.val + dx * step;
      const snapped = Math.round(raw / step) * step;
      onChange(clamp(Number(snapped.toFixed(decimals))));
    };
    const up = () => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  };
  return (
    <div className="twk-num">
      <span className="twk-num-lbl" onPointerDown={onScrubStart}>{label}</span>
      <input type="number" value={value} min={min} max={max} step={step}
             onChange={(e) => onChange(clamp(Number(e.target.value)))} />
      {unit && <span className="twk-num-unit">{unit}</span>}
    </div>
  );
}

// Relative-luminance contrast pick — checkmarks drawn over a swatch need to
// read on both #111 and #fafafa without per-option configuration. Hex input
// only (#rgb / #rrggbb); named or rgb()/hsl() colors fall through to "light".
function __twkIsLight(hex) {
  const h = String(hex).replace('#', '');
  const x = h.length === 3 ? h.replace(/./g, (c) => c + c) : h.padEnd(6, '0');
  const n = parseInt(x.slice(0, 6), 16);
  if (Number.isNaN(n)) return true;
  const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
  return r * 299 + g * 587 + b * 114 > 148000;
}

const __TwkCheck = ({ light }) => (
  <svg viewBox="0 0 14 14" aria-hidden="true">
    <path d="M3 7.2 5.8 10 11 4.2" fill="none" strokeWidth="2.2"
          strokeLinecap="round" strokeLinejoin="round"
          stroke={light ? 'rgba(0,0,0,.78)' : '#fff'} />
  </svg>
);

// TweakColor — curated color/palette picker. Each option is either a single
// hex string or an array of 1-5 hex strings; the card adapts — a lone color
// renders solid, a palette renders colors[0] as the hero (left ~2/3) with the
// rest stacked in a sharp column on the right. onChange emits the
// option in the shape it was passed (string stays string, array stays array).
// Without options it falls back to the native color input for back-compat.
function TweakColor({ label, value, options, onChange }) {
  if (!options || !options.length) {
    return (
      <div className="twk-row twk-row-h">
        <div className="twk-lbl"><span>{label}</span></div>
        <input type="color" className="twk-swatch" value={value}
               onChange={(e) => onChange(e.target.value)} />
      </div>
    );
  }
  // Native <input type=color> emits lowercase hex per the HTML spec, so
  // compare case-insensitively. String() guards JSON.stringify(undefined),
  // which returns the primitive undefined (no .toLowerCase).
  const key = (o) => String(JSON.stringify(o)).toLowerCase();
  const cur = key(value);
  return (
    <TweakRow label={label}>
      <div className="twk-chips" role="radiogroup">
        {options.map((o, i) => {
          const colors = Array.isArray(o) ? o : [o];
          const [hero, ...rest] = colors;
          const sup = rest.slice(0, 4);
          const on = key(o) === cur;
          return (
            <button key={i} type="button" className="twk-chip" role="radio"
                    aria-checked={on} data-on={on ? '1' : '0'}
                    aria-label={colors.join(', ')} title={colors.join(' · ')}
                    style={{ background: hero }}
                    onClick={() => onChange(o)}>
              {sup.length > 0 && (
                <span>
                  {sup.map((c, j) => <i key={j} style={{ background: c }} />)}
                </span>
              )}
              {on && <__TwkCheck light={__twkIsLight(hero)} />}
            </button>
          );
        })}
      </div>
    </TweakRow>
  );
}

function TweakButton({ label, onClick, secondary = false }) {
  return (
    <button type="button" className={secondary ? 'twk-btn secondary' : 'twk-btn'}
            onClick={onClick}>{label}</button>
  );
}

Object.assign(window, {
  useTweaks, TweaksPanel, TweakSection, TweakRow,
  TweakSlider, TweakToggle, TweakRadio, TweakSelect,
  TweakText, TweakNumber, TweakColor, TweakButton,
});


// ============================ data.jsx ============================

// data.jsx — Fixtures for Maquinaria Pesada cockpit
// 22 episodios = 15 M + 7 T

// Live producción
const LIVE_PROC = [
  { id: "p1", cmd: "generar_episodio_v2.py M5",   pid: 41207, t: "00:04:22", cost: "0.42€" },
  { id: "p2", cmd: "validar_episodio.py M3",       pid: 41318, t: "00:00:14", cost: "0.01€" },
];

const RECENT_FILES = [
  { path: "Guiones/M5_guion.txt",       t: "hace 12 s",  by: "Claude" },
  { path: "episodios/M3_T1_v4.mp3",     t: "hace 1 min", by: "ElevenLabs" },
  { path: "escaletas/M5.md",            t: "hace 3 min", by: "Claude" },
  { path: "logs/2026-05-12_M3.jsonl",   t: "hace 4 min", by: "runner" },
];

// Tokens consumption
const TOKEN_DATA = {
  total_30d: 18_420_000,
  cost_30d: 142.18,
  budget: 250,
  byModel: [
    { model: "claude-haiku-4.5",  tokens: 8_120_000, cost: 18.40, share: 44 },
    { model: "claude-sonnet-4.6", tokens: 5_840_000, cost: 78.20, share: 32 },
    { model: "claude-opus-4.7",   tokens:   780_000, cost: 36.80, share:  4 },
    { model: "gpt-4o-mini",       tokens: 2_960_000, cost:  4.80, share: 16 },
    { model: "whisper-local",     tokens:   720_000, cost:  0.00, share:  4 },
  ],
  byKind: [
    { kind: "Generación de guiones", pct: 52 },
    { kind: "Validación dual",       pct: 28 },
    { kind: "Mejorar con IA",        pct: 12 },
    { kind: "Asistente",             pct:  5 },
    { kind: "Otros",                 pct:  3 },
  ],
};

// Pipeline nodes (canónico)
const PIPELINE = [
  { id: "src",     label: "PDF temático",     kind: "input",  x:  60, y: 220, code: "PDFs/Mn.pdf" },
  { id: "claude1", label: "Claude · guion",   kind: "ai",     x: 240, y: 220, code: "generar_guion.py" },
  { id: "guion",   label: "Guion",            kind: "art",    x: 420, y: 220, code: "Guiones/Mn.txt" },
  { id: "claude2", label: "Claude · escaleta",kind: "ai",     x: 600, y: 120, code: "generate_escaleta.py" },
  { id: "esc",     label: "Escaleta",         kind: "art",    x: 780, y: 120, code: "escaletas/Mn.md" },
  { id: "gpt",     label: "GPT · debate",     kind: "ai",     x: 600, y: 320, code: "dual_debate.py" },
  { id: "val",     label: "Validación",       kind: "art",    x: 780, y: 320, code: "logs/dual_Mn.json" },
  { id: "eleven",  label: "ElevenLabs · TTS", kind: "ai",     x: 960, y: 220, code: "generar_episodio_v2.py" },
  { id: "mp3",     label: "Episodio",         kind: "out",    x:1140, y: 220, code: "episodios/Mn.mp3" },
  { id: "kling",   label: "Kling · vídeo",    kind: "ai",     x:1140, y:  80, code: "kling_runner.py" },
  { id: "mp4",     label: "Vídeo",            kind: "out",    x:1140, y: -20, code: "videopodcast/Mn.mp4" },
];

const EDGES = [
  ["src", "claude1"], ["claude1", "guion"],
  ["guion", "claude2"], ["claude2", "esc"],
  ["guion", "gpt"], ["gpt", "val"],
  ["esc", "eleven"], ["val", "eleven"],
  ["eleven", "mp3"], ["mp3", "kling"], ["kling", "mp4"],
];

// AI usage log (synthetic)
const AI_LOG = [
  { t: "12:42:18", model: "haiku-4.5",  kind: "Mejorar con IA",  tok:  1240, cost: 0.003 },
  { t: "12:41:50", model: "sonnet-4.6", kind: "Generar guion",   tok: 14820, cost: 0.198 },
  { t: "12:39:02", model: "haiku-4.5",  kind: "Asistente",       tok:   820, cost: 0.002 },
  { t: "12:36:11", model: "sonnet-4.6", kind: "Generar guion",   tok: 12100, cost: 0.162 },
  { t: "12:32:48", model: "gpt-4o-mini",kind: "Debate dual",      tok:  4400, cost: 0.001 },
];

Object.assign(window, {
  MODULES, EPISODES, LIVE_PROC, RECENT_FILES, TOKEN_DATA,
  PIPELINE, EDGES, AI_LOG, GUION_PREVIEW, CHECKS_M3, KINDS,
  SOURCES, pathOf,
});

// ── Backend bootstrap ────────────────────────────────────────────────
// Si hay servidor (web_server.py) sobreescribimos los fixtures con datos
// reales del repo. Si la llamada falla (servidor parado, file://) los
// fixtures de arriba se quedan como degradación elegante.
window.__BOOTSTRAP__ = (async function bootstrap() {
  try {
    const res = await fetch("/api/bootstrap", { cache: "no-store" });
    if (!res.ok) throw new Error("bootstrap " + res.status);
    const d = await res.json();
    if (Array.isArray(d.MODULES) && d.MODULES.length)             window.MODULES = d.MODULES;
    if (Array.isArray(d.EPISODES) && d.EPISODES.length)           window.EPISODES = d.EPISODES;
    if (Array.isArray(d.LIVE_PROC))                                window.LIVE_PROC = d.LIVE_PROC;
    if (Array.isArray(d.RECENT_FILES) && d.RECENT_FILES.length)    window.RECENT_FILES = d.RECENT_FILES;
    if (d.TOKEN_DATA && Array.isArray(d.TOKEN_DATA.byModel) && d.TOKEN_DATA.byModel.length) {
      window.TOKEN_DATA = d.TOKEN_DATA;
      if (Array.isArray(d.TOKEN_DATA.log) && d.TOKEN_DATA.log.length) {
        window.AI_LOG = d.TOKEN_DATA.log;
      }
    }
    if (d.ECONOMICS) window.ECONOMICS = d.ECONOMICS;
    applyBootstrap(d);  // capa de datos sin globals (data.ts)
    window.__BOOTSTRAP_OK__ = true;
    return d;
  } catch (e) {
    window.__BOOTSTRAP_OK__ = false;
    window.__BOOTSTRAP_ERR__ = String(e);
    return null;
  }
})();


// ============================ ui.jsx ============================

// ============================ shell.jsx ============================

// shell.jsx — Sidebar + topbar + AI drawer

function Sidebar({ current, onNav }) {
  return (
    <aside className="sb">
      <div className="sb-brand">
        <div className="sb-logo">MP</div>
        <div>
          <div className="sb-title">Maquinaria<br/>Pesada</div>
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
                  className={`sb-item ${active ? "active" : ""}`}
                  onClick={() => wired && onNav(it.id)}
                  style={{ opacity: wired ? 1 : 0.42, cursor: wired ? "pointer" : "not-allowed" }}
                  title={wired ? "" : "Página no incluida en este prototipo"}
                >
                  <span className="sb-item-num">{it.num}</span>
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
        {LIVE_PROC.map((p) => (
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

// ── Topbar ─────────────────────────────────────────────────
function Topbar({ crumbs, onCrumb, onOpenAI, onOpenFix }) {
  return (
    <div className="topbar">
      <div className="crumbs">
        {crumbs.map((c, i) => (
          <React.Fragment key={i}>
            {i > 0 && <span className="sep">/</span>}
            {c.id && i < crumbs.length - 1
              ? <a onClick={() => onCrumb(c.id)}>{c.label}</a>
              : <span className={i === crumbs.length - 1 ? "cur" : ""}>{c.label}</span>}
          </React.Fragment>
        ))}
      </div>
      <div className="topbar-actions">
        <div className="row gap-4 dim mono" style={{ fontSize: 11, letterSpacing: "0.08em", marginRight: 8 }}>
          <span>163 <span className="muted">tests</span> <span style={{ color: "var(--ok)" }}>●</span></span>
          <span className="muted">·</span>
          <span>30bfb39</span>
        </div>
        {onOpenFix && (
          <Btn kind="danger" sm onClick={onOpenFix} icon={<Icon name="wrench" size={11}/>}>
            Arreglar con Claude
          </Btn>
        )}
        <Btn kind="primary" sm onClick={onOpenAI} icon={<Icon name="spark" size={11}/>}>
          Mejorar con IA
        </Btn>
      </div>
    </div>
  );
}

// ── AI Drawer ──────────────────────────────────────────────
function AIDrawer({ open, onClose, mode, context }) {
  const [input, setInput] = React.useState("");
  const [messages, setMessages] = React.useState([]);
  const [streaming, setStreaming] = React.useState(false);
  const [streamText, setStreamText] = React.useState("");

  // Seed messages based on mode/context when opened
  React.useEffect(() => {
    if (!open) return;
    if (mode === "fix") {
      setMessages([
        { role: "system", body: context?.error || "Sesión Claude para arreglar episodio." },
      ]);
    } else {
      setMessages([]);
    }
    setStreamText("");
  }, [open, mode, context?.id]);

  const [lastUsage, setLastUsage] = React.useState(null);

  const send = async () => {
    if (!input.trim()) return;
    const userMsg = { role: "user", body: input };
    const userText = input;
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setStreaming(true);
    setStreamText("");

    const FALLBACK = mode === "fix"
      ? "He inspeccionado el episodio.\n\n1. El audio M3_T2 falla en el bloque 4: 'Atención escalada' — ElevenLabs devolvió 502 en el segundo intento.\n2. Voy a regenerar SOLO ese bloque con la voz María y volver a concatenar.\n3. No tocaré el guion ni la escaleta.\n\n¿Procedo?"
      : "He analizado este episodio. Mejoras sugeridas:\n\n→ El bloque 3 del guion es 22% más largo que la media. Considera dividirlo.\n→ María lleva 4 turnos seguidos entre 18:00 y 21:30. Insertar una intervención de Iago.\n→ La escaleta no menciona RoPE — está en el guion. Refrescar.\n\n[fallback offline]";

    // Llamada real al backend; si falla → fallback simulado.
    let reply = FALLBACK;
    let usage = null;
    try {
      const res = await fetch("/api/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode,
          target: context && (context.target || context.id) ? (context.target || context.id) : null,
          message: userText,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data && data.text) {
          reply = data.text;
          usage = data.usage || null;
        }
      }
    } catch (_) { /* keep fallback */ }

    setLastUsage(usage);

    // Efecto typewriter sobre la respuesta final (real o fallback)
    let i = 0;
    const tick = () => {
      i += Math.floor(Math.random() * 4) + 2;
      setStreamText(reply.slice(0, i));
      if (i < reply.length) setTimeout(tick, 18);
      else {
        setStreaming(false);
        setMessages((m) => [...m, { role: "ai", body: reply }]);
        setStreamText("");
      }
    };
    tick();
  };

  const onKey = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } };

  const title = mode === "fix" ? "Arreglar con Claude" : "Mejorar con IA";

  return (
    <React.Fragment>
      <div className={`drawer-overlay ${open ? "open" : ""}`} onClick={onClose} />
      <aside className={`drawer ${open ? "open" : ""}`}>
        <div className="drawer-hd">
          <div className="drawer-title">
            <Icon name={mode === "fix" ? "wrench" : "spark"} size={14}/>
            {title}
          </div>
          <button className="btn ghost sm" onClick={onClose}><Icon name="close" size={11}/></button>
        </div>

        <div className="drawer-body">
          {context && (
            <div className="ai-msg context">
              <div className="role">Contexto</div>
              <div style={{ marginTop: 6, color: "var(--text)", fontFamily: "var(--f-mono)", fontSize: 11 }}>
                <div><span className="muted">target:</span> {context.target || "—"}</div>
                {context.error && (
                  <pre style={{ margin: "4px 0 0", whiteSpace: "pre-wrap", color: "var(--alert)" }}>
                    {context.error}
                  </pre>
                )}
              </div>
            </div>
          )}

          {messages.length === 0 && !streaming && (
            <div style={{ color: "var(--text-mute)", fontFamily: "var(--f-mono)", fontSize: 11, marginTop: 12 }}>
              {mode === "fix"
                ? "Claude tiene el contexto del fallo. Escribe instrucciones o pulsa Enter para que proponga un fix."
                : "Pregunta lo que necesites sobre este recurso. Claude tiene acceso a archivos relacionados (PDFs, guion, escaleta, logs)."}
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`ai-msg ${m.role}`}>
              <div className="role">{m.role === "user" ? "Tú" : m.role === "ai" ? "Claude" : "Sistema"}</div>
              <div className="body" style={{ whiteSpace: "pre-wrap" }}>{m.body}</div>
            </div>
          ))}

          {streaming && (
            <div className="ai-msg ai">
              <div className="role">Claude</div>
              <div className="body" style={{ whiteSpace: "pre-wrap" }}>
                {streamText}
                <span className="ai-cursor" />
              </div>
            </div>
          )}
        </div>

        <div className="drawer-foot">
          <input
            className="ai-input"
            placeholder={mode === "fix" ? "Describe qué hay que arreglar…" : "Pregúntale algo…"}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKey}
          />
          <Btn kind="primary" sm onClick={send}><Icon name="arrow" size={11}/> Enviar</Btn>
        </div>

        <div className="drawer-foot" style={{ borderTop: 0, paddingTop: 0 }}>
          <div className="ai-cost">
            {lastUsage ? (
              <React.Fragment>
                <span>Modelo <b>{lastUsage.model}</b></span>
                <span>Tokens <b>{(lastUsage.input_tokens || 0) + (lastUsage.output_tokens || 0)}</b></span>
                <span>Coste <b>{((lastUsage.cost_usd || 0)).toFixed(4)}$</b></span>
              </React.Fragment>
            ) : (
              <React.Fragment>
                <span>Modelo <b>claude-haiku-4-5</b></span>
                <span>Tokens <b>—</b></span>
                <span>Coste <b>—</b></span>
              </React.Fragment>
            )}
          </div>
        </div>
      </aside>
    </React.Fragment>
  );
}

Object.assign(window, { Sidebar, Topbar, AIDrawer, NAV_GROUPS, WIRED, srcFor, ghLink, REPO, REPO_REF });


// ============================ pages-1.jsx ============================

// pages-1.jsx — Inicio + Master + Módulo

// ════════════════════════════════════════════════════════════
// INICIO — was "Landing". Now also explains the IA reorganization.
// ════════════════════════════════════════════════════════════
function PageInicio({ onNav, onOpenAI }) {
  const okMods   = MODULES.filter(m => m.status === "ok").length;
  const warnMods = MODULES.filter(m => m.status === "warn").length;
  const emptyMods= MODULES.filter(m => m.status === "empty" || m.status === "alert").length;

  return (
    <div className="content">
      <PageHeader
        title="Estado de obra"
        sub="Maquinaria Pesada · Cockpit · 12 may 2026 · 12:42:18"
      />
      <SourcePills files={srcFor("home")}/>

      {/* ── KPIs globales ── */}
      <div className="kpi-grid mb-12">
        <Kpi label="Módulos completos"  value={`${okMods}`}    unit={`/ ${MODULES.length}`} delta="+1 esta semana"        deltaDir="up" />
        <Kpi label="Episodios"           value="22"             unit="total"                 delta="15 M · 7 T"                          />
        <Kpi label="Producción · 30d"    value="142"            unit="€"                     delta="56% del budget (250€)" deltaDir="up" />
        <Kpi label="Tokens · 30d"        value="18.4"           unit="M"                     delta="-12% vs mes anterior"  deltaDir="dn" />
        <Kpi label="Tests"               value="163"            unit="✓"                     delta="ruff clean · pytest ✓" deltaDir="up" />
      </div>

      <div className="grid gap-8" style={{ gridTemplateColumns: "1.4fr 1fr" }}>
        {/* ── Mapa de la app (reorganización) ── */}
        <Panel
          title={<span><Icon name="grid" size={12}/> &nbsp;Mapa de la cabina ↔ repositorio</span>}
          meta="13 páginas conectadas con su código fuente"
          actions={<Btn sm kind="ghost" onClick={() => window.open(REPO + "/tree/" + REPO_REF + "/cockpit", "_blank")}>
            <Icon name="folder" size={10}/> Ver cockpit/
          </Btn>}
        >
          <div className="mono dim" style={{ fontSize: 11, marginBottom: 14, lineHeight: 1.6 }}>
            Cada página de la cabina apunta a los archivos del repo que la implementan. Antes: 16 páginas
            sin agrupar, "Master" oculta como #0, redundancia entre Estado/Master, chat libre como página
            y como drawer. Ahora: 5 dominios + un asistente como drawer global, todos enlazados a su
            código fuente en <span style={{ color: "var(--y)" }}>bakero/maquinaria-pesada</span>.
          </div>

          {NAV_GROUPS.map((g) => (
            <div key={g.label} style={{ marginBottom: 14 }}>
              <div className="h3" style={{ marginBottom: 6, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ width: 4, height: 12, background: "var(--y)" }}/>
                {g.label}
                <span className="muted mono" style={{ fontSize: 9, marginLeft: "auto" }}>
                  {g.items.length} {g.items.length === 1 ? "página" : "páginas"}
                </span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 6 }}>
                {g.items.map(it => {
                  const wired = WIRED.has(it.id);
                  return (
                    <div
                      key={it.id}
                      onClick={() => wired && onNav(it.id)}
                      style={{
                        border: "1px solid var(--border)",
                        background: wired ? "var(--panel-2)" : "transparent",
                        padding: "10px 12px",
                        cursor: wired ? "pointer" : "default",
                        opacity: wired ? 1 : 0.55,
                        position: "relative",
                      }}
                    >
                      <div className="row gap-3" style={{ marginBottom: 6 }}>
                        <Icon name={it.icon} size={11}/>
                        <span className="mono muted" style={{ fontSize: 9 }}>{it.num}</span>
                        <span className="display" style={{ fontSize: 11, color: wired ? "var(--text)" : "var(--text-mute)" }}>
                          {it.label}
                        </span>
                        {wired && <span className="badge y" style={{ marginLeft: "auto", padding: "0 4px", fontSize: 8 }}>LIVE</span>}
                      </div>
                      {it.src && it.src.length > 0 && (
                        <div className="col" style={{ gap: 2, paddingLeft: 22 }}>
                          {it.src.slice(0, 3).map((s) => (
                            <a key={s}
                               href={ghLink(s)}
                               target="_blank"
                               rel="noopener"
                               onClick={(e) => e.stopPropagation()}
                               className="mono"
                               style={{
                                 fontSize: 9.5,
                                 color: "var(--text-mute)",
                                 textDecoration: "none",
                                 letterSpacing: 0,
                                 wordBreak: "break-all",
                                 lineHeight: 1.35,
                               }}
                               title={`Abrir ${s} en GitHub`}
                               onMouseEnter={(e) => e.currentTarget.style.color = "var(--y)"}
                               onMouseLeave={(e) => e.currentTarget.style.color = "var(--text-mute)"}>
                              {s}
                            </a>
                          ))}
                          {it.src.length > 3 && (
                            <span className="mono" style={{ fontSize: 9, color: "var(--text-mute)", fontStyle: "italic" }}>
                              + {it.src.length - 3} más
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </Panel>

        <div className="col gap-8">
          {/* ── Semáforo módulos ── */}
          <Panel
            title={<span><Icon name="module" size={12}/> &nbsp;Semáforo de módulos</span>}
            actions={<Btn sm onClick={() => onNav("master")}><Icon name="arrow" size={10}/> Ver Master</Btn>}
          >
            <div className="grid" style={{ gridTemplateColumns: "repeat(5, 1fr)", gap: 4 }}>
              {MODULES.map((m) => (
                <div
                  key={m.id}
                  onClick={() => onNav("master")}
                  style={{
                    background: "var(--panel-2)",
                    border: "1px solid var(--border)",
                    padding: "8px 6px",
                    textAlign: "center",
                    cursor: "pointer",
                  }}
                >
                  <div className="mono" style={{ fontSize: 10, color: "var(--y)" }}>{m.id}</div>
                  <div style={{ margin: "5px auto 4px" }}>
                    <StatusDot status={m.status === "empty" ? "empty" : m.status}/>
                  </div>
                  <div className="mono dim" style={{ fontSize: 9 }}>{m.pct}%</div>
                </div>
              ))}
            </div>
            <div className="row gap-8 mt-12 mono" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.08em" }}>
              <span><StatusDot status="ok" sm/> &nbsp;{okMods} OK</span>
              <span><StatusDot status="warn" sm/> &nbsp;{warnMods} EN CURSO</span>
              <span><StatusDot status="empty" sm/> &nbsp;{emptyMods} PENDIENTE</span>
            </div>
          </Panel>

          {/* ── Últimos archivos ── */}
          <Panel
            title={<span><Icon name="folder" size={12}/> &nbsp;Recientes</span>}
            meta="auto-refresh"
          >
            {RECENT_FILES.map((f, i) => (
              <div key={i} className="row" style={{
                padding: "6px 0",
                borderBottom: i < RECENT_FILES.length - 1 ? "1px solid var(--border)" : "none",
                fontSize: 12, fontFamily: "var(--f-mono)",
              }}>
                <span style={{ flex: 1, color: "var(--text)" }}>{f.path}</span>
                <span style={{ color: "var(--text-mute)", fontSize: 10 }}>{f.t}</span>
              </div>
            ))}
          </Panel>

          {/* ── Alertas ── */}
          <Panel title={<span style={{ color: "var(--alert)" }}><Icon name="dot" size={10}/> &nbsp;Atención</span>}>
            <div className="col gap-4">
              <div className="row gap-4" style={{ padding: "6px 0", fontSize: 13 }}>
                <StatusDot status="alert" sm/>
                <span className="fill">M3_T2 · audio falló (502 ElevenLabs)</span>
                <Btn sm kind="ghost" onClick={() => onNav("episodio", "M3_T2")}>ABRIR</Btn>
              </div>
              <div className="row gap-4" style={{ padding: "6px 0", fontSize: 13 }}>
                <StatusDot status="warn" sm/>
                <span className="fill">M8 · guion truncado en bloque 4</span>
                <Btn sm kind="ghost" onClick={() => onNav("modulo", "M8")}>ABRIR</Btn>
              </div>
              <div className="row gap-4" style={{ padding: "6px 0", fontSize: 13 }}>
                <StatusDot status="warn" sm/>
                <span className="fill">Saldo ElevenLabs: 8.40€ (recargar &lt; 10€)</span>
                <Btn sm kind="ghost" onClick={() => onNav("consumo")}>RECARGAR</Btn>
              </div>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// MASTER — list/matrix/gantt views (3 variants tweakable)
// ════════════════════════════════════════════════════════════
function PageMaster({ onNav, onOpenAI, view, density }) {
  return (
    <div className="content">
      <PageHeader
        title="Master M0 — M14"
        sub="Vista global de los 15 módulos · 22 episodios"
        actions={null}
      />
      <SourcePills files={srcFor("master")}/>

      {/* View switcher */}
      <div className="row mb-8" style={{ justifyContent: "space-between" }}>
        <div className="row gap-3">
          {["lista", "matriz", "gantt"].map((v) => (
            <div
              key={v}
              className={`btn sm ${view === v ? "primary" : ""}`}
              onClick={() => window.__setMasterView && window.__setMasterView(v)}
              style={{ cursor: "pointer" }}
            >
              {v.toUpperCase()}
            </div>
          ))}
        </div>
        <div className="row gap-3">
          <Btn sm kind="ghost" icon={<Icon name="refresh" size={10}/>}
               onClick={() => window.location.reload()}>Re-scan</Btn>
          <Btn sm onClick={() => onOpenAI({ target: "Master · M0–M14", purpose: "improve" })}
               icon={<Icon name="spark" size={10}/>}>Mejorar con IA</Btn>
        </div>
      </div>

      {view === "lista" && <MasterListView onNav={onNav} density={density}/>}
      {view === "matriz"&& <MasterMatrixView onNav={onNav}/>}
      {view === "gantt" && <MasterGanttView onNav={onNav}/>}
    </div>
  );
}

// ── Master · Lista ───────────────────────────────────────
function MasterListView({ onNav, density }) {
  const rowH = density === "compact" ? 36 : density === "comfy" ? 56 : 44;
  return (
    <Panel noPad>
      <table className="tbl">
        <thead>
          <tr>
            <th style={{ width: 60 }}>ID</th>
            <th>Módulo</th>
            <th style={{ width: 100 }}>Eps.</th>
            <th style={{ width: 180 }}>Progreso</th>
            <th style={{ width: 180 }}>Estado</th>
            <th style={{ width: 70, textAlign: "right" }}></th>
          </tr>
        </thead>
        <tbody>
          {MODULES.map((m) => {
            const eps = EPISODES.filter(e => e.mod === m.id);
            return (
              <tr key={m.id} className="clickable" onClick={() => onNav("modulo", m.id)} style={{ height: rowH }}>
                <td>
                  <span className="mono" style={{ color: "var(--y)", fontSize: 13, fontWeight: 500 }}>{m.id}</span>
                </td>
                <td>
                  <div className="display" style={{ fontSize: 14, fontWeight: 500, letterSpacing: "0.04em" }}>{m.name}</div>
                  <div className="dim mono" style={{ fontSize: 10, marginTop: 2 }}>{m.short}</div>
                </td>
                <td>
                  <div className="row gap-3">
                    <span className="badge">M</span>
                    {eps.filter(e => e.kind === "T").length > 0 && (
                      <span className="badge">T×{eps.filter(e => e.kind === "T").length}</span>
                    )}
                  </div>
                </td>
                <td>
                  <div className="row gap-4">
                    <div style={{ flex: 1 }}><Bar pct={m.pct} status={m.status}/></div>
                    <span className="mono tabular" style={{ fontSize: 11, minWidth: 32, textAlign: "right" }}>{m.pct}%</span>
                  </div>
                </td>
                <td>
                  <div className="row gap-3">
                    <StatusDot status={m.status === "empty" ? "empty" : m.status}/>
                    <span className="display" style={{ fontSize: 11, letterSpacing: "0.12em" }}>
                      {m.status === "ok"    ? "Completo" :
                       m.status === "warn"  ? "En curso" :
                       m.status === "alert" ? "Bloqueado" : "Pendiente"}
                    </span>
                  </div>
                </td>
                <td style={{ textAlign: "right" }}>
                  <Icon name="arrow" size={12}/>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </Panel>
  );
}

// ── Master · Matriz (módulo × tipo de contenido) ─────────
function MasterMatrixView({ onNav }) {
  return (
    <Panel noPad>
      <div style={{ overflowX: "auto" }}>
        <table className="tbl">
          <thead>
            <tr>
              <th style={{ width: 60 }}>ID</th>
              <th>Módulo</th>
              <th style={{ width: 50 }}>Eps</th>
              {KINDS.map((k) => (
                <th key={k} style={{ width: 72, textAlign: "center", padding: "8px 6px" }}>
                  <div style={{ fontSize: 10 }}>{k.toUpperCase()}</div>
                  <div className="mono" style={{
                    fontSize: 9, fontWeight: 400, color: "var(--y)",
                    letterSpacing: 0, textTransform: "none", marginTop: 2,
                  }}>
                    {SOURCES[k].folder}
                  </div>
                </th>
              ))}
              <th style={{ width: 90 }}>%</th>
            </tr>
          </thead>
          <tbody>
            {MODULES.map((m) => {
              const eps = EPISODES.filter(e => e.mod === m.id);
              // Aggregate worst status per kind across episodes
              const agg = (k) => {
                const s = eps.map(e => e.state[k]);
                if (s.includes("alert")) return "alert";
                if (s.includes("run"))   return "run";
                if (s.includes("warn"))  return "warn";
                if (s.every(x => x === "ok")) return "ok";
                if (s.every(x => x === "empty")) return "empty";
                return "warn";
              };
              return (
                <tr key={m.id} className="clickable" onClick={() => onNav("modulo", m.id)}>
                  <td><span className="mono" style={{ color: "var(--y)" }}>{m.id}</span></td>
                  <td className="display" style={{ fontSize: 13 }}>{m.name}</td>
                  <td className="mono dim">{eps.length}</td>
                  {KINDS.map((k) => (
                    <td key={k} style={{ textAlign: "center" }}>
                      <div style={{ display: "inline-block" }}>
                        <KindCell status={agg(k)}/>
                      </div>
                    </td>
                  ))}
                  <td>
                    <div className="row gap-3">
                      <div style={{ flex: 1, minWidth: 40 }}><Bar pct={m.pct} status={m.status}/></div>
                      <span className="mono tabular" style={{ fontSize: 10 }}>{m.pct}</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="row gap-8 mono" style={{ fontSize: 10, color: "var(--text-mute)", padding: "10px 16px", borderTop: "1px solid var(--border)", letterSpacing: "0.08em" }}>
        <span><StatusDot status="ok" sm/> &nbsp;OK</span>
        <span><StatusDot status="warn" sm/> &nbsp;PARCIAL</span>
        <span><StatusDot status="alert" sm/> &nbsp;ERROR</span>
        <span><StatusDot status="run" sm/> &nbsp;CORRIENDO</span>
        <span><StatusDot status="empty" sm/> &nbsp;VACÍO</span>
      </div>
    </Panel>
  );
}

// ── Master · Gantt (cronológico, ritmo de producción) ────
function MasterGanttView({ onNav }) {
  return (
    <Panel noPad>
      <div style={{ padding: "14px 20px 18px" }}>
        {/* Header week scale */}
        <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: 16, marginBottom: 8 }}>
          <div></div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(20, 1fr)", gap: 0 }}>
            {Array.from({ length: 20 }, (_, i) => (
              <div key={i} className="mono" style={{
                fontSize: 9, color: "var(--text-mute)", textAlign: "left",
                borderLeft: i % 4 === 0 ? "1px solid var(--border-2)" : "1px solid var(--border)",
                paddingLeft: 4,
                letterSpacing: "0.06em",
              }}>
                {i % 4 === 0 ? `W${i + 1}` : ""}
              </div>
            ))}
          </div>
        </div>

        {MODULES.map((m, idx) => {
          // synthetic timeline
          const start = (idx * 1.2) % 20;
          const len   = m.status === "ok" ? 3 + (idx % 2) : m.status === "warn" ? 4 : 3;
          const color = m.status === "ok" ? "var(--ok)" :
                        m.status === "warn" ? "var(--y)" :
                        m.status === "alert" ? "var(--alert)" : "var(--border-2)";
          return (
            <div key={m.id}
                 onClick={() => onNav("modulo", m.id)}
                 style={{
                   display: "grid",
                   gridTemplateColumns: "120px 1fr",
                   gap: 16,
                   alignItems: "center",
                   padding: "5px 0",
                   borderBottom: "1px solid var(--border)",
                   cursor: "pointer",
                 }}>
              <div className="row gap-3">
                <span className="mono" style={{ color: "var(--y)", width: 30, fontSize: 12 }}>{m.id}</span>
                <span className="display" style={{ fontSize: 11, letterSpacing: "0.06em" }}>{m.name}</span>
              </div>
              <div style={{ position: "relative", height: 22 }}>
                <div style={{ position: "absolute", inset: 0, background: "var(--panel-2)" }}/>
                <div style={{
                  position: "absolute",
                  top: 3, bottom: 3,
                  left: `${(start / 20) * 100}%`,
                  width: `${(len / 20) * 100}%`,
                  background: color,
                  opacity: m.status === "empty" ? 0.3 : 0.9,
                  borderLeft: `2px solid ${color}`,
                  display: "flex",
                  alignItems: "center",
                  padding: "0 6px",
                }}>
                  <span className="mono" style={{ fontSize: 9, color: "#0D0D0D", fontWeight: 600 }}>
                    {m.status !== "empty" && `${m.pct}%`}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

// ════════════════════════════════════════════════════════════
// MÓDULO — detalle de un Mn (default M3)
// ════════════════════════════════════════════════════════════
function PageModulo({ onNav, onOpenAI, modId }) {
  // modId viene de la selección (sidebar/Master); fallback a M3 como demo.
  const mod = MODULES.find(m => m.id === modId)
           || MODULES.find(m => m.id === "M3")
           || MODULES[0];
  const eps = EPISODES.filter(e => e.mod === mod.id);

  return (
    <div className="content">
      <PageHeader
        title={`${mod.id} · ${mod.name}`}
        sub={mod.short}
        actions={
          <React.Fragment>
            <Btn sm kind="ghost" icon={<Icon name="folder" size={11}/>}
                 onClick={() => fetch("/api/reveal", {
                   method: "POST",
                   headers: { "Content-Type": "application/json" },
                   body: JSON.stringify({ path: `Guiones/` }),
                 }).catch(() => {})}>
              Abrir carpeta
            </Btn>
            <Btn sm kind="primary" onClick={() => onOpenAI({ target: `Módulo ${mod.id}`, purpose: "improve" })}
                 icon={<Icon name="spark" size={11}/>}>
              Mejorar con IA
            </Btn>
          </React.Fragment>
        }
      />
      <SourcePills files={srcFor("modulo")}/>

      <div className="kpi-grid mb-12" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
        <Kpi label="Progreso"      value={mod.pct} unit="%"        delta={mod.status === "ok" ? "Listo" : "En curso"} deltaDir={mod.status === "ok" ? "up" : ""}/>
        <Kpi label="Episodios"     value={eps.length} unit=""        delta={`1 M · ${eps.length - 1} T`}/>
        <Kpi label="Gasto módulo"  value="12.4" unit="€"             delta="3 generaciones de guion"/>
        <Kpi label="Última build"  value="hoy" unit="12:38"          delta="claude-sonnet-4.6" />
      </div>

      <div className="grid gap-8" style={{ gridTemplateColumns: "1.5fr 1fr" }}>
        {/* ── Tabla de episodios ── */}
        <Panel
          title={<span><Icon name="episode" size={12}/> &nbsp;Episodios</span>}
          meta={`${eps.length} contenidos`}
          noPad
        >
          <table className="tbl">
            <thead>
              <tr>
                <th style={{ width: 100 }}>Episodio</th>
                <th>Título</th>
                <th style={{ width: 60 }}>Dur.</th>
                {KINDS.map(k => <th key={k} style={{ width: 60, textAlign: "center", padding: "8px 4px" }}>
                  <div style={{ fontSize: 10 }}>{k[0].toUpperCase() + k.slice(1, 3).toLowerCase()}</div>
                  <div className="mono" style={{
                    fontSize: 9, fontWeight: 400, color: "var(--y)",
                    letterSpacing: 0, textTransform: "none", marginTop: 2, opacity: 0.7,
                  }}>
                    {SOURCES[k].folder.replace("/", "")}
                  </div>
                </th>)}
                <th style={{ width: 40, textAlign: "right" }}></th>
              </tr>
            </thead>
            <tbody>
              {eps.map(ep => {
                const hasError = Object.values(ep.state).includes("alert");
                return (
                  <tr key={ep.id} className="clickable" onClick={() => onNav("episodio", ep.id)}>
                    <td>
                      <div className="row gap-3">
                        <span className="badge" style={{
                          background: ep.kind === "M" ? "var(--y-soft)" : "var(--panel-2)",
                          color: ep.kind === "M" ? "var(--y)" : "var(--text-dim)",
                          borderColor: ep.kind === "M" ? "var(--y)" : "var(--border-2)",
                        }}>{ep.kind}</span>
                        <span className="mono" style={{ fontSize: 11 }}>{ep.id}</span>
                        {hasError && <span style={{ color: "var(--alert)" }} title="Errores detectados">●</span>}
                      </div>
                    </td>
                    <td style={{ fontSize: 13 }}>{ep.title.replace(/^Episodio M\d+ — /, "").replace(/^T\d+ — /, "")}</td>
                    <td className="mono dim" style={{ fontSize: 11 }}>{ep.dur}</td>
                    {KINDS.map(k => (
                      <td key={k} style={{ textAlign: "center" }}>
                        <div style={{ display: "inline-block" }}>
                          <KindCell status={ep.state[k]}/>
                        </div>
                      </td>
                    ))}
                    <td style={{ textAlign: "right" }}><Icon name="arrow" size={11}/></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Panel>

        {/* ── Acciones del módulo ── */}
        <div className="col gap-8">
          <GenGuionPanel epId={mod.id}/>

          <Panel title={<span><Icon name="prompt" size={12}/> &nbsp;Acciones</span>}>
            <div className="col gap-3">
              <Btn icon={<Icon name="play" size={11}/>}
                   onClick={() => onNav("lanzador")}>Generar audio pendiente</Btn>
              <Btn icon={<Icon name="check" size={11}/>}
                   onClick={() => onOpenAI && onOpenAI({ target: `Módulo ${mod.id}`, purpose: "improve",
                                                         hint: "validar módulo completo" })}>
                Validar módulo completo
              </Btn>
              <Btn kind="ghost" icon={<Icon name="doc" size={11}/>}
                   onClick={() => window.open("/files/RRSS/feed.xml", "_blank")}>
                Exportar a podcast .rss
              </Btn>
            </div>
          </Panel>

          <Panel title={<span><Icon name="log" size={12}/> &nbsp;Últimos logs</span>} meta="M3">
            <div className="col" style={{ fontSize: 11, fontFamily: "var(--f-mono)" }}>
              <div style={{ padding: "4px 0", borderBottom: "1px solid var(--border)" }}>
                <span className="muted">12:38:02 </span>
                <span style={{ color: "var(--ok)" }}>[OK] </span>
                <span>guion M3 generado · 9842 palabras</span>
              </div>
              <div style={{ padding: "4px 0", borderBottom: "1px solid var(--border)" }}>
                <span className="muted">12:33:14 </span>
                <span style={{ color: "var(--info)" }}>[INFO] </span>
                <span>dual_debate convergido (94%)</span>
              </div>
              <div style={{ padding: "4px 0", borderBottom: "1px solid var(--border)" }}>
                <span className="muted">11:58:40 </span>
                <span style={{ color: "var(--alert)" }}>[ERR] </span>
                <span>eleven 502 en M3_T2 · bloque 4</span>
              </div>
              <div style={{ padding: "4px 0" }}>
                <span className="muted">11:42:08 </span>
                <span style={{ color: "var(--warn)" }}>[WARN] </span>
                <span>vídeo M3 escena drift 1.8s @ 41:22</span>
              </div>
            </div>
          </Panel>

          <Panel title={<span><Icon name="brain" size={12}/> &nbsp;Diagnóstico IA</span>}>
            <div style={{ fontSize: 13, color: "var(--text-dim)", lineHeight: 1.55 }}>
              El módulo está al <b style={{ color: "var(--y)" }}>72%</b>. Bloqueado por
              M3_T2 (audio fallido) y vídeo M3 (drift de escena).
              Coste estimado para cerrar: <b style={{ color: "var(--text)" }}>~0.18€</b>.
            </div>
            <div className="mt-8">
              <Btn sm kind="primary" onClick={() => onOpenAI({ target: `Módulo ${mod.id}`, purpose: "improve" })}>
                <Icon name="spark" size={10}/> Sugerir plan
              </Btn>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { PageInicio, PageMaster, PageModulo });


// ============================ pages-2.jsx ============================

// pages-2.jsx — Episodio + Pizarra

// ════════════════════════════════════════════════════════════
// PIZARRA — generador de episodios real (audio + video pipelines)
// ════════════════════════════════════════════════════════════

const REPO_URL = "https://github.com/bakero/maquinaria-pesada";
const REPO_BRANCH = "master";

// ── Real pipeline of maquinaria-pesada ──
// Layout: x ∈ [40, 1500], y ∈ [40, 700]
// Audio pipeline (top, y=80-260) — Video pipeline (y=420-700)
const INITIAL_NODES = [
  // ─── INPUTS (left column) ───────────────────────────────
  { id: "pdf",       label: "PDFs/resumenes/RESUMEN_Mn.pdf", kind: "input", x:  40, y:  80, code: "PDFs/resumenes/RESUMEN_Mn.pdf", repo: "PDFs/", description: "PDF resumen temático del módulo — fuente humana de partida." },
  { id: "docs",      label: "Docs vivos del repo",          kind: "input", x:  40, y: 200, code: "BIBLIA_SISTEMA.md · PODCAST.md · VIDEOPODCAST.md · PRIMERPODCAST.md", repo: "BIBLIA_SISTEMA.md", description: "4 documentos vivos que aportan APLICACIÓN_PRÁCTICA al guion." },
  { id: "spec_md",   label: "PODCAST_M_SPEC.md",            kind: "input", x:  40, y: 320, code: "PODCAST_M_SPEC.md", repo: "PODCAST_M_SPEC.md", description: "Spec normativa: estructura de bloques, balance Iago/María, frases obligatorias." },

  // ─── SPEC ENGINE (central rules) ────────────────────────
  { id: "spec_py",   label: "podcast_spec.py",              kind: "art",   x: 240, y: 200, code: "podcast_spec.py", repo: "podcast_spec.py", description: "Reglas Python derivadas del spec MD. Valida guiones y parsea bloques." },

  // ─── AUDIO PIPELINE (top swim lane) ─────────────────────
  { id: "gen_guion", label: "generar_guion.py",             kind: "ai",    x: 440, y:  80, code: "generar_guion.py", repo: "generar_guion.py", model: "claude-sonnet-4.5", description: "Genera el guion M desde PDF + docs vivos + spec." },
  { id: "guion",     label: "Guiones/Mn.txt",               kind: "art",   x: 640, y:  80, code: "Guiones/Mn_<Nombre>.txt", repo: "Guiones/", description: "Guion final con diálogo Iago/María estructurado." },
  { id: "gen_ep",    label: "generar_episodio_v2.py",       kind: "ai",    x: 840, y:  80, code: "generar_episodio_v2.py", repo: "generar_episodio_v2.py", model: "elevenlabs · eleven_v3", description: "Sintetiza audio dual con 2 voces validadas. Mezcla con sintonía y bed." },
  { id: "mp3",       label: "episodios/Mn.mp3",             kind: "art",   x:1040, y:  80, code: "episodios/Mn.mp3", repo: "episodios/", description: "Audio final del episodio. Salida de la rama audio, entrada de la rama vídeo." },
  { id: "validar",   label: "validar_episodio.py",          kind: "ai",    x:1240, y:  80, code: "validar_episodio.py", repo: "validar_episodio.py", model: "claude-haiku-4.5", description: "QA del audio: detecta gaps, comprueba duración y loudness." },

  // ─── DIVIDER (visual only, no node) ────────────────────

  // ─── VIDEO PIPELINE (bottom swim lane) ──────────────────
  // Column V1 — extracción audio
  { id: "transcr",   label: "transcriber.py",               kind: "ai",    x:  40, y: 460, code: "maquinaria_pesada_pipeline/pipeline/transcriber.py", repo: "maquinaria_pesada_pipeline/pipeline/transcriber.py", model: "whisper-large-v3 (local)", description: "Transcripción word-level del audio para subtítulos y alineación." },
  { id: "audio_an",  label: "audio_analyzer.py",            kind: "ai",    x:  40, y: 580, code: "maquinaria_pesada_pipeline/pipeline/audio_analyzer.py", repo: "maquinaria_pesada_pipeline/pipeline/audio_analyzer.py", model: "silencedetect", description: "Detecta silencios y segmentos de habla con FFmpeg." },
  { id: "sintonia",  label: "sintonia_detector.py",         kind: "ai",    x:  40, y: 700, code: "maquinaria_pesada_pipeline/pipeline/sintonia_detector.py", repo: "maquinaria_pesada_pipeline/pipeline/sintonia_detector.py", model: "scipy.correlate", description: "Cross-correlation para encontrar la sintonía con precisión exacta." },

  // Column V2 — extracción contenido
  { id: "content",   label: "content_extractor.py",         kind: "ai",    x: 240, y: 460, code: "maquinaria_pesada_pipeline/pipeline/content_extractor.py", repo: "maquinaria_pesada_pipeline/pipeline/content_extractor.py", description: "Parser de guion + PDF → estructura canónica." },
  { id: "concept",   label: "concept_extractor.py",         kind: "ai",    x: 240, y: 580, code: "maquinaria_pesada_pipeline/pipeline/concept_extractor.py", repo: "maquinaria_pesada_pipeline/pipeline/concept_extractor.py", model: "claude-haiku-4.5", description: "Extrae 1614 conceptos clave del PDF para indexación visual." },

  // Column V3 — media
  { id: "media",     label: "media_finder.py",              kind: "ai",    x: 440, y: 460, code: "maquinaria_pesada_pipeline/pipeline/media_finder.py", repo: "maquinaria_pesada_pipeline/pipeline/media_finder.py", description: "Busca imágenes/gifs en Wikipedia/Wikimedia/Tenor para cada concepto." },
  { id: "gen_esc",   label: "escaleta_generator.py",        kind: "ai",    x: 440, y: 580, code: "maquinaria_pesada_pipeline/pipeline/escaleta_generator.py", repo: "maquinaria_pesada_pipeline/pipeline/escaleta_generator.py", model: "claude-sonnet-4.5", description: "Genera escaleta markdown con timing y assets por bloque." },

  // Column V4 — escaleta artefactos
  { id: "escaleta",  label: "escaletas/Mn.md",              kind: "art",   x: 640, y: 460, code: "escaletas/Mn.md", repo: "escaletas/", description: "Escaleta canónica: 7-8 bloques con tiempos y media references." },
  { id: "parse_esc", label: "escaleta_parser.py",           kind: "ai",    x: 640, y: 580, code: "maquinaria_pesada_pipeline/pipeline/escaleta_parser.py", repo: "maquinaria_pesada_pipeline/pipeline/escaleta_parser.py", description: "Parsea escaleta MD → estructura tipada." },

  // Column V5 — pipeline assembly
  { id: "esc_pipe",  label: "escaleta_to_pipeline.py",      kind: "ai",    x: 840, y: 500, code: "maquinaria_pesada_pipeline/pipeline/escaleta_to_pipeline.py", repo: "maquinaria_pesada_pipeline/pipeline/escaleta_to_pipeline.py", description: "Construye scene_track + scene_timeline (cronograma de escenas)." },

  // Column V6 — rendering
  { id: "kling",     label: "kling_generator.py",           kind: "ai",    x:1040, y: 460, code: "maquinaria_pesada_pipeline/pipeline/kling_generator.py", repo: "maquinaria_pesada_pipeline/pipeline/kling_generator.py", model: "kling-1.6-pro (kuaishou)", description: "Image-to-video con JWT auth. Catálogo de clips estudio (~$24/episodio)." },
  { id: "overlay",   label: "overlay_renderer.py",          kind: "ai",    x:1040, y: 580, code: "maquinaria_pesada_pipeline/pipeline/overlay_renderer.py", repo: "maquinaria_pesada_pipeline/pipeline/overlay_renderer.py", description: "Renderiza overlays con PIL → frames PNG por escena." },
  { id: "subs",      label: "subtitle_generator.py",        kind: "ai",    x:1040, y: 700, code: "maquinaria_pesada_pipeline/pipeline/subtitle_generator.py", repo: "maquinaria_pesada_pipeline/pipeline/subtitle_generator.py", description: "Genera .srt blanco desde Whisper word-level." },

  // Column V7 — final composition
  { id: "compose",   label: "video_compositor.py",          kind: "ai",    x:1240, y: 580, code: "maquinaria_pesada_pipeline/pipeline/video_compositor.py", repo: "maquinaria_pesada_pipeline/pipeline/video_compositor.py", model: "ffmpeg layout-C (PIP)", description: "Compone Kling + overlays + subs + audio con ffmpeg." },

  // Final output
  { id: "mp4",       label: "videopodcast/Mn.mp4",          kind: "out",   x:1440, y: 580, code: "videopodcast/Mn.mp4", repo: "videopodcast/", description: "MP4 1080p final, listo para YouTube." },
];

const INITIAL_EDGES = [
  // Audio
  ["pdf",       "gen_guion"],
  ["docs",      "gen_guion"],
  ["spec_md",   "spec_py"],
  ["spec_py",   "gen_guion"],
  ["gen_guion", "guion"],
  ["guion",     "gen_ep"],
  ["spec_py",   "gen_ep"],
  ["gen_ep",    "mp3"],
  ["mp3",       "validar"],

  // Audio → Video bridges
  ["mp3",       "transcr"],
  ["mp3",       "audio_an"],
  ["mp3",       "sintonia"],
  ["guion",     "content"],
  ["pdf",       "concept"],

  // Video pipeline
  ["transcr",   "content"],
  ["content",   "gen_esc"],
  ["audio_an",  "gen_esc"],
  ["concept",   "media"],
  ["media",     "gen_esc"],
  ["gen_esc",   "escaleta"],
  ["escaleta",  "parse_esc"],
  ["parse_esc", "esc_pipe"],
  ["esc_pipe",  "kling"],
  ["esc_pipe",  "overlay"],
  ["transcr",   "subs"],
  ["sintonia",  "compose"],
  ["kling",     "compose"],
  ["overlay",   "compose"],
  ["subs",      "compose"],
  ["mp3",       "compose"],
  ["compose",   "mp4"],
];

// Component kinds & their canonical folders
const PZ_KINDS = [
  { id: "input",  label: "Fuente",       icon: "doc",     folder: "PDFs/",         ext: ".pdf",  hint: "Material de partida" },
  { id: "ai",     label: "Componente IA",icon: "spark",   folder: "(script .py)",  ext: ".py",   hint: "Llamada a modelo" },
  { id: "art",    label: "Artefacto",    icon: "doc",     folder: "auto",          ext: "",      hint: "Guiones/, escaletas/, logs/…" },
  { id: "out",    label: "Salida",       icon: "play",    folder: "episodios/",    ext: ".mp3",  hint: "Audio o vídeo final" },
];

// Compute anchor point on the border of a node along direction to (tx, ty)
function nodeAnchor(node, tx, ty) {
  const NODE_W = 132;
  const NODE_H = 76;
  const cx = node.x + NODE_W / 2;
  const cy = node.y + NODE_H / 2;
  const dx = tx - cx;
  const dy = ty - cy;

  if (node.kind === "ai") {
    // Circular node (110px diameter centered in 132-wide box → offset by 11)
    const r = 55;
    const len = Math.sqrt(dx * dx + dy * dy) || 1;
    return [cx + (dx / len) * r, cy + (dy / len) * r];
  }
  // Rectangle anchor: intersect with bbox border
  const hw = NODE_W / 2 - 4;
  const hh = NODE_H / 2 - 4;
  const ax = Math.abs(dx);
  const ay = Math.abs(dy);
  if (ax * hh > ay * hw) {
    // Hits left/right
    const k = hw / (ax || 1);
    return [cx + (dx > 0 ? hw : -hw), cy + dy * k];
  }
  const k = hh / (ay || 1);
  return [cx + dx * k, cy + (dy > 0 ? hh : -hh)];
}

function PagePizarra({ onNav, onOpenAI }) {
  const [nodes, setNodes] = React.useState(INITIAL_NODES);
  const [edges, setEdges] = React.useState(INITIAL_EDGES);
  const [selected, setSelected] = React.useState("gen_guion");
  const [dragging, setDragging] = React.useState(null);
  const [adding, setAdding] = React.useState(false);
  const canvasRef = React.useRef(null);

  const CW = 1640, CH = 800;

  // Drag handlers
  const onNodeMouseDown = (e, nodeId) => {
    if (e.button !== 0) return;
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const scaleX = CW / rect.width;
    const scaleY = CH / rect.height;
    setDragging({
      id: nodeId,
      offX: e.clientX * scaleX - node.x,
      offY: e.clientY * scaleY - node.y,
      scaleX, scaleY,
    });
    setSelected(nodeId);
    e.preventDefault();
    e.stopPropagation();
  };

  const onCanvasMouseMove = (e) => {
    if (!dragging) return;
    const x = e.clientX * dragging.scaleX - dragging.offX;
    const y = e.clientY * dragging.scaleY - dragging.offY;
    const cx = Math.max(10, Math.min(CW - 142, x));
    const cy = Math.max(10, Math.min(CH - 86,  y));
    setNodes((ns) => ns.map(n => n.id === dragging.id ? { ...n, x: cx, y: cy } : n));
  };

  const onCanvasMouseUp = () => setDragging(null);

  React.useEffect(() => {
    if (!dragging) return;
    const up = () => setDragging(null);
    window.addEventListener("mouseup", up);
    return () => window.removeEventListener("mouseup", up);
  }, [dragging]);

  const selNode = nodes.find(n => n.id === selected);

  const addNode = (newNode) => {
    setNodes((ns) => [...ns, newNode]);
    setSelected(newNode.id);
    setAdding(false);
  };

  const deleteSelected = () => {
    if (!selected) return;
    setNodes((ns) => ns.filter(n => n.id !== selected));
    setEdges((es) => es.filter(([a, b]) => a !== selected && b !== selected));
    setSelected(null);
  };

  const resetLayout = () => {
    setNodes(INITIAL_NODES);
    setEdges(INITIAL_EDGES);
  };

  const nAI = nodes.filter(n => n.kind === "ai").length;
  const nIn = nodes.filter(n => n.kind === "input").length;
  const nArt= nodes.filter(n => n.kind === "art").length;
  const nOut= nodes.filter(n => n.kind === "out").length;

  return (
    <div className="content">
      <PageHeader
        title="Pizarra · Generador de episodios"
        sub={`bakero/maquinaria-pesada @ master · ${nodes.length} componentes · ${edges.length} conexiones`}
        actions={
          <React.Fragment>
            <Btn sm kind="ghost" icon={<Icon name="folder" size={11}/>}
                 onClick={() => window.open(REPO_URL, "_blank")}>Repositorio</Btn>
            <Btn sm kind="ghost" icon={<Icon name="refresh" size={11}/>} onClick={resetLayout}>
              Resetear layout
            </Btn>
            <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Pipeline canónico", purpose: "improve" })}
                 icon={<Icon name="spark" size={11}/>}>Mejorar con IA</Btn>
          </React.Fragment>
        }
      />
      <SourcePills files={srcFor("pizarra")}/>

      <div className="grid gap-8" style={{ gridTemplateColumns: "1fr 400px" }}>
        {/* Canvas */}
        <Panel
          title={<span><Icon name="pipe" size={12}/> &nbsp;Pipeline real · audio + vídeo</span>}
          meta={`${nIn} fuentes · ${nAI} IA · ${nArt} artefactos · ${nOut} salidas`}
          noPad
        >
          <div style={{ overflow: "auto", maxHeight: 640 }}>
            <div
              ref={canvasRef}
              className={`pz-canvas ${dragging ? "dragging" : ""}`}
              style={{ width: CW, height: CH, minWidth: CW }}
              onMouseMove={onCanvasMouseMove}
              onMouseUp={onCanvasMouseUp}
              onClick={(e) => { if (e.target === e.currentTarget) setSelected(null); }}
            >
              {/* Lane labels */}
              <div style={{
                position: "absolute", top: 14, left: 200,
                fontFamily: "var(--f-display)", fontSize: 11, color: "var(--y)",
                letterSpacing: "0.2em", opacity: 0.6,
              }}>RAMA AUDIO · raíz del repo</div>
              <div style={{
                position: "absolute", top: 380, left: 200,
                fontFamily: "var(--f-display)", fontSize: 11, color: "var(--y)",
                letterSpacing: "0.2em", opacity: 0.6,
              }}>RAMA VÍDEO · maquinaria_pesada_pipeline/</div>

              {/* Lane separator */}
              <div style={{
                position: "absolute", left: 0, right: 0, top: 360,
                height: 8, background: "repeating-linear-gradient(-45deg, rgba(245,196,0,0.4) 0 8px, transparent 8px 16px)",
              }}/>

              {/* Toolbar */}
              <div className="pz-toolbar">
                <button className="btn primary sm" onClick={() => setAdding(!adding)}>
                  <Icon name="arrow" size={10}/> Añadir componente
                </button>
                {selected && (
                  <button className="btn danger sm" onClick={deleteSelected}>
                    <Icon name="close" size={10}/> Quitar
                  </button>
                )}
              </div>

              {/* Add modal */}
              {adding && <AddComponentForm onAdd={addNode} onCancel={() => setAdding(false)} canvasW={CW} canvasH={CH}/>}

              {/* SVG overlay with edges */}
              <svg
                className="pz-svg-overlay"
                viewBox={`0 0 ${CW} ${CH}`}
                preserveAspectRatio="none"
                style={{ width: CW, height: CH }}
              >
                <defs>
                  <marker id="arr2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto">
                    <path d="M0 0 L10 5 L0 10 z" fill="var(--y)"/>
                  </marker>
                  <marker id="arr2-sel" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto">
                    <path d="M0 0 L10 5 L0 10 z" fill="#FFD93D"/>
                  </marker>
                </defs>
                {edges.map(([a, b], i) => {
                  const na = nodes.find(n => n.id === a);
                  const nb = nodes.find(n => n.id === b);
                  if (!na || !nb) return null;
                  const nbCx = nb.x + 66;
                  const nbCy = nb.y + 38;
                  const naCx = na.x + 66;
                  const naCy = na.y + 38;
                  const [x1, y1] = nodeAnchor(na, nbCx, nbCy);
                  const [x2, y2] = nodeAnchor(nb, naCx, naCy);
                  const isSel = selected && (a === selected || b === selected);
                  return (
                    <line
                      key={i}
                      x1={x1} y1={y1} x2={x2} y2={y2}
                      stroke={isSel ? "#FFD93D" : "var(--y)"}
                      strokeOpacity={isSel ? 0.95 : 0.5}
                      strokeWidth={isSel ? 2 : 1.4}
                      markerEnd={`url(#${isSel ? "arr2-sel" : "arr2"})`}
                    />
                  );
                })}
              </svg>

              {/* Nodes */}
              {nodes.map((n) => (
                <div
                  key={n.id}
                  className={`pz-node kind-${n.kind} ${selected === n.id ? "selected" : ""} ${dragging?.id === n.id ? "dragging" : ""}`}
                  style={{ left: n.x, top: n.y }}
                  onMouseDown={(e) => onNodeMouseDown(e, n.id)}
                  onClick={(e) => { e.stopPropagation(); setSelected(n.id); }}
                >
                  <div className="pz-node-body">
                    <div className="pz-node-kind">
                      {n.kind === "ai" ? "IA" : n.kind === "input" ? "FUENTE" : n.kind === "art" ? "ARTEFACTO" : "SALIDA"}
                      {n.generated && <span style={{ color: "var(--ok)", marginLeft: 6 }}>· ✨</span>}
                    </div>
                    <div className="pz-node-label">
                      {(n.label.length > 28 ? n.label.slice(0, 26) + "…" : n.label)}
                    </div>
                    {n.model && (
                      <div className="pz-node-path" style={{ color: "var(--info)", marginTop: 2 }}>
                        {n.model}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Legend */}
              <div className="pz-legend">
                <div className="row"><span style={{ display: "inline-block", width: 12, height: 12, borderRadius: "50%", background: "var(--y-soft)", border: "1px solid var(--y)" }}/> COMPONENTE IA</div>
                <div className="row"><span style={{ display: "inline-block", width: 12, height: 12, background: "var(--panel-2)", borderLeft: "3px solid var(--info)" }}/> FUENTE</div>
                <div className="row"><span style={{ display: "inline-block", width: 12, height: 12, background: "var(--panel-2)", borderLeft: "3px solid var(--text-dim)" }}/> ARTEFACTO</div>
                <div className="row"><span style={{ display: "inline-block", width: 12, height: 12, background: "var(--panel-2)", borderLeft: "3px solid var(--ok)" }}/> SALIDA</div>
                <div className="row" style={{ marginTop: 4, color: "var(--text-mute)" }}>↻ arrastra cualquier nodo</div>
                <div className="row" style={{ color: "var(--text-mute)" }}>✨ generado por Claude</div>
              </div>
            </div>
          </div>
        </Panel>

        {/* Inspector */}
        <Panel title={<span><Icon name="doc" size={12}/> &nbsp;Inspector</span>}>
          {selNode ? (
            <NodeInspector node={selNode} onNav={onNav} onOpenAI={onOpenAI}/>
          ) : (
            <div className="mono dim" style={{ fontSize: 12, textAlign: "center", padding: "32px 0" }}>
              Selecciona un componente
            </div>
          )}
        </Panel>
      </div>

      {/* Pipeline metrics */}
      <div className="kpi-grid mt-12">
        <Kpi label="Componentes IA"   value={nAI} delta={`${nodes.filter(n => n.model).length} con modelo declarado`}/>
        <Kpi label="Tiempo medio"      value="6:42" unit="min" delta="por episodio M"/>
        <Kpi label="Coste medio"       value="0.84" unit="€"   delta="audio + ~24€ vídeo Kling"/>
        <Kpi label="Tasa éxito · 30d"  value="96.4" unit="%"   delta="3 fallos · 84 runs"/>
      </div>
    </div>
  );
}

// ── Node inspector with GitHub link, description, code ───
function NodeInspector({ node, onNav, onOpenAI }) {
  const ghUrl = node.repo ? `${REPO_URL}/blob/${REPO_BRANCH}/${node.repo}` : REPO_URL;
  const ghTreeUrl = node.repo && node.repo.endsWith("/") ? `${REPO_URL}/tree/${REPO_BRANCH}/${node.repo}` : ghUrl;

  return (
    <React.Fragment>
      <div className="display" style={{ fontSize: 15, color: "var(--y)", marginBottom: 4 }}>
        {node.label}
      </div>
      <div className="mono dim" style={{ fontSize: 11, marginBottom: 12 }}>
        {node.kind === "ai"    ? "Componente · IA" :
         node.kind === "input" ? "Fuente · Input" :
         node.kind === "art"   ? "Artefacto" : "Salida"}
        {node.generated && <span style={{ color: "var(--ok)" }}> · ✨ Claude-generated</span>}
      </div>

      {node.description && (
        <div style={{
          fontSize: 13,
          color: "var(--text-dim)",
          lineHeight: 1.55,
          background: "var(--panel-2)",
          borderLeft: "2px solid var(--y)",
          padding: "8px 12px",
          marginBottom: 12,
        }}>
          {node.description}
        </div>
      )}

      <div className="col gap-3" style={{ marginBottom: 12 }}>
        <div>
          <div className="muted mono" style={{ fontSize: 10, letterSpacing: "0.08em", marginBottom: 2 }}>ARCHIVO</div>
          <div className="mono" style={{ fontSize: 11, color: "var(--y)", wordBreak: "break-all" }}>{node.code}</div>
        </div>

        {node.model && (
          <div>
            <div className="muted mono" style={{ fontSize: 10, letterSpacing: "0.08em", marginBottom: 2 }}>MODELO</div>
            <div className="mono" style={{ fontSize: 11, color: "var(--info)" }}>{node.model}</div>
          </div>
        )}

        <div className="row gap-3 mt-4">
          <a href={ghUrl} target="_blank" rel="noopener" className="btn sm" style={{ textDecoration: "none" }}>
            <Icon name="folder" size={11}/> Abrir en GitHub
          </a>
          {node.repo && node.repo.endsWith("/") && (
            <a href={ghTreeUrl} target="_blank" rel="noopener" className="btn sm ghost" style={{ textDecoration: "none" }}>
              Carpeta ↗
            </a>
          )}
        </div>
      </div>

      <div className="h3 mt-12">Código</div>
      <pre className="code" style={{ fontSize: 11, maxHeight: 240, overflow: "auto" }}>
{node.generated && node.generatedCode
  ? node.generatedCode
  : node.kind === "ai"
  ? `# ${node.code}
"""${node.description || ""}"""

from anthropic import Anthropic
from pathlib import Path

client = Anthropic()
MODEL  = "${node.model || "claude-sonnet-4-5"}"

def run(input_path: Path) -> Path:
    ${node.id === "transcr" ? `import whisper
    model = whisper.load_model("large-v3")
    result = model.transcribe(str(input_path), word_timestamps=True)
    return write_srt(result)` : `text = input_path.read_text(encoding="utf-8")
    response = client.messages.create(
        model=MODEL,
        max_tokens=16_000,
        messages=[{"role": "user", "content": build_prompt(text)}],
    )
    out = output_path_for(input_path)
    out.write_text(response.content[0].text, encoding="utf-8")
    return out`}`
  : node.kind === "art"
  ? `# ${node.code}
# Artefacto en disco — filesystem source-of-truth.
# Generado por la fase anterior, consumido por la siguiente.`
  : node.kind === "input"
  ? `# ${node.code}
# Material de partida humano.
# Versionado fuera del pipeline.`
  : `# ${node.code}
# Salida final del pipeline.`}
      </pre>

      <div className="row gap-3 mt-12">
        <Btn sm icon={<Icon name="prompt" size={11}/>}
             onClick={() => onOpenAI && onOpenAI({ target: `Nodo · ${node.code}`, purpose: "improve",
                                                   hint: "editar lógica del nodo" })}>
          Editar
        </Btn>
        <Btn sm kind="ghost" icon={<Icon name="play" size={11}/>}
             onClick={() => onNav && onNav("lanzador")}>
          Re-ejecutar
        </Btn>
      </div>
    </React.Fragment>
  );
}

// ── Add component form: describe → Claude generates code ──
function AddComponentForm({ onAdd, onCancel }) {
  const [kind, setKind] = React.useState("ai");
  const [name, setName] = React.useState("");
  const [desc, setDesc] = React.useState("");
  const [folder, setFolder] = React.useState("maquinaria_pesada_pipeline/pipeline/");
  const [stage, setStage] = React.useState("form"); // form | generating | done
  const [code, setCode] = React.useState("");
  const [streamed, setStreamed] = React.useState("");

  React.useEffect(() => {
    if (kind === "input")  setFolder("PDFs/");
    if (kind === "ai")     setFolder("maquinaria_pesada_pipeline/pipeline/");
    if (kind === "art")    setFolder("Guiones/");
    if (kind === "out")    setFolder("episodios/");
  }, [kind]);

  const folderOptions = kind === "ai"
    ? ["maquinaria_pesada_pipeline/pipeline/", "(raíz del repo)"]
    : kind === "art"
    ? ["Guiones/", "escaletas/", "logs/"]
    : kind === "out"
    ? ["episodios/", "videopodcast/"]
    : ["PDFs/", "PDFs/resumenes/"];

  const submit = (e) => {
    e.preventDefault();
    if (!name.trim() || !desc.trim()) return;
    if (kind === "ai") {
      // Simulate Claude generating code
      setStage("generating");
      const generated = generateMockCode(name, desc);
      let i = 0;
      const tick = () => {
        i += Math.floor(Math.random() * 8) + 4;
        setStreamed(generated.slice(0, i));
        if (i < generated.length) setTimeout(tick, 16);
        else {
          setCode(generated);
          setStage("done");
        }
      };
      setTimeout(tick, 300);
    } else {
      finish("");
    }
  };

  const finish = (generatedCode) => {
    const safe = name.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/_+$/, "").slice(0, 30) || `node_${Date.now()}`;
    const ext = kind === "ai" ? ".py" : kind === "input" ? ".pdf" : kind === "out" ? ".mp3" : ".md";
    const folderFinal = folder === "(raíz del repo)" ? "" : folder;
    const node = {
      id: safe,
      label: kind === "ai" ? safe + ".py" : folderFinal + safe + ext,
      kind,
      x: 700, y: 380,
      code: folderFinal + safe + ext,
      repo: folderFinal + safe + ext,
      description: desc,
      generated: true,
      generatedCode: generatedCode || undefined,
      model: kind === "ai" ? "claude-sonnet-4.5 (interpretado)" : undefined,
    };
    onAdd(node);
  };

  return (
    <form
      className="pz-add-modal"
      onSubmit={submit}
      onMouseDown={(e) => e.stopPropagation()}
      onClick={(e) => e.stopPropagation()}
      style={{ width: stage === "form" ? 380 : 540 }}
    >
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
        <div className="display" style={{ fontSize: 11, color: "var(--y)", letterSpacing: "0.16em" }}>
          {stage === "form"       && "NUEVO COMPONENTE"}
          {stage === "generating" && "✨ CLAUDE INTERPRETANDO…"}
          {stage === "done"       && "✓ CÓDIGO GENERADO"}
        </div>
        <button type="button" className="btn ghost sm" onClick={onCancel} style={{ padding: "2px 6px" }}>
          <Icon name="close" size={10}/>
        </button>
      </div>

      {stage === "form" && (
        <div className="col gap-6">
          {/* Kind */}
          <div>
            <div className="h3 mb-4" style={{ fontSize: 10 }}>Tipo</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4 }}>
              {PZ_KINDS.map((k) => (
                <button
                  type="button" key={k.id} onClick={() => setKind(k.id)}
                  className="btn sm"
                  style={{
                    background: kind === k.id ? "var(--y)" : "transparent",
                    color: kind === k.id ? "#0D0D0D" : "var(--text)",
                    borderColor: kind === k.id ? "var(--y)" : "var(--border-2)",
                    fontWeight: kind === k.id ? 600 : 500,
                    justifyContent: "flex-start",
                  }}>
                  <Icon name={k.icon} size={10}/> {k.label}
                </button>
              ))}
            </div>
          </div>

          {/* Name */}
          <div>
            <div className="h3 mb-4" style={{ fontSize: 10 }}>Nombre del archivo</div>
            <input
              autoFocus
              className="ai-input"
              placeholder={kind === "ai" ? "resumir_pdf_corto" : "nuevo_artefacto"}
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={{ width: "100%" }}
            />
          </div>

          {/* Description — only for AI; key for Claude to generate code */}
          {kind === "ai" && (
            <div>
              <div className="row" style={{ justifyContent: "space-between", marginBottom: 4 }}>
                <div className="h3" style={{ fontSize: 10, margin: 0 }}>¿Qué debe hacer este componente?</div>
                <span className="mono" style={{ fontSize: 9, color: "var(--y)" }}>✨ Claude generará el código</span>
              </div>
              <textarea
                className="ai-input"
                placeholder="p.ej. 'Toma un PDF, extrae las 5 ideas principales con Claude Haiku y las escribe a logs/ideas_<Mn>.json'"
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
                rows={4}
                style={{ width: "100%", resize: "vertical", fontFamily: "var(--f-mono)", fontSize: 11, lineHeight: 1.5 }}
              />
            </div>
          )}

          {kind !== "ai" && (
            <div>
              <div className="h3 mb-4" style={{ fontSize: 10 }}>Descripción</div>
              <textarea
                className="ai-input"
                placeholder="Qué representa este nodo en el pipeline"
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
                rows={3}
                style={{ width: "100%", resize: "vertical", fontFamily: "var(--f-body)", fontSize: 12 }}
              />
            </div>
          )}

          {/* Folder */}
          {folderOptions.length > 1 && (
            <div>
              <div className="h3 mb-4" style={{ fontSize: 10 }}>Carpeta destino</div>
              <div className="row gap-3" style={{ flexWrap: "wrap" }}>
                {folderOptions.map((f) => (
                  <button
                    type="button" key={f} onClick={() => setFolder(f)}
                    className="btn sm"
                    style={{
                      background: folder === f ? "var(--y-soft)" : "transparent",
                      borderColor: folder === f ? "var(--y)" : "var(--border-2)",
                      color: folder === f ? "var(--y)" : "var(--text-dim)",
                      fontFamily: "var(--f-mono)",
                      fontSize: 10, letterSpacing: 0, textTransform: "none",
                    }}>{f}</button>
                ))}
              </div>
            </div>
          )}

          {/* Preview path */}
          <div style={{
            background: "var(--panel-2)",
            border: "1px dashed var(--border-2)",
            padding: "6px 10px",
            fontFamily: "var(--f-mono)",
            fontSize: 11,
          }}>
            <span className="muted">→ se creará: </span>
            <span style={{ color: "var(--y)" }}>
              {kind === "ai"
                ? (folder === "(raíz del repo)" ? "" : folder) + (name || "componente") + ".py"
                : folder + (name || "nuevo") + (kind === "input" ? ".pdf" : kind === "out" ? ".mp3" : ".md")}
            </span>
          </div>

          <div className="row gap-3" style={{ justifyContent: "flex-end" }}>
            <Btn sm kind="ghost" onClick={onCancel}>Cancelar</Btn>
            <button type="submit" className="btn primary sm" disabled={!name.trim() || !desc.trim()}>
              {kind === "ai" ? <React.Fragment><Icon name="spark" size={11}/> Crear con Claude</React.Fragment> : <React.Fragment><Icon name="check" size={11}/> Crear</React.Fragment>}
            </button>
          </div>
        </div>
      )}

      {stage === "generating" && (
        <div>
          <div className="mono dim" style={{ fontSize: 11, marginBottom: 8, color: "var(--info)" }}>
            <Icon name="spark" size={10}/> claude-sonnet-4.5 · streaming…
          </div>
          <pre className="code" style={{ fontSize: 10.5, maxHeight: 320, overflow: "auto" }}>
            {streamed}<span className="ai-cursor"/>
          </pre>
        </div>
      )}

      {stage === "done" && (
        <div>
          <div className="row gap-4" style={{ marginBottom: 10 }}>
            <span className="badge ok">✓ {code.split("\n").length} líneas</span>
            <span className="badge">claude-sonnet-4.5</span>
            <span className="badge">~0.024€</span>
          </div>
          <pre className="code" style={{ fontSize: 10.5, maxHeight: 240, overflow: "auto", marginBottom: 12 }}>
            {code}
          </pre>
          <div className="row gap-3" style={{ justifyContent: "flex-end" }}>
            <Btn sm kind="ghost" onClick={() => setStage("form")}>← Volver</Btn>
            <button type="button" className="btn primary sm" onClick={() => finish(code)}>
              <Icon name="check" size={11}/> Añadir a la pizarra
            </button>
          </div>
        </div>
      )}
    </form>
  );
}

// ── Mock code generator: realistic Python for the prototype ──
function generateMockCode(name, desc) {
  const safe = name.toLowerCase().replace(/[^a-z0-9]+/g, "_") || "componente";
  // try to infer model from description
  const usesHaiku  = /haiku|r[aá]pido|simple|extracci[oó]n/i.test(desc);
  const usesGpt    = /gpt|openai|valid|debate/i.test(desc);
  const usesEleven = /audio|voz|tts|elevenlabs/i.test(desc);
  const usesWhisper= /whisper|transcrib|subtitul/i.test(desc);

  let imports, model, body;
  if (usesEleven) {
    imports = `from elevenlabs.client import ElevenLabs\nfrom pathlib import Path`;
    model = `eleven_v3`;
    body = `eleven = ElevenLabs()
    audio = eleven.text_to_speech.convert(
        text=text_input,
        voice_id="EXAVITQu4vr4xnSDxMaL",
        model_id="eleven_v3",
    )
    out_path.write_bytes(b"".join(audio))`;
  } else if (usesWhisper) {
    imports = `import whisper\nfrom pathlib import Path`;
    model = `whisper-large-v3`;
    body = `model = whisper.load_model("large-v3")
    result = model.transcribe(
        str(audio_path),
        word_timestamps=True,
        language="es",
    )
    return result["segments"]`;
  } else if (usesGpt) {
    imports = `from openai import OpenAI\nfrom pathlib import Path`;
    model = `gpt-4o-mini`;
    body = `client = OpenAI()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content`;
  } else {
    imports = `from anthropic import Anthropic\nfrom pathlib import Path\nimport json`;
    model = usesHaiku ? `claude-haiku-4-5` : `claude-sonnet-4-5`;
    body = `client = Anthropic()
    prompt = build_prompt(input_data)
    response = client.messages.create(
        model=MODEL,
        max_tokens=${usesHaiku ? "4_000" : "16_000"},
        messages=[{"role": "user", "content": prompt}],
    )
    output_text = response.content[0].text
    out_path.write_text(output_text, encoding="utf-8")
    return out_path`;
  }

  return `#!/usr/bin/env python3
"""${safe}.py

${desc.trim()}

Generado por Claude · interpretado desde descripción del usuario.
"""
from __future__ import annotations

${imports}

MODEL = "${model}"


def run(input_path: Path, out_path: Path) -> Path:
    """Punto de entrada del componente."""
    ${body}


def build_prompt(data) -> str:
    return f"""Eres un asistente del pipeline MaquinarIA Pesada.
Tarea: ${desc.trim()}

Input:
{data}
"""


if __name__ == "__main__":
    import sys
    in_p  = Path(sys.argv[1])
    out_p = Path(sys.argv[2]) if len(sys.argv) > 2 else in_p.with_suffix(".out")
    run(in_p, out_p)
    print(f"[ok] {in_p} -> {out_p}")
`;
}
Object.assign(window, { PagePizarra });


// ============================ pages-3.jsx ============================

// pages-3.jsx — Mapa, Conectores, Lanzador, Fuentes, Previsualizar,
//                Logs, Optimizar, Consumo, Ajustes
// ────────────────────────────────────────────────────────────────

// ════════════════════════════════════════════════════════════
// SHARED FIXTURES (local to these pages)
// ════════════════════════════════════════════════════════════
const MAP_NODES = [
  // generators (IA)
  { id: "claude_sonnet",  label: "Claude Sonnet 4.5", kind: "generator", x:  60, y:  40 },
  { id: "claude_haiku",   label: "Claude Haiku 4.5",  kind: "generator", x:  60, y: 160 },
  { id: "gpt4o",          label: "GPT-4o mini",       kind: "generator", x:  60, y: 280 },
  { id: "elevenlabs_gen", label: "ElevenLabs v3",     kind: "generator", x:  60, y: 400 },
  { id: "kling_gen",      label: "Kling 1.6 pro",     kind: "generator", x:  60, y: 520 },

  // systems (pipelines)
  { id: "gen_guion",  label: "generar_guion.py",       kind: "system", x: 320, y:  40 },
  { id: "dual",       label: "dual_debate.py",         kind: "system", x: 320, y: 160 },
  { id: "gen_ep",     label: "generar_episodio_v2.py", kind: "system", x: 320, y: 400 },
  { id: "kling_pipe", label: "kling_generator.py",     kind: "system", x: 320, y: 520 },
  { id: "validar",    label: "validar_episodio.py",    kind: "system", x: 320, y: 280 },

  // outputs (generated)
  { id: "guion_out", label: "Guiones/*.txt",       kind: "generated", x: 600, y:  40 },
  { id: "val_out",   label: "logs/dual_*.json",    kind: "generated", x: 600, y: 160 },
  { id: "checks",    label: "checks/*.json",       kind: "generated", x: 600, y: 280 },
  { id: "mp3_out",   label: "episodios/*.mp3",     kind: "generated", x: 600, y: 400 },
  { id: "mp4_out",   label: "videopodcast/*.mp4",  kind: "generated", x: 600, y: 520 },
];

const MAP_EDGES = [
  ["claude_sonnet",  "gen_guion"],
  ["gen_guion",      "guion_out"],
  ["claude_sonnet",  "dual"],
  ["gpt4o",          "dual"],
  ["dual",           "val_out"],
  ["claude_haiku",   "validar"],
  ["validar",        "checks"],
  ["elevenlabs_gen", "gen_ep"],
  ["gen_ep",         "mp3_out"],
  ["kling_gen",      "kling_pipe"],
  ["kling_pipe",     "mp4_out"],
];

const CONNECTORS = {
  service: [
    { id: "anthropic",  label: "Anthropic",  env: "ANTHROPIC_API_KEY",  status: "ok",    detail: "claude-sonnet-4.5 · claude-haiku-4.5", latency: 142 },
    { id: "openai",     label: "OpenAI",     env: "OPENAI_API_KEY",     status: "ok",    detail: "gpt-4o-mini · debate dual",            latency: 188 },
    { id: "elevenlabs", label: "ElevenLabs", env: "ELEVENLABS_API_KEY", status: "warn",  detail: "saldo 8.40€ · recargar",               latency: 232 },
    { id: "kling",      label: "Kling",      env: "KLING_API_KEY",      status: "ok",    detail: "kling-1.6-pro · JWT auth",             latency: 412 },
    { id: "whisper",    label: "Whisper",    env: "(local)",            status: "ok",    detail: "whisper-large-v3 · cpu",               latency:  18 },
    // ── distribución ──
    { id: "spotify",    label: "Spotify for Podcasters", env: "SPOTIFY_CLIENT_ID + SECRET", status: "ok",   detail: "OAuth · métricas de oyentes y reproducciones", latency: 218, kind: "distribution" },
    { id: "ivoox",      label: "iVoox",                  env: "IVOOX_API_KEY",             status: "ok",   detail: "RSS + scraping autenticado · descargas",       latency: 304, kind: "distribution" },
    { id: "linkedin",   label: "LinkedIn",               env: "LINKEDIN_ACCESS_TOKEN",     status: "warn", detail: "token expira en 11 días · refrescar",         latency: 162, kind: "distribution" },
  ],
  pipeline: [
    { id: "generar_guion",      label: "generar_guion.py",      script: "generar_guion.py",      icon: "prompt", description: "Genera guion M desde PDF + docs vivos." },
    { id: "generar_episodio",   label: "generar_episodio_v2.py",script: "generar_episodio_v2.py",icon: "play",   description: "Sintetiza audio dual con 2 voces." },
    { id: "validar_episodio",   label: "validar_episodio.py",   script: "validar_episodio.py",   icon: "check",  description: "QA del audio: gaps, duración, loudness." },
    { id: "dual_debate",        label: "dual_debate.py",        script: "dual_debate.py",        icon: "spark",  description: "Debate Claude vs GPT sobre el guion." },
    { id: "producir_episodio",  label: "producir_episodio.py",  script: "producir_episodio.py",  icon: "prompt", description: "Pipeline completo: guion → audio → validación." },
    { id: "lanzar_produccion",  label: "lanzar_produccion.py",  script: "lanzar_produccion.py",  icon: "prompt", description: "Cola de producción de varios episodios." },
    { id: "rebalance_blocks",   label: "rebalance_blocks.py",   script: "rebalance_blocks.py",   icon: "prompt", description: "Rebalancea bloques de un guion existente." },
    { id: "normalizar_guiones", label: "normalizar_guiones.py", script: "normalizar_guiones.py", icon: "prompt", description: "Normaliza formato Iago/María en guiones." },
  ],
  source: [
    { id: "pdfs",      label: "PDFs",        folder: "PDFs/",        ext: ".pdf",   count: 22, icon: "doc"    },
    { id: "guiones",   label: "Guiones",     folder: "Guiones/",     ext: ".txt",   count: 18, icon: "doc"    },
    { id: "escaletas", label: "Escaletas",   folder: "escaletas/",   ext: ".md",    count: 11, icon: "doc"    },
    { id: "episodios", label: "Audio",       folder: "episodios/",   ext: ".mp3",   count: 14, icon: "play"   },
    { id: "video",     label: "Vídeo",       folder: "videopodcast/",ext: ".mp4",   count:  4, icon: "play"   },
    { id: "logs",      label: "Logs",        folder: "logs/",        ext: ".jsonl", count: 38, icon: "log"    },
  ],
};

// Pipelines — formulario de cada script (lanzador)
const PIPELINE_FORMS = {
  generar_guion: {
    script: "generar_guion.py",
    description: "Genera el guion M de un módulo a partir del PDF temático y docs vivos.",
    fields: [
      { flag: "--modulo",   label: "Módulo",        kind: "select", options: ["M0","M1","M2","M3","M4","M5","M6","M7","M8","M9","M10","M11","M12","M13","M14"], default: "M5", required: true },
      { flag: "--modelo",   label: "Modelo",        kind: "select", options: ["claude-sonnet-4.5","claude-haiku-4.5","claude-opus-4.7"], default: "claude-sonnet-4.5" },
      { flag: "--temperature", label: "Temperatura", kind: "str",    default: "0.7" },
      { flag: "--dual-debate", label: "Debate dual", kind: "bool",   default: true,  help: "Validar con GPT-4o-mini" },
      { flag: "--force",    label: "Forzar regen",  kind: "bool",   default: false },
    ],
  },
  generar_episodio: {
    script: "generar_episodio_v2.py",
    description: "Sintetiza el audio del episodio con voces de Iago y María.",
    fields: [
      { flag: "--episodio", label: "Episodio",      kind: "str",    default: "M5",         required: true, placeholder: "M5 · M3_T2 · …" },
      { flag: "--voz-iago", label: "Voice Iago",    kind: "str",    default: "pNInz6obpgDQGcFmaJgB" },
      { flag: "--voz-maria",label: "Voice María",   kind: "str",    default: "EXAVITQu4vr4xnSDxMaL" },
      { flag: "--model",    label: "Modelo TTS",    kind: "select", options: ["eleven_v3","eleven_turbo_v2_5"], default: "eleven_v3" },
      { flag: "--bed",      label: "Música de fondo",kind: "bool",  default: true },
    ],
  },
  validar_episodio: {
    script: "validar_episodio.py",
    description: "Verifica audio (gaps, loudness, duración) y emite checks.json.",
    fields: [
      { flag: "--episodio", label: "Episodio",        kind: "str",    default: "M3",   required: true },
      { flag: "--lufs",     label: "Target LUFS",     kind: "str",    default: "-16" },
      { flag: "--max-gap",  label: "Gap máximo (s)",  kind: "str",    default: "3.0" },
      { flag: "--auto-fix", label: "Auto-fix",        kind: "bool",   default: false, help: "Corrige loudness y silencios sin preguntar" },
    ],
  },
  producir_episodio: {
    script: "producir_episodio.py",
    description: "Pipeline completo: guion → audio → validación → vídeo.",
    fields: [
      { flag: "--modulo",   label: "Módulo",          kind: "select", options: ["M0","M1","M2","M3","M4","M5","M6","M7","M8"], default: "M5", required: true },
      { flag: "--include-video", label: "Incluir vídeo", kind: "bool", default: false, help: "Lanza también Kling (+24€)" },
      { flag: "--dry-run",  label: "Dry-run",         kind: "bool",   default: false },
    ],
  },
};

// Fuentes — items por carpeta (más realista que listar uno por uno)
const SOURCE_ITEMS = {
  pdfs: [
    { name: "RESUMEN_M3.pdf", size: "1.2 MB", t: "2026-04-20", url: "assets/pdf/RESUMEN_M3.pdf" },
    { name: "RESUMEN_M5.pdf", size: "1.1 MB", t: "2026-05-02", url: "assets/pdf/RESUMEN_M5.pdf" },
    { name: "RESUMEN_M7.pdf", size: "0.9 MB", t: "2026-05-04", url: "assets/pdf/RESUMEN_M7.pdf" },
    { name: "M0.pdf",         size: "1.8 MB", t: "2026-04-12" },
    { name: "M1.pdf",         size: "2.1 MB", t: "2026-04-13" },
    { name: "M2.pdf",         size: "2.4 MB", t: "2026-04-15" },
    { name: "M3.pdf",         size: "2.4 MB", t: "2026-04-20" },
    { name: "M4.pdf",         size: "2.8 MB", t: "2026-04-28" },
    { name: "M6.pdf",         size: "1.9 MB", t: "2026-05-04" },
  ],
  guiones: [
    { name: "M0_guion.txt", size: "38 KB", t: "2026-04-12" },
    { name: "M3_guion.txt", size: "39 KB", t: "2026-05-08" },
    { name: "M3_T1.txt",    size: "12 KB", t: "2026-05-09" },
    { name: "M3_T2.txt",    size: "11 KB", t: "2026-05-11" },
    { name: "M5_guion.txt", size: "41 KB", t: "2026-05-12" },
  ],
  escaletas: [
    { name: "M0.md", size: "8 KB",  t: "2026-04-12" },
    { name: "M3.md", size: "11 KB", t: "2026-05-08" },
    { name: "M3_T2.md", size: "11 KB", t: "2026-05-11" },
    { name: "M5.md", size: "9 KB",  t: "2026-05-12" },
  ],
  episodios: [
    { name: "M7_T1.mp3",    size: "13 MB",  t: "2026-05-12", url: "assets/audio/M7_T1.mp3"  },
    { name: "M10_T5.mp3",   size: "11 MB",  t: "2026-05-09", url: "assets/audio/M10_T5.mp3" },
    { name: "M12_T2.mp3",   size: "9 MB",   t: "2026-05-08", url: "assets/audio/M12_T2.mp3" },
    { name: "M0.mp3",       size: "44 MB",  t: "2026-04-13" },
    { name: "M3.mp3",       size: "52 MB",  t: "2026-05-09" },
    { name: "M3_T2.mp3",    size: "4.8 MB", t: "2026-05-12", err: "truncado @ 03:14" },
  ],
  video: [
    { name: "intro.mp4", size: "8 MB",   t: "2026-04-01", url: "assets/video/intro.mp4" },
    { name: "M0.mp4",    size: "412 MB", t: "2026-04-15" },
    { name: "M3.mp4",    size: "488 MB", t: "2026-05-10", err: "drift @ 41:22" },
  ],
  logs: [
    { name: "2026-05-12_M3.jsonl",   size: "184 KB", t: "hoy" },
    { name: "2026-05-12_M3_T2.jsonl",size:  "28 KB", t: "hoy" },
    { name: "2026-05-11_M5.jsonl",   size: "212 KB", t: "ayer" },
    { name: "2026-05-10_M4.jsonl",   size:  "92 KB", t: "hace 2d" },
    { name: "ai_usage.jsonl",        size: "4.2 MB", t: "auto" },
  ],
};

// Optimizar — recomendaciones (heurísticas sobre ai_usage.jsonl)
const OPT_RECS = [
  { id: "T01",         severity: "critical", title: "Modelo caro para output corto",
    evidence: "84 llamadas a sonnet-4.6 con output <300 tokens (12% del gasto)",
    action: "Cambiar a haiku-4.5 para validaciones y prompts cortos.",
    savings: 8.42 },
  { id: "HOT-SOURCE",  severity: "warning",  title: "Una sola fuente concentra >40% del gasto",
    evidence: "generar_guion.py representa el 52% del coste (74.84€)",
    action: "Cachear PDFs ya procesados; reusar prompts del system.",
    savings: 4.18 },
  { id: "FAILS",       severity: "warning",  title: "Reintentos sin backoff",
    evidence: "11 fallos consecutivos en eleven_v3 (502) sin pausa exponencial",
    action: "Implementar exponential backoff con jitter en el adapter.",
    savings: 1.32 },
  { id: "VERBOSE",     severity: "info",     title: "Prompts demasiado verbosos",
    evidence: "Media de 4.2k tokens de input por llamada (vs benchmark 1.8k)",
    action: "Mover boilerplate al system; usar few-shot solo cuando aporte.",
    savings: 2.04 },
  { id: "CACHE",       severity: "info",     title: "Falta caché de prompts repetidos",
    evidence: "Misma intro de Iago/María enviada 142 veces este mes",
    action: "Activar prompt-caching de Anthropic en la generación de bloques.",
    savings: 3.66 },
];

// Consumo — saldo por proveedor
const PROVIDER_BALANCE = [
  { id: "anthropic",  topped: 200.00, spent: 133.40, calls:  428 },
  { id: "openai",     topped:  40.00, spent:   4.80, calls:   92 },
  { id: "elevenlabs", topped:  60.00, spent:  51.60, calls: 1840 },
  { id: "kling",      topped: 100.00, spent:  72.00, calls:    3 },
];
const TOPUPS = [
  { t: "2026-05-01 09:12", provider: "anthropic",  amount: 100, note: "Recarga mensual" },
  { t: "2026-04-22 14:38", provider: "elevenlabs", amount:  30, note: "Saldo bajo" },
  { t: "2026-04-15 10:05", provider: "anthropic",  amount: 100, note: "—" },
  { t: "2026-04-01 11:00", provider: "kling",      amount: 100, note: "Setup inicial" },
  { t: "2026-03-28 16:24", provider: "openai",     amount:  40, note: "Recarga" },
  { t: "2026-03-15 09:00", provider: "elevenlabs", amount:  30, note: "Recarga" },
];

// Log JSONL realista
const LOG_LINES = [
  `{"t":"12:42:18","lvl":"INFO", "src":"runner","msg":"M5 pipeline start","mode":"v2"}`,
  `{"t":"12:42:22","lvl":"INFO", "src":"guion","msg":"PDF parsed","pages":18,"chars":42018}`,
  `{"t":"12:42:31","lvl":"INFO", "src":"claude","msg":"generation started","model":"sonnet-4.5","in":3804}`,
  `{"t":"12:43:14","lvl":"INFO", "src":"claude","msg":"block 1 done","tokens":1240,"cost":0.018}`,
  `{"t":"12:43:48","lvl":"INFO", "src":"claude","msg":"block 2 done","tokens":1880,"cost":0.024}`,
  `{"t":"12:44:22","lvl":"WARN", "src":"claude","msg":"rate limit hit","retry_in":8}`,
  `{"t":"12:44:30","lvl":"INFO", "src":"claude","msg":"resuming"}`,
  `{"t":"12:45:18","lvl":"INFO", "src":"claude","msg":"block 3 done","tokens":2104,"cost":0.026}`,
  `{"t":"12:46:02","lvl":"INFO", "src":"dual","msg":"debate convergence","agreement":0.94}`,
  `{"t":"12:46:48","lvl":"INFO", "src":"guion","msg":"saved","path":"Guiones/M5_guion.txt"}`,
  `{"t":"12:47:12","lvl":"INFO", "src":"eleven","msg":"synthesis start","blocks":7}`,
  `{"t":"12:47:38","lvl":"INFO", "src":"eleven","msg":"block synthesized","blk":1,"dur":0.42,"cost":0.008}`,
  `{"t":"12:48:14","lvl":"INFO", "src":"eleven","msg":"block synthesized","blk":2,"dur":1.88,"cost":0.032}`,
];

// ════════════════════════════════════════════════════════════
// PAGE · MAPA
// ════════════════════════════════════════════════════════════
function PageMapa({ onNav, onOpenAI }) {
  const [hover, setHover] = React.useState(null);
  const [view, setView]   = React.useState("grafo"); // grafo | tabla

  const KIND_COLOR = { generator: "var(--info)", system: "var(--y)", generated: "var(--ok)" };
  const KIND_LABEL = { generator: "GENERATOR · IA", system: "SYSTEM · pipeline", generated: "GENERATED · output" };

  const CW = 760, CH = 600;

  return (
    <div className="content">
      <PageHeader
        title="Mapa de componentes"
        sub="Grafo del cockpit · 3 tipos de nodo · persistido en components_map.json"
        actions={
          <React.Fragment>
            <Btn sm kind="ghost" icon={<Icon name="refresh" size={11}/>}
                 onClick={() => window.location.reload()}>Reescanear</Btn>
            <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Mapa de componentes", purpose: "improve" })}
                 icon={<Icon name="spark" size={11}/>}>Mejorar con IA</Btn>
          </React.Fragment>
        }
      />
      <SourcePills files={srcFor("mapa")}/>

      <div className="row mb-8" style={{ justifyContent: "space-between" }}>
        <div className="row gap-3">
          {["grafo", "tabla"].map((v) => (
            <div key={v} className={`btn sm ${view === v ? "primary" : ""}`}
                 onClick={() => setView(v)} style={{ cursor: "pointer" }}>
              {v.toUpperCase()}
            </div>
          ))}
        </div>
        <div className="mono dim" style={{ fontSize: 11, letterSpacing: "0.08em" }}>
          {MAP_NODES.length} nodos · {MAP_EDGES.length} aristas
        </div>
      </div>

      {view === "grafo" ? (
        <Panel
          title={<span><Icon name="map" size={12}/> &nbsp;Grafo de componentes</span>}
          meta="cockpit/components_map.json"
          noPad
        >
          <div style={{
            background: "#0A0A0A",
            backgroundImage:
              "linear-gradient(rgba(245,196,0,0.04) 1px, transparent 1px)," +
              "linear-gradient(90deg, rgba(245,196,0,0.04) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
            position: "relative",
            height: CH,
            overflow: "hidden",
          }}>
            {/* Column labels */}
            {[
              { x: 60,  label: "GENERATORS" },
              { x: 320, label: "SYSTEMS" },
              { x: 600, label: "GENERATED" },
            ].map((c) => (
              <div key={c.label} style={{
                position: "absolute", left: c.x, top: 10,
                fontFamily: "var(--f-display)", fontSize: 10, color: "var(--y)",
                letterSpacing: "0.2em", opacity: 0.7,
              }}>{c.label}</div>
            ))}

            <svg viewBox={`0 0 ${CW} ${CH}`} preserveAspectRatio="none"
                 style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }}>
              <defs>
                <marker id="mp-arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto">
                  <path d="M0 0 L10 5 L0 10 z" fill="var(--y)"/>
                </marker>
              </defs>
              {MAP_EDGES.map(([a, b], i) => {
                const na = MAP_NODES.find(n => n.id === a);
                const nb = MAP_NODES.find(n => n.id === b);
                if (!na || !nb) return null;
                const x1 = na.x + 140, y1 = na.y + 26;
                const x2 = nb.x - 4,  y2 = nb.y + 26;
                const sel = hover && (a === hover || b === hover);
                return (
                  <line key={i} x1={x1} y1={y1} x2={x2} y2={y2}
                        stroke="var(--y)" strokeOpacity={sel ? 0.95 : 0.35}
                        strokeWidth={sel ? 2 : 1.2} markerEnd="url(#mp-arr)"/>
                );
              })}
            </svg>

            {MAP_NODES.map((n) => (
              <div key={n.id}
                   onMouseEnter={() => setHover(n.id)}
                   onMouseLeave={() => setHover(null)}
                   style={{
                     position: "absolute", left: n.x, top: n.y,
                     width: 140, padding: "8px 10px",
                     background: "var(--panel-2)",
                     border: "1px solid var(--border-2)",
                     borderLeft: `3px solid ${KIND_COLOR[n.kind]}`,
                     boxShadow: hover === n.id ? `0 0 0 1px ${KIND_COLOR[n.kind]}` : "none",
                     cursor: "pointer",
                   }}>
                <div className="mono" style={{
                  fontSize: 8, letterSpacing: "0.16em",
                  color: KIND_COLOR[n.kind], marginBottom: 2,
                }}>{n.kind.toUpperCase()}</div>
                <div className="display" style={{
                  fontSize: 11, letterSpacing: "0.04em",
                  color: "var(--text)", lineHeight: 1.2,
                }}>{n.label}</div>
              </div>
            ))}

            <div style={{
              position: "absolute", left: 12, bottom: 12,
              background: "rgba(0,0,0,0.7)",
              border: "1px solid var(--border)",
              padding: "8px 12px",
              fontFamily: "var(--f-mono)",
              fontSize: 10,
              color: "var(--text-dim)",
              display: "flex", flexDirection: "column", gap: 4,
              letterSpacing: "0.08em",
            }}>
              {["generator","system","generated"].map((k) => (
                <div key={k} className="row gap-3">
                  <span style={{ width: 12, height: 12, background: "var(--panel-2)", borderLeft: `3px solid ${KIND_COLOR[k]}` }}/>
                  {KIND_LABEL[k]}
                </div>
              ))}
            </div>
          </div>
        </Panel>
      ) : (
        <Panel noPad>
          <table className="tbl">
            <thead>
              <tr>
                <th style={{ width: 200 }}>ID</th>
                <th>Label</th>
                <th style={{ width: 140 }}>Tipo</th>
                <th style={{ width: 70, textAlign: "right" }}>Aristas</th>
              </tr>
            </thead>
            <tbody>
              {MAP_NODES.map((n) => {
                const ins = MAP_EDGES.filter(([_, b]) => b === n.id).length;
                const outs = MAP_EDGES.filter(([a, _]) => a === n.id).length;
                return (
                  <tr key={n.id}>
                    <td><span className="mono" style={{ fontSize: 11, color: "var(--y)" }}>{n.id}</span></td>
                    <td className="display" style={{ fontSize: 13 }}>{n.label}</td>
                    <td>
                      <span className="badge" style={{ color: KIND_COLOR[n.kind], borderColor: KIND_COLOR[n.kind] }}>
                        {n.kind}
                      </span>
                    </td>
                    <td className="mono dim" style={{ textAlign: "right", fontSize: 11 }}>{ins} ← · {outs} →</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Panel>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · CONECTORES
// ════════════════════════════════════════════════════════════
function PageConectores({ onNav, onOpenAI }) {
  return (
    <div className="content">
      <PageHeader
        title="Conectores"
        sub="Servicios externos · pipelines del repo · fuentes de contenido"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Conectores", purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Mejorar con IA</Btn>
        }
      />
      <SourcePills files={srcFor("conectores")}/>

      {/* Servicios IA */}
      <div className="h2">
        <Icon name="plug" size={14}/> Servicios IA
        <span className="mono dim" style={{ fontSize: 10, marginLeft: "auto", letterSpacing: "0.08em" }}>
          {CONNECTORS.service.filter(s => s.kind !== "distribution").length} servicios
        </span>
      </div>
      <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
        {CONNECTORS.service.filter(s => s.kind !== "distribution").map((c) => (
          <div key={c.id} className="panel" style={{ padding: "14px 16px" }}>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
              <div className="display" style={{ fontSize: 13, letterSpacing: "0.06em" }}>{c.label}</div>
              <StatusDot status={c.status}/>
            </div>
            <div className="mono dim" style={{ fontSize: 11, marginBottom: 6 }}>{c.detail}</div>
            <div className="row" style={{ justifyContent: "space-between", marginTop: 8 }}>
              <span className="badge">{c.env}</span>
              <span className="mono" style={{ fontSize: 10, color: "var(--text-mute)" }}>
                {c.latency}ms
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Distribución — Spotify / iVoox / LinkedIn */}
      <div className="h2">
        <Icon name="map" size={14}/> Distribución y métricas
        <Btn sm kind="ghost" onClick={() => onNav("metricas")} icon={<Icon name="arrow" size={10}/>}>
          Ver métricas
        </Btn>
      </div>
      <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
        {CONNECTORS.service.filter(s => s.kind === "distribution").map((c) => (
          <div key={c.id} className="panel"
               style={{ padding: "14px 16px", cursor: "pointer", borderLeft: "3px solid var(--info)" }}
               onClick={() => onNav("metricas")}>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
              <div className="display" style={{ fontSize: 13, letterSpacing: "0.06em" }}>{c.label}</div>
              <StatusDot status={c.status}/>
            </div>
            <div className="mono dim" style={{ fontSize: 11, marginBottom: 6 }}>{c.detail}</div>
            <div className="row" style={{ justifyContent: "space-between", marginTop: 8 }}>
              <span className="badge">{c.env}</span>
              <span className="mono" style={{ fontSize: 10, color: "var(--text-mute)" }}>
                {c.latency}ms
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Pipelines */}
      <div className="h2">
        <Icon name="prompt" size={14}/> Pipelines del repo
        <span className="mono dim" style={{ fontSize: 10, marginLeft: "auto", letterSpacing: "0.08em" }}>
          {CONNECTORS.pipeline.length} scripts
        </span>
      </div>
      <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))" }}>
        {CONNECTORS.pipeline.map((c) => (
          <div key={c.id} className="panel" style={{ padding: "14px 16px" }}>
            <div className="row gap-3" style={{ marginBottom: 6 }}>
              <Icon name={c.icon} size={12}/>
              <span className="display" style={{ fontSize: 13, letterSpacing: "0.04em" }}>{c.label}</span>
            </div>
            <div className="mono" style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 8, minHeight: 32 }}>
              {c.description}
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="mono" style={{ fontSize: 10, color: "var(--y)" }}>{c.script}</span>
              {PIPELINE_FORMS[c.id]
                ? <Btn sm onClick={() => onNav("lanzador")}>Lanzar →</Btn>
                : <span className="mono" style={{ fontSize: 9, color: "var(--text-mute)" }}>sin form</span>}
            </div>
          </div>
        ))}
      </div>

      {/* Fuentes */}
      <div className="h2">
        <Icon name="folder" size={14}/> Fuentes de contenido
        <span className="mono dim" style={{ fontSize: 10, marginLeft: "auto", letterSpacing: "0.08em" }}>
          {CONNECTORS.source.length} tipos
        </span>
      </div>
      <div className="grid gap-8" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
        {CONNECTORS.source.map((c) => (
          <div key={c.id} className="panel"
               style={{ padding: "14px 16px", cursor: "pointer" }}
               onClick={() => onNav("fuentes")}>
            <div className="row gap-3" style={{ marginBottom: 6 }}>
              <Icon name={c.icon} size={12}/>
              <span className="display" style={{ fontSize: 13, letterSpacing: "0.04em" }}>{c.label}</span>
              <span style={{ marginLeft: "auto", color: "var(--y)", fontFamily: "var(--f-mono)", fontSize: 13 }}>
                {c.count}
              </span>
            </div>
            <div className="mono" style={{ fontSize: 10, color: "var(--y)" }}>{c.folder}<span className="dim">{c.ext}</span></div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · LANZADOR (Generar prompt para Codex)
// ════════════════════════════════════════════════════════════
function PageLanzador({ onNav, onOpenAI }) {
  const ids = Object.keys(PIPELINE_FORMS);
  const [sel, setSel] = React.useState(ids[0]);
  const [vals, setVals] = React.useState({});
  const [copied, setCopied] = React.useState(false);
  const [running, setRunning] = React.useState(false);
  const [output, setOutput] = React.useState([]);

  const form = PIPELINE_FORMS[sel];

  // Reset values when changing pipeline
  React.useEffect(() => {
    const init = {};
    form.fields.forEach(f => { init[f.flag] = f.default; });
    setVals(init);
    setOutput([]);
  }, [sel]);

  const update = (flag, v) => setVals((s) => ({ ...s, [flag]: v }));

  const cmd = (() => {
    const parts = [`python ${form.script}`];
    form.fields.forEach(f => {
      const v = vals[f.flag];
      if (f.kind === "bool") { if (v) parts.push(f.flag); }
      else if (v != null && v !== "") parts.push(`${f.flag} ${JSON.stringify(v).replace(/"/g, "")}`);
    });
    return parts.join(" \\\n  ");
  })();

  const copy = () => {
    navigator.clipboard?.writeText(cmd.replace(/\\\n  /g, " "));
    setCopied(true);
    setTimeout(() => setCopied(false), 1400);
  };

  const run = async () => {
    setRunning(true);
    setOutput([`$ ${cmd.replace(/\\\n  /g, " ")}`]);
    // Construye flags como pares [flag, value] para el backend
    const flags = [];
    form.fields.forEach(f => {
      const v = vals[f.flag];
      if (f.kind === "bool") { if (v) flags.push([f.flag, true]); }
      else if (v != null && v !== "") flags.push([f.flag, v]);
    });
    try {
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ script: form.script, flags }),
      });
      const data = await res.json();
      if (data.ok) {
        setOutput((o) => [...o,
          `[${new Date().toLocaleTimeString()}] INFO  runner: lanzado en background`,
          `[${new Date().toLocaleTimeString()}] INFO  pid=${data.pid} log=${data.log}`,
          `[${new Date().toLocaleTimeString()}] INFO  consulta el log en logs/${data.log}`,
        ]);
      } else {
        setOutput((o) => [...o, `[error] ${data.error || "no se pudo lanzar"}`]);
      }
    } catch (e) {
      setOutput((o) => [...o, `[offline] ${e.message || e} — usa la cabina Streamlit`]);
    }
    setRunning(false);
  };

  return (
    <div className="content">
      <PageHeader
        title="Lanzador de pipelines"
        sub="Rellena el formulario y genera el comando · ejecuta localmente o copia a Codex"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: `Pipeline · ${form.script}`, purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Mejorar con IA</Btn>
        }
      />
      <SourcePills files={srcFor("lanzador")}/>

      <div className="grid gap-8" style={{ gridTemplateColumns: "1fr 1.2fr" }}>
        {/* LEFT — pipeline selector + form */}
        <div className="col gap-8">
          <Panel title={<span><Icon name="prompt" size={12}/> &nbsp;Pipeline</span>}>
            <div className="col gap-3">
              {ids.map((id) => (
                <div key={id}
                     onClick={() => setSel(id)}
                     style={{
                       padding: "8px 10px",
                       border: "1px solid",
                       borderColor: sel === id ? "var(--y)" : "var(--border)",
                       background: sel === id ? "var(--y-soft)" : "var(--panel-2)",
                       cursor: "pointer",
                     }}>
                  <div className="display" style={{
                    fontSize: 12, letterSpacing: "0.06em",
                    color: sel === id ? "var(--y)" : "var(--text)",
                  }}>{id}</div>
                  <div className="mono dim" style={{ fontSize: 10, marginTop: 2 }}>
                    {PIPELINE_FORMS[id].script}
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel
            title={<span><Icon name="settings" size={12}/> &nbsp;Parámetros</span>}
            meta={form.script}
          >
            <div className="mono dim mb-12" style={{ fontSize: 11, lineHeight: 1.5 }}>
              {form.description}
            </div>
            <div className="col gap-4">
              {form.fields.map((f) => (
                <div key={f.flag}>
                  <div className="row" style={{ justifyContent: "space-between", marginBottom: 4 }}>
                    <span className="display" style={{ fontSize: 11, letterSpacing: "0.08em", color: "var(--text-dim)" }}>
                      {f.label}{f.required && <span style={{ color: "var(--alert)" }}> *</span>}
                    </span>
                    <span className="mono" style={{ fontSize: 10, color: "var(--y)" }}>{f.flag}</span>
                  </div>
                  {f.kind === "bool" ? (
                    <div className="row gap-3">
                      {[true, false].map((b) => (
                        <button key={String(b)}
                                className={`btn sm ${vals[f.flag] === b ? "primary" : ""}`}
                                onClick={() => update(f.flag, b)}
                                style={{ flex: 1 }}>
                          {b ? "Sí" : "No"}
                        </button>
                      ))}
                    </div>
                  ) : f.kind === "select" ? (
                    <select className="ai-input" value={vals[f.flag] ?? ""}
                            onChange={(e) => update(f.flag, e.target.value)}
                            style={{ width: "100%" }}>
                      {f.options.map(o => <option key={o} value={o}>{o}</option>)}
                    </select>
                  ) : (
                    <input className="ai-input" value={vals[f.flag] ?? ""}
                           onChange={(e) => update(f.flag, e.target.value)}
                           placeholder={f.placeholder}
                           style={{ width: "100%" }}/>
                  )}
                  {f.help && <div className="mono" style={{ fontSize: 10, color: "var(--text-mute)", marginTop: 3 }}>{f.help}</div>}
                </div>
              ))}
            </div>
          </Panel>
        </div>

        {/* RIGHT — generated command + run */}
        <div className="col gap-8">
          <Panel
            title={<span><Icon name="doc" size={12}/> &nbsp;Comando generado</span>}
            meta="bash · listo para pegar"
            actions={
              <React.Fragment>
                <Btn sm kind="ghost" onClick={copy}>
                  {copied ? "Copiado ✓" : "Copiar"}
                </Btn>
                <Btn sm kind="primary" onClick={run} icon={<Icon name="play" size={10}/>}>
                  {running ? "Ejecutando…" : "Ejecutar"}
                </Btn>
              </React.Fragment>
            }
          >
            <pre className="code" style={{ borderLeftColor: "var(--y)", fontSize: 12.5, padding: "12px 14px" }}>
{cmd}
            </pre>
            <div className="row gap-4 mt-8 mono" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.08em" }}>
              <span>cwd: <span style={{ color: "var(--y)" }}>~/maquinaria-pesada</span></span>
              <span>·</span>
              <span>sandbox: workspace-write</span>
              <span>·</span>
              <span>timeout: 30m</span>
            </div>
          </Panel>

          <Panel
            title={<span><Icon name="log" size={12}/> &nbsp;Salida</span>}
            meta={running ? "streaming…" : output.length ? "finalizado" : "sin ejecutar"}
          >
            {output.length === 0 ? (
              <div className="mono dim" style={{ fontSize: 11, padding: "20px 0", textAlign: "center" }}>
                Pulsa <b style={{ color: "var(--y)" }}>Ejecutar</b> para lanzar el pipeline aquí.
              </div>
            ) : (
              <pre className="code" style={{ borderLeftColor: running ? "var(--info)" : "var(--ok)", maxHeight: 320, overflow: "auto" }}>
                {output.join("\n")}
                {running && <span className="ai-cursor"/>}
              </pre>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · FUENTES
// ════════════════════════════════════════════════════════════
function PageFuentes({ onNav, onOpenAI }) {
  const [src, setSrc] = React.useState("pdfs");
  const [filter, setFilter] = React.useState("");
  const [picked, setPicked] = React.useState(null);

  const source = CONNECTORS.source.find(s => s.id === src);
  const items = (SOURCE_ITEMS[src] || []).filter(it => it.name.toLowerCase().includes(filter.toLowerCase()));

  React.useEffect(() => { setPicked(items[0] || null); }, [src]);

  return (
    <div className="content">
      <PageHeader
        title="Fuentes de contenido"
        sub="Filesystem como única fuente de verdad · PDFs, guiones, escaletas, audio, vídeo, logs"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: `Fuentes · ${picked?.name}`, purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Analizar con IA</Btn>
        }
      />
      <SourcePills files={srcFor("fuentes")}/>

      {/* Source-type picker */}
      <div className="row gap-3 mb-12" style={{ flexWrap: "wrap" }}>
        {CONNECTORS.source.map((s) => (
          <div key={s.id}
               className={`btn sm ${src === s.id ? "primary" : ""}`}
               onClick={() => setSrc(s.id)}
               style={{ cursor: "pointer" }}>
            <Icon name={s.icon} size={10}/>
            {s.label}
            <span className="mono" style={{
              fontSize: 9, padding: "1px 5px",
              background: src === s.id ? "rgba(0,0,0,0.2)" : "var(--panel-2)",
              color: src === s.id ? "#0D0D0D" : "var(--text-mute)",
              borderRadius: 2,
            }}>{(SOURCE_ITEMS[s.id] || []).length}</span>
          </div>
        ))}
      </div>

      <div className="grid gap-8" style={{ gridTemplateColumns: "360px 1fr" }}>
        {/* LEFT — file list */}
        <Panel
          title={<span><Icon name="folder" size={12}/> &nbsp;{source.folder}</span>}
          meta={`${items.length}/${(SOURCE_ITEMS[src] || []).length}`}
        >
          <input className="ai-input mb-8" placeholder="Filtrar por nombre…"
                 value={filter} onChange={(e) => setFilter(e.target.value)}
                 style={{ width: "100%" }}/>
          <div className="col gap-2" style={{ maxHeight: 480, overflowY: "auto" }}>
            {items.map((it) => (
              <div key={it.name}
                   onClick={() => setPicked(it)}
                   style={{
                     padding: "8px 10px",
                     borderTop:    `1px solid ${picked?.name === it.name ? "var(--y)" : "var(--border)"}`,
                     borderRight:  `1px solid ${picked?.name === it.name ? "var(--y)" : "var(--border)"}`,
                     borderBottom: `1px solid ${picked?.name === it.name ? "var(--y)" : "var(--border)"}`,
                     borderLeft:   it.err ? "3px solid var(--alert)"
                                : picked?.name === it.name ? "3px solid var(--y)"
                                : "1px solid var(--border)",
                     background: picked?.name === it.name ? "var(--y-soft)" : "var(--panel-2)",
                     cursor: "pointer",
                   }}>
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <span className="mono" style={{
                    fontSize: 12,
                    color: picked?.name === it.name ? "var(--y)" : "var(--text)",
                    wordBreak: "break-all",
                  }}>{it.name}</span>
                </div>
                <div className="row gap-3 mt-2 mono" style={{ fontSize: 10, color: "var(--text-mute)" }}>
                  <span>{it.size}</span>
                  <span>·</span>
                  <span>{it.t}</span>
                  {it.err && <span style={{ color: "var(--alert)", marginLeft: "auto" }}>{it.err}</span>}
                </div>
              </div>
            ))}
            {!items.length && <div className="mono dim" style={{ fontSize: 11, padding: 16, textAlign: "center" }}>
              Sin items que coincidan.
            </div>}
          </div>
        </Panel>

        {/* RIGHT — viewer */}
        <Panel
          title={picked ? <span><Icon name={source.icon} size={12}/> &nbsp;{picked.name}</span>
                        : <span>Selecciona un archivo</span>}
          meta={picked ? `${picked.size} · ${picked.t}` : ""}
        >
          {picked ? (
            <div className="col gap-8">
              <div className="row gap-4">
                <div style={{ flex: 1 }}>
                  <div className="display" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.16em" }}>RUTA</div>
                  <div className="mono" style={{ fontSize: 12, color: "var(--y)", marginTop: 4 }}>{source.folder}{picked.name}</div>
                </div>
                <Btn sm kind="ghost" icon={<Icon name="folder" size={10}/>}
                     onClick={() => fetch("/api/reveal", {
                       method: "POST",
                       headers: { "Content-Type": "application/json" },
                       body: JSON.stringify({ path: source.folder + picked.name }),
                     }).catch(() => {})}>
                  Revelar
                </Btn>
                <Btn sm icon={<Icon name="doc" size={10}/>}
                     onClick={() => window.open(`/files/${source.folder}${picked.name}`, "_blank")}>
                  Descargar
                </Btn>
              </div>

              {/* Preview placeholder per source type */}
              {src === "pdfs" && (
                picked.url ? (
                  <div style={{ background: "#525659", border: "1px solid var(--border)" }}>
                    <iframe
                      key={picked.url}
                      src={picked.url + "#view=FitH&toolbar=1"}
                      style={{ width: "100%", height: 600, border: 0, display: "block" }}
                      title={picked.name}
                    />
                  </div>
                ) : (
                  <div style={{
                    background: "#F4EFE3", color: "#2A2620", padding: "40px 56px",
                    fontFamily: "Georgia, serif", fontSize: 13, lineHeight: 1.6, minHeight: 280,
                    position: "relative",
                  }}>
                    <div style={{ fontWeight: 700, textTransform: "uppercase", marginBottom: 14, letterSpacing: "0.02em" }}>
                      {picked.name.replace(".pdf", "")} · Resumen temático
                    </div>
                    <div style={{ opacity: 0.7 }}>
                      Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor
                      incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
                      nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
                    </div>
                    <div style={{
                      position: "absolute", top: 10, right: 14,
                      fontFamily: "var(--f-mono)", fontSize: 10, color: "rgba(0,0,0,0.4)",
                      letterSpacing: "0.1em",
                    }}>
                      preview · archivo no disponible localmente
                    </div>
                  </div>
                )
              )}
              {(src === "guiones" || src === "escaletas") && (
                <pre className="code" style={{ maxHeight: 320, overflow: "auto" }}>
{src === "guiones"
? `# ${picked.name}
# generado: ${picked.t}
# encoding: utf-8

[IAGO] Vale María, hoy nos metemos con...
[MARIA] Buena pregunta. Lo bonito es que...
[IAGO] Vamos a desglosarlo: query, key, value.
...`
: `# ${picked.name.replace(".md","")}
> ${picked.size} · ${picked.t}

## 01 · Apertura
- tiempo: \`0:00 → 0:42\`
- palabras: 320
- contenido: saludo, contexto, conexión con módulo anterior.

## 02 · El problema
- tiempo: \`0:42 → 2:10\`
- palabras: 680
...`}
                </pre>
              )}
              {src === "episodios" && (
                <div className="col gap-4">
                  {picked.url ? (
                    <div style={{ background: "#0A0A0A", padding: 16, border: "1px solid var(--border)" }}>
                      <audio
                        key={picked.url}
                        src={picked.url}
                        controls
                        preload="metadata"
                        style={{ width: "100%", filter: "invert(0.92) hue-rotate(180deg)" }}
                      />
                    </div>
                  ) : (
                    <React.Fragment>
                      <div style={{ background: "#0A0A0A", padding: "20px 16px", height: 100, display: "flex", alignItems: "center", gap: 1 }}>
                        {Array.from({ length: 80 }).map((_, i) => (
                          <div key={i} style={{
                            flex: 1,
                            height: `${20 + Math.abs(Math.sin(i * 0.4)) * 50}px`,
                            background: picked.err && i > 50 ? "var(--alert)" : "var(--y)",
                            opacity: 0.8,
                          }}/>
                        ))}
                      </div>
                      <div className="row gap-3">
                        <Btn sm onClick={() => window.open(`/files/${source.folder}${picked.name}`, "_blank")}>
                          <Icon name="play" size={11}/> Play
                        </Btn>
                        <span className="mono dim" style={{ fontSize: 11 }}>{picked.name}</span>
                      </div>
                    </React.Fragment>
                  )}
                </div>
              )}
              {src === "video" && (
                picked.url ? (
                  <div style={{ background: "#000", border: "1px solid var(--border)" }}>
                    <video
                      key={picked.url}
                      src={picked.url}
                      controls
                      preload="metadata"
                      style={{ width: "100%", aspectRatio: "16/9", display: "block" }}
                    />
                  </div>
                ) : (
                  <div style={{
                    background: "#0A0A0A", aspectRatio: "16/9",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    border: "1px dashed var(--border-2)",
                  }}>
                    <div className="col gap-3" style={{ textAlign: "center" }}>
                      <Icon name="play" size={28}/>
                      <div className="mono dim" style={{ fontSize: 11 }}>{picked.size} · archivo no cacheado</div>
                    </div>
                  </div>
                )
              )}
              {src === "logs" && (
                <pre className="code" style={{ maxHeight: 320, overflow: "auto", fontSize: 11 }}>
{LOG_LINES.slice(0, 8).join("\n")}
...
                </pre>
              )}
            </div>
          ) : (
            <div className="mono dim" style={{ textAlign: "center", padding: 40, fontSize: 12 }}>
              Sin selección.
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · PREVISUALIZAR (Player)
// ════════════════════════════════════════════════════════════
function PagePlayer({ onNav, onOpenAI }) {
  const [tab, setTab] = React.useState("audio");
  const items = tab === "audio" ? SOURCE_ITEMS.episodios : SOURCE_ITEMS.video;
  const [pick, setPick] = React.useState(items[0]?.name);
  React.useEffect(() => { setPick((tab === "audio" ? SOURCE_ITEMS.episodios : SOURCE_ITEMS.video)[0]?.name); }, [tab]);

  const sel = items.find(i => i.name === pick) || items[0];

  return (
    <div className="content">
      <PageHeader
        title="Previsualizar"
        sub="Audio y vídeo generados · escucha y revisa antes de publicar"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: `Preview · ${sel?.name}`, purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Sugerir checks</Btn>
        }
      />
      <SourcePills files={srcFor("player")}/>

      <div className="tabs mb-12">
        {[{ id: "audio", icon: "play", label: "Audio" }, { id: "video", icon: "play", label: "Vídeo" }].map((t) => (
          <div key={t.id} className={`tab ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
            <Icon name={t.icon} size={11}/>
            {t.label}
            <span className="badge" style={{ marginLeft: 4 }}>{tab === "audio" ? SOURCE_ITEMS.episodios.length : SOURCE_ITEMS.video.length}</span>
          </div>
        ))}
      </div>

      <div className="grid gap-8" style={{ gridTemplateColumns: "280px 1fr" }}>
        <Panel title={<span><Icon name="folder" size={12}/> &nbsp;Cola</span>} noPad>
          <div className="col gap-2" style={{ padding: 10 }}>
            {items.map((it) => (
              <div key={it.name}
                   onClick={() => setPick(it.name)}
                   style={{
                     padding: "8px 10px",
                     borderTop:    `1px solid ${pick === it.name ? "var(--y)" : "var(--border)"}`,
                     borderRight:  `1px solid ${pick === it.name ? "var(--y)" : "var(--border)"}`,
                     borderBottom: `1px solid ${pick === it.name ? "var(--y)" : "var(--border)"}`,
                     borderLeft:   it.err ? "3px solid var(--alert)"
                                : pick === it.name ? "3px solid var(--y)"
                                : "1px solid var(--border)",
                     background: pick === it.name ? "var(--y-soft)" : "var(--panel-2)",
                     cursor: "pointer",
                   }}>
                <div className="mono" style={{ fontSize: 12, color: pick === it.name ? "var(--y)" : "var(--text)" }}>{it.name}</div>
                <div className="mono dim" style={{ fontSize: 10, marginTop: 2 }}>{it.size} · {it.t}</div>
                {it.err && <div className="mono" style={{ fontSize: 10, color: "var(--alert)", marginTop: 2 }}>{it.err}</div>}
              </div>
            ))}
          </div>
        </Panel>

        <Panel
          title={<span><Icon name="play" size={12}/> &nbsp;{sel?.name}</span>}
          meta={`${sel?.size} · ${sel?.t}`}
        >
          {tab === "audio" ? (
            <div className="col gap-8">
              {sel?.url ? (
                <div style={{
                  background: "#0A0A0A", padding: "24px 20px", border: "1px solid var(--border)",
                  borderLeft: "3px solid var(--y)",
                }}>
                  {/* Waveform decorative */}
                  <div style={{ position: "relative", height: 80, display: "flex", alignItems: "center", gap: 1, marginBottom: 16 }}>
                    {Array.from({ length: 120 }).map((_, i) => {
                      const h = 12 + Math.abs(Math.sin(i * 0.32)) * 60 + (i % 3) * 6;
                      return (
                        <div key={i} style={{
                          flex: 1, height: `${h}px`,
                          background: "var(--y)", opacity: 0.6,
                        }}/>
                      );
                    })}
                  </div>
                  <audio
                    key={sel.url}
                    src={sel.url}
                    controls
                    preload="metadata"
                    style={{ width: "100%", filter: "invert(0.92) hue-rotate(180deg)" }}
                  />
                </div>
              ) : (
                <div style={{
                  background: "#0A0A0A", padding: "24px 16px", position: "relative",
                  height: 160, display: "flex", alignItems: "center", gap: 1,
                }}>
                  {Array.from({ length: 120 }).map((_, i) => {
                    const fail = sel?.err && i > 80;
                    const h = fail ? 6 : 16 + Math.abs(Math.sin(i * 0.32)) * 80 + (i % 3) * 8;
                    return (
                      <div key={i} style={{
                        flex: 1, height: `${h}px`,
                        background: fail ? "var(--alert)" : "var(--y)",
                        opacity: fail ? 0.5 : 0.85,
                      }}/>
                    );
                  })}
                  <div style={{ position: "absolute", left: "30%", top: 0, bottom: 0, width: 1, background: "var(--y)" }}/>
                  <div style={{
                    position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center",
                    background: "rgba(13,13,13,0.7)",
                  }}>
                    <div className="mono" style={{ fontSize: 11, color: "var(--text-mute)", letterSpacing: "0.16em" }}>
                      ARCHIVO NO CACHEADO LOCALMENTE
                    </div>
                  </div>
                </div>
              )}

              <div className="row" style={{ justifyContent: "space-between" }}>
                <div className="row gap-4">
                  <span className="mono dim" style={{ fontSize: 12 }}>
                    {sel?.url ? "▶ controles HTML5 nativos" : (sel?.err ? "03:14 (truncado)" : "—")}
                  </span>
                </div>
                {sel?.url && (
                  <a href={sel.url} download={sel.name} className="btn sm ghost" style={{ textDecoration: "none" }}>
                    <Icon name="folder" size={11}/> Descargar MP3
                  </a>
                )}
              </div>

              {/* Spec checks */}
              <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
                {[
                  { label: "LUFS",      v: "-15.8", ok: true },
                  { label: "Duración",  v: sel?.err ? "03:14" : "11:08", ok: !sel?.err },
                  { label: "Silencios", v: sel?.err ? "1 (4.2s)" : "0", ok: !sel?.err },
                ].map((s) => (
                  <div key={s.label} className="panel" style={{ padding: "10px 12px", borderLeft: `3px solid ${s.ok ? "var(--ok)" : "var(--alert)"}` }}>
                    <div className="display" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.14em" }}>{s.label}</div>
                    <div className="mono" style={{ fontSize: 18, color: s.ok ? "var(--ok)" : "var(--alert)", marginTop: 4 }}>{s.v}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="col gap-8">
              {sel?.url ? (
                <div style={{ background: "#000", border: "1px solid var(--border)", borderLeft: "3px solid var(--y)" }}>
                  <video
                    key={sel.url}
                    src={sel.url}
                    controls
                    preload="metadata"
                    style={{ width: "100%", aspectRatio: "16/9", display: "block", background: "#000" }}
                  />
                </div>
              ) : (
                <div style={{
                  background: "#0A0A0A", aspectRatio: "16/9",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  position: "relative", border: "1px dashed var(--border-2)",
                }}>
                  <div style={{ position: "absolute", inset: 12, border: "1px solid var(--border)", opacity: 0.4 }}/>
                  <div className="col gap-3" style={{ textAlign: "center" }}>
                    <div style={{ width: 64, height: 64, borderRadius: "50%", background: "var(--y)",
                                  display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto" }}>
                      <span style={{ color: "#0D0D0D", fontSize: 24, marginLeft: 4 }}>▶</span>
                    </div>
                    <div className="mono dim" style={{ fontSize: 11 }}>{sel?.size} · archivo no cacheado</div>
                    {sel?.err && <div className="mono" style={{ fontSize: 11, color: "var(--alert)" }}>{sel.err}</div>}
                  </div>
                </div>
              )}

              <div className="row" style={{ justifyContent: "space-between" }}>
                <span className="mono dim" style={{ fontSize: 12 }}>
                  {sel?.url ? "▶ controles HTML5 nativos · 1920×1080" : "—"}
                </span>
                {sel?.url && (
                  <a href={sel.url} download={sel.name} className="btn sm ghost" style={{ textDecoration: "none" }}>
                    <Icon name="folder" size={11}/> Descargar MP4
                  </a>
                )}
              </div>
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · LOGS
// ════════════════════════════════════════════════════════════
function PageLogs({ onNav, onOpenAI }) {
  const logs = SOURCE_ITEMS.logs;
  const [sel, setSel] = React.useState(logs[0].name);
  const [auto, setAuto] = React.useState(false);
  const [lines, setLines] = React.useState(LOG_LINES);
  const [filter, setFilter] = React.useState("");

  // Auto-refresh: append random line every 5s
  React.useEffect(() => {
    if (!auto) return;
    const id = setInterval(() => {
      const t = new Date().toLocaleTimeString("es-ES", { hour12: false });
      const samples = [
        `{"t":"${t}","lvl":"INFO","src":"runner","msg":"heartbeat","cpu":12,"mem":42}`,
        `{"t":"${t}","lvl":"INFO","src":"claude","msg":"token","model":"haiku-4.5","tokens":${Math.floor(Math.random()*200)+20}}`,
        `{"t":"${t}","lvl":"WARN","src":"eleven","msg":"latency high","ms":${Math.floor(Math.random()*800)+200}}`,
      ];
      setLines((l) => [...l, samples[Math.floor(Math.random() * samples.length)]]);
    }, 1500);
    return () => clearInterval(id);
  }, [auto]);

  const filtered = filter
    ? lines.filter(l => l.toLowerCase().includes(filter.toLowerCase()))
    : lines;

  const counts = lines.reduce((acc, l) => {
    if (l.includes('"ERROR"')) acc.err++;
    else if (l.includes('"WARN"')) acc.warn++;
    else acc.info++;
    return acc;
  }, { info: 0, warn: 0, err: 0 });

  return (
    <div className="content">
      <PageHeader
        title="Logs de producción"
        sub="JSONL en logs/ · auto-refresh opcional · diagnóstico IA sobre las últimas líneas"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({
            target: `Log · ${sel}`,
            purpose: "improve",
          })} icon={<Icon name="spark" size={11}/>}>Diagnóstico con IA</Btn>
        }
      />
      <SourcePills files={srcFor("logs")}/>

      <div className="kpi-grid mb-12">
        <Kpi label="Líneas"     value={lines.length} delta={`auto-refresh ${auto ? "ON" : "OFF"}`} deltaDir={auto ? "up" : ""}/>
        <Kpi label="INFO"       value={counts.info}/>
        <Kpi label="WARN"       value={counts.warn} delta={counts.warn ? "atención" : "ok"}/>
        <Kpi label="ERROR"      value={counts.err}  delta={counts.err ? "investigar" : "limpio"} deltaDir={counts.err ? "dn" : "up"}/>
      </div>

      <div className="grid gap-8" style={{ gridTemplateColumns: "280px 1fr" }}>
        <Panel title={<span><Icon name="folder" size={12}/> &nbsp;Archivos</span>} noPad>
          <div className="col gap-2" style={{ padding: 10 }}>
            {logs.map((l) => (
              <div key={l.name}
                   onClick={() => setSel(l.name)}
                   style={{
                     padding: "8px 10px",
                     border: "1px solid",
                     borderColor: sel === l.name ? "var(--y)" : "var(--border)",
                     background: sel === l.name ? "var(--y-soft)" : "var(--panel-2)",
                     cursor: "pointer",
                   }}>
                <div className="mono" style={{ fontSize: 11, color: sel === l.name ? "var(--y)" : "var(--text)", wordBreak: "break-all" }}>
                  {l.name}
                </div>
                <div className="mono dim" style={{ fontSize: 10, marginTop: 2 }}>{l.size} · {l.t}</div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel
          title={<span><Icon name="log" size={12}/> &nbsp;{sel}</span>}
          meta={auto ? "live · 1.5s" : "snapshot"}
          actions={
            <React.Fragment>
              <input className="ai-input" placeholder="Filtrar…" value={filter}
                     onChange={(e) => setFilter(e.target.value)} style={{ width: 140, fontSize: 11 }}/>
              <button className={`btn sm ${auto ? "primary" : "ghost"}`} onClick={() => setAuto(!auto)}>
                <Icon name="refresh" size={10}/> Auto
              </button>
            </React.Fragment>
          }
        >
          <pre className="code" style={{
            maxHeight: 480, overflow: "auto", fontSize: 11.5,
            borderLeftColor: auto ? "var(--info)" : "var(--y)",
          }}>
            {filtered.map((l, i) => {
              const isErr = l.includes('"ERROR"');
              const isWarn = l.includes('"WARN"');
              const color = isErr ? "var(--alert)" : isWarn ? "var(--warn)" : "var(--text-dim)";
              return (
                <div key={i} style={{ color, whiteSpace: "pre-wrap" }}>{l}</div>
              );
            })}
            {auto && <span className="ai-cursor"/>}
          </pre>
        </Panel>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · OPTIMIZAR
// ════════════════════════════════════════════════════════════
function PageOptimizar({ onNav, onOpenAI }) {
  const totalSavings = OPT_RECS.reduce((s, r) => s + r.savings, 0);
  const sevColor = { critical: "var(--alert)", warning: "var(--warn)", info: "var(--info)" };
  const sevLabel = { critical: "CRÍTICA", warning: "AVISO", info: "INFO" };

  return (
    <div className="content">
      <PageHeader
        title="Optimizar consumo"
        sub="Heurísticas sobre ai_usage.jsonl · sin IA · solo reglas explicables"
        actions={
          <React.Fragment>
            <Btn sm kind="ghost" icon={<Icon name="refresh" size={11}/>}
                 onClick={() => window.location.reload()}>Re-analizar</Btn>
            <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Optimización · reglas", purpose: "improve" })}
                 icon={<Icon name="spark" size={11}/>}>Proponer más reglas</Btn>
          </React.Fragment>
        }
      />
      <SourcePills files={srcFor("optimizar")}/>

      <div className="kpi-grid mb-12">
        <Kpi label="Llamadas analizadas"  value="2.4k"          delta="últimos 30 días"/>
        <Kpi label="Gasto total"           value="142.18" unit="€"/>
        <Kpi label="Ahorro potencial"      value={totalSavings.toFixed(2)} unit="€" delta={`${Math.round((totalSavings / 142.18) * 100)}% del gasto`} deltaDir="up"/>
        <Kpi label="Recomendaciones"       value={OPT_RECS.length} delta={`${OPT_RECS.filter(r => r.severity === "critical").length} críticas`}/>
      </div>

      <div className="h2"><Icon name="brain" size={14}/> Recomendaciones</div>

      <div className="col gap-3">
        {OPT_RECS.map((r) => (
          <div key={r.id} className="panel" style={{
            padding: "14px 18px",
            borderLeft: `3px solid ${sevColor[r.severity]}`,
          }}>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 10 }}>
              <div className="row gap-4">
                <span className="badge" style={{
                  color: sevColor[r.severity],
                  borderColor: sevColor[r.severity],
                  background: r.severity === "critical" ? "rgba(204,34,0,0.08)"
                            : r.severity === "warning"  ? "rgba(232,114,17,0.08)"
                            : "rgba(77,184,255,0.08)",
                }}>{sevLabel[r.severity]}</span>
                <div className="display" style={{ fontSize: 14, letterSpacing: "0.04em" }}>{r.title}</div>
                <span className="mono dim" style={{ fontSize: 10 }}>regla: {r.id}</span>
              </div>
              <div className="col" style={{ alignItems: "flex-end", gap: 0 }}>
                <div className="display" style={{ fontSize: 9, color: "var(--text-mute)", letterSpacing: "0.16em" }}>AHORRO</div>
                <div className="mono" style={{ fontSize: 18, color: "var(--ok)" }}>{r.savings.toFixed(2)}€</div>
              </div>
            </div>
            <div className="grid gap-8" style={{ gridTemplateColumns: "1fr 1fr" }}>
              <div>
                <div className="display mb-4" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.14em" }}>EVIDENCIA</div>
                <div className="mono" style={{ fontSize: 12, color: "var(--text-dim)", lineHeight: 1.5 }}>{r.evidence}</div>
              </div>
              <div>
                <div className="display mb-4" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.14em" }}>ACCIÓN</div>
                <div className="mono" style={{ fontSize: 12, color: "var(--y)", lineHeight: 1.5 }}>{r.action}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · CONSUMO (Tokens + Economics)
// ════════════════════════════════════════════════════════════
function PageConsumo({ onNav, onOpenAI }) {
  const [tab, setTab] = React.useState("uso");
  const totalBalance = PROVIDER_BALANCE.reduce((s, p) => s + (p.topped - p.spent), 0);

  return (
    <div className="content">
      <PageHeader
        title="Consumo · tokens y saldos"
        sub="Agregado de ai_usage.jsonl + recargas por proveedor"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Consumo IA", purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Mejorar con IA</Btn>
        }
      />
      <SourcePills files={srcFor("consumo")}/>

      <div className="kpi-grid mb-12">
        <Kpi label="Tokens · 30d"   value="18.4" unit="M" delta="−12% vs mes anterior" deltaDir="dn"/>
        <Kpi label="Gasto · 30d"    value="142.18" unit="€" delta="57% del budget (250€)"/>
        <Kpi label="Saldo global"   value={totalBalance.toFixed(2)} unit="€" delta={`${PROVIDER_BALANCE.length} proveedores`} deltaDir="up"/>
        <Kpi label="Llamadas · 30d" value="2 402" delta="ø 53/día"/>
      </div>

      <div className="tabs mb-12">
        {[
          { id: "uso",     icon: "coin",  label: "Uso por modelo" },
          { id: "saldo",   icon: "key",   label: "Saldos & recargas" },
          { id: "eventos", icon: "log",   label: "Últimos eventos" },
        ].map((t) => (
          <div key={t.id} className={`tab ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
            <Icon name={t.icon} size={11}/>{t.label}
          </div>
        ))}
      </div>

      {tab === "uso" && (
        <div className="grid gap-8" style={{ gridTemplateColumns: "1.5fr 1fr" }}>
          <Panel title={<span><Icon name="brain" size={12}/> &nbsp;Por modelo</span>} noPad>
            <table className="tbl">
              <thead>
                <tr>
                  <th>Modelo</th>
                  <th style={{ width: 100, textAlign: "right" }}>Tokens</th>
                  <th style={{ width: 90,  textAlign: "right" }}>Coste</th>
                  <th style={{ width: 200 }}>Cuota</th>
                </tr>
              </thead>
              <tbody>
                {TOKEN_DATA.byModel.map((m) => (
                  <tr key={m.model}>
                    <td className="mono" style={{ fontSize: 12, color: "var(--y)" }}>{m.model}</td>
                    <td className="mono tabular" style={{ textAlign: "right", fontSize: 12 }}>{(m.tokens / 1e6).toFixed(2)}M</td>
                    <td className="mono tabular" style={{ textAlign: "right", fontSize: 13 }}>{m.cost.toFixed(2)}€</td>
                    <td>
                      <div className="row gap-3">
                        <div style={{ flex: 1 }}><Bar pct={m.share} status="ok"/></div>
                        <span className="mono" style={{ fontSize: 10, minWidth: 28, textAlign: "right" }}>{m.share}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>

          <Panel title={<span><Icon name="grid" size={12}/> &nbsp;Por tipo</span>}>
            <div className="col gap-4">
              {TOKEN_DATA.byKind.map((k) => (
                <div key={k.kind}>
                  <div className="row" style={{ justifyContent: "space-between", marginBottom: 4 }}>
                    <span className="display" style={{ fontSize: 11, letterSpacing: "0.06em", color: "var(--text-dim)" }}>{k.kind}</span>
                    <span className="mono" style={{ fontSize: 11, color: "var(--y)" }}>{k.pct}%</span>
                  </div>
                  <Bar pct={k.pct}/>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      )}

      {tab === "saldo" && (
        <div className="grid gap-8" style={{ gridTemplateColumns: "1.2fr 1fr" }}>
          <Panel title={<span><Icon name="coin" size={12}/> &nbsp;Saldos por proveedor</span>} noPad>
            <table className="tbl">
              <thead>
                <tr>
                  <th>Proveedor</th>
                  <th style={{ width: 100, textAlign: "right" }}>Recargado</th>
                  <th style={{ width: 100, textAlign: "right" }}>Gastado</th>
                  <th style={{ width: 100, textAlign: "right" }}>Saldo</th>
                  <th style={{ width: 80,  textAlign: "right" }}>Llamadas</th>
                </tr>
              </thead>
              <tbody>
                {PROVIDER_BALANCE.map((p) => {
                  const bal = p.topped - p.spent;
                  const low = bal < 20;
                  return (
                    <tr key={p.id}>
                      <td className="display" style={{ fontSize: 12 }}>{p.id}</td>
                      <td className="mono tabular" style={{ textAlign: "right" }}>{p.topped.toFixed(2)}€</td>
                      <td className="mono tabular" style={{ textAlign: "right", color: "var(--text-dim)" }}>{p.spent.toFixed(2)}€</td>
                      <td className="mono tabular" style={{ textAlign: "right", color: low ? "var(--warn)" : "var(--ok)", fontSize: 14 }}>
                        {bal.toFixed(2)}€
                      </td>
                      <td className="mono tabular dim" style={{ textAlign: "right" }}>{p.calls}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Panel>

          <Panel title={<span><Icon name="key" size={12}/> &nbsp;Histórico recargas</span>} meta={`${TOPUPS.length} en total`} noPad>
            <div className="col gap-2" style={{ padding: 12, maxHeight: 320, overflow: "auto" }}>
              {TOPUPS.map((t, i) => (
                <div key={i} className="row" style={{
                  padding: "6px 10px", border: "1px solid var(--border)", background: "var(--panel-2)",
                  fontFamily: "var(--f-mono)", fontSize: 11,
                }}>
                  <span style={{ color: "var(--text-mute)", width: 110 }}>{t.t}</span>
                  <span style={{ flex: 1, color: "var(--y)" }}>{t.provider}</span>
                  <span style={{ color: "var(--ok)" }}>+{t.amount.toFixed(2)}€</span>
                </div>
              ))}
            </div>
            <div style={{ padding: 12, borderTop: "1px solid var(--border)", background: "var(--panel-2)" }}>
              <Btn sm kind="primary" icon={<Icon name="key" size={10}/>}
                   onClick={async () => {
                     const provider = window.prompt("Proveedor (anthropic / openai / elevenlabs / kling):");
                     if (!provider) return;
                     const amount = parseFloat(window.prompt("Importe USD:") || "0");
                     if (!amount || amount <= 0) return;
                     const note = window.prompt("Nota (opcional):") || "";
                     const res = await fetch("/api/economics/topup", {
                       method: "POST",
                       headers: { "Content-Type": "application/json" },
                       body: JSON.stringify({ provider, amount, note }),
                     });
                     const data = await res.json();
                     if (data.ok) window.location.reload();
                     else window.alert("Error: " + (data.error || "desconocido"));
                   }}>
                Registrar recarga
              </Btn>
            </div>
          </Panel>
        </div>
      )}

      {tab === "eventos" && (
        <Panel title={<span><Icon name="log" size={12}/> &nbsp;Últimos eventos</span>} meta="ai_usage.jsonl" noPad>
          <table className="tbl">
            <thead>
              <tr>
                <th style={{ width: 90 }}>T</th>
                <th>Modelo</th>
                <th>Tipo</th>
                <th style={{ width: 100, textAlign: "right" }}>Tokens</th>
                <th style={{ width: 90,  textAlign: "right" }}>Coste</th>
              </tr>
            </thead>
            <tbody>
              {AI_LOG.map((e, i) => (
                <tr key={i}>
                  <td className="mono dim" style={{ fontSize: 11 }}>{e.t}</td>
                  <td className="mono" style={{ color: "var(--y)" }}>{e.model}</td>
                  <td>{e.kind}</td>
                  <td className="mono tabular" style={{ textAlign: "right" }}>{e.tok.toLocaleString()}</td>
                  <td className="mono tabular" style={{ textAlign: "right", color: "var(--ok)" }}>{e.cost.toFixed(3)}€</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · AJUSTES (API Keys + sandbox)
// ════════════════════════════════════════════════════════════
function PageAjustes({ onNav, onOpenAI }) {
  const [checking, setChecking] = React.useState(false);
  const [keys, setKeys] = React.useState(CONNECTORS.service);

  const recheck = async () => {
    setChecking(true);
    // Llama a /api/api-key/ping para cada proveedor y actualiza el estado
    const updated = await Promise.all(CONNECTORS.service.map(async (k) => {
      const t0 = performance.now();
      try {
        const res = await fetch("/api/api-key/ping", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ provider: (k.id || k.label || "").toLowerCase() }),
        });
        const data = await res.json();
        const latency = Math.round(performance.now() - t0);
        return { ...k, latency, status: data.ok ? "ok" : "warn",
                 detail: data.ok ? `${data.found.length}/${data.expected.length} keys` : (data.error || k.detail) };
      } catch {
        return { ...k, status: "alert", detail: "sin conexión con backend" };
      }
    }));
    setKeys(updated);
    setChecking(false);
  };

  return (
    <div className="content">
      <PageHeader
        title="Ajustes"
        sub="API keys · sandbox · preferencias del cockpit"
        actions={
          <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Ajustes · API keys", purpose: "improve" })}
               icon={<Icon name="spark" size={11}/>}>Mejorar con IA</Btn>
        }
      />
      <SourcePills files={srcFor("ajustes")}/>

      <div className="h2">
        <Icon name="key" size={14}/> API keys de proveedores
        <Btn sm kind="ghost" onClick={recheck} icon={<Icon name="refresh" size={11}/>}>
          {checking ? "Verificando…" : "Re-verificar (ignora caché 5min)"}
        </Btn>
      </div>

      <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}>
        {keys.map((k) => {
          const badge = k.status === "ok" ? "🟢 OK" : k.status === "warn" ? "🟡 AVISO" : "🔴 ERROR";
          return (
            <div key={k.id} className="panel" style={{ padding: "14px 16px" }}>
              <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
                <div className="display" style={{ fontSize: 14, letterSpacing: "0.04em" }}>{k.label}</div>
                <StatusDot status={k.status}/>
              </div>
              <div className="mono dim" style={{ fontSize: 10, marginBottom: 8 }}>{badge}</div>
              <div className="row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
                <span className="badge">{k.env}</span>
                <span className="mono" style={{ fontSize: 10, color: "var(--text-mute)" }}>
                  {checking ? "…" : `${k.latency}ms`}
                </span>
              </div>
              <div className="mono" style={{ fontSize: 10, color: "var(--text-dim)", lineHeight: 1.4, minHeight: 28 }}>
                {k.detail}
              </div>
              <div className="row gap-3 mt-8">
                <Btn sm kind="ghost" style={{ flex: 1 }}
                     onClick={() => window.alert(`Rota la API key de ${k.label} editando .env y reinicia el servidor.`)}>
                  <Icon name="settings" size={10}/> Rotar
                </Btn>
                <Btn sm kind="ghost" style={{ flex: 1 }}
                     onClick={async () => {
                       const res = await fetch("/api/api-key/ping", {
                         method: "POST",
                         headers: { "Content-Type": "application/json" },
                         body: JSON.stringify({ provider: (k.id || k.label || "").toLowerCase() }),
                       });
                       const data = await res.json();
                       window.alert(data.ok
                         ? `OK · ${data.found.length}/${data.expected.length} keys presentes`
                         : `Faltan: ${(data.expected || []).filter(n => !(data.found || []).some(f => f.name === n)).join(", ") || data.error}`);
                     }}>
                  <Icon name="check" size={10}/> Ping
                </Btn>
              </div>
            </div>
          );
        })}
      </div>

      <div className="h2"><Icon name="settings" size={14}/> Sandbox · ejecución</div>

      <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <Panel title={<span><Icon name="folder" size={12}/> &nbsp;Whitelist de rutas</span>}>
          <div className="mono dim mb-8" style={{ fontSize: 11 }}>
            Rutas dentro del repo donde el cockpit puede escribir. Cualquier otra es solo-lectura.
          </div>
          <div className="col gap-2">
            {[
              "cockpit/components_map.json",
              "logs/",
              "Guiones/",
              "escaletas/",
              "episodios/",
              "videopodcast/",
            ].map((p) => (
              <div key={p} className="row" style={{
                padding: "6px 10px", background: "var(--panel-2)", border: "1px solid var(--border)",
                borderLeft: "2px solid var(--ok)",
              }}>
                <Icon name="check" size={11}/>
                <span className="mono" style={{ fontSize: 12, color: "var(--y)" }}>{p}</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title={<span><Icon name="settings" size={12}/> &nbsp;Preferencias</span>}>
          <div className="col gap-6">
            {[
              { label: "Modelo por defecto",    v: "claude-haiku-4.5",  hint: "Usado en validaciones y Mejorar con IA" },
              { label: "Timeout pipeline",       v: "30 min",            hint: "Antes de cancelar un proceso colgado" },
              { label: "Auto-refresh logs",      v: "5 s",               hint: "Cuando 'Auto' está activado" },
              { label: "Budget mensual",         v: "250.00 €",          hint: "Avisa al 80%" },
              { label: "Caché de prompts",       v: "ON",                hint: "Anthropic prompt-caching" },
            ].map((p) => (
              <div key={p.label} className="row" style={{
                justifyContent: "space-between", padding: "8px 0",
                borderBottom: "1px dashed var(--border)",
              }}>
                <div className="col" style={{ gap: 2 }}>
                  <span className="display" style={{ fontSize: 11, letterSpacing: "0.06em" }}>{p.label}</span>
                  <span className="mono dim" style={{ fontSize: 10 }}>{p.hint}</span>
                </div>
                <span className="mono" style={{ fontSize: 12, color: "var(--y)" }}>{p.v}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="h2"><Icon name="dot" size={14}/> Acerca de</div>
      <Panel>
        <div className="grid gap-8" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
          {[
            { lbl: "Versión",      v: "v0.9.0"     },
            { lbl: "Branch",       v: "master"     },
            { lbl: "Commit",       v: "30bfb39"    },
            { lbl: "Tests",        v: "163 ✓"      },
            { lbl: "Python",       v: "3.11.6"     },
            { lbl: "Streamlit",    v: "1.36.0"     },
          ].map((a) => (
            <div key={a.lbl}>
              <div className="display" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.16em" }}>{a.lbl}</div>
              <div className="mono" style={{ fontSize: 14, color: "var(--y)", marginTop: 4 }}>{a.v}</div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PAGE · MÉTRICAS DE DIFUSIÓN (Spotify · iVoox · LinkedIn)
// ════════════════════════════════════════════════════════════

// 30 días de datos sintéticos por plataforma
const _trend = (base, drift, jitter) =>
  Array.from({ length: 30 }, (_, i) =>
    Math.max(0, Math.round(base + i * drift + (Math.sin(i * 0.7) * jitter * 0.5) + (Math.random() - 0.5) * jitter))
  );

const METRICS = {
  spotify: {
    label: "Spotify",
    color: "#1DB954",
    logo: "♫",
    followers: 1842,
    followers_delta: "+124 (30d)",
    plays_30d: 14_280,
    listeners_30d: 6_420,
    completion_rate: 68,
    avg_listen: "18:42",
    countries: [
      { c: "España",      pct: 64 },
      { c: "México",      pct: 12 },
      { c: "Argentina",   pct:  8 },
      { c: "Colombia",    pct:  6 },
      { c: "Chile",       pct:  4 },
      { c: "Otros",       pct:  6 },
    ],
    trend: _trend(380, 6, 120),
    auth: { type: "OAuth 2.0", expires: "2026-08-12", scopes: ["podcast-read","metrics-read"] },
  },
  ivoox: {
    label: "iVoox",
    color: "#E5005B",
    logo: "▶",
    followers: 928,
    followers_delta: "+42 (30d)",
    plays_30d: 8_140,
    downloads_30d: 3_280,
    completion_rate: 71,
    avg_listen: "21:18",
    countries: [
      { c: "España",      pct: 88 },
      { c: "Argentina",   pct:  4 },
      { c: "México",      pct:  4 },
      { c: "Otros",       pct:  4 },
    ],
    trend: _trend(220, 4, 80),
    auth: { type: "API key + RSS", expires: "—", scopes: ["read"] },
  },
  linkedin: {
    label: "LinkedIn",
    color: "#0A66C2",
    logo: "in",
    followers: 3_640,
    followers_delta: "+286 (30d)",
    impressions_30d: 48_220,
    engagement_30d: 4_180,
    engagement_rate: 8.7,
    avg_listen: "—",
    countries: [
      { c: "España",      pct: 58 },
      { c: "México",      pct: 14 },
      { c: "USA",         pct:  9 },
      { c: "UK",          pct:  6 },
      { c: "Argentina",   pct:  5 },
      { c: "Otros",       pct:  8 },
    ],
    trend: _trend(1500, 18, 320),
    auth: { type: "OAuth 2.0", expires: "2026-05-23", scopes: ["r_organization_social","r_member_social"], warn: "expira en 11 días" },
  },
};

// Top episodios cross-platform
const TOP_EPISODES = [
  { id: "M3",    title: "Transformers",             spotify: 2840, ivoox: 1820, linkedin: 12420 },
  { id: "M2",    title: "Redes neuronales",         spotify: 2410, ivoox: 1580, linkedin:  9840 },
  { id: "M1",    title: "Datos y ML clásico",       spotify: 2180, ivoox: 1420, linkedin:  8120 },
  { id: "M0",    title: "Cimientos",                spotify: 1980, ivoox: 1320, linkedin:  7640 },
  { id: "M4",    title: "LLMs y emergencia",        spotify: 1420, ivoox:  980, linkedin:  6280 },
  { id: "M3_T1", title: "T1 · Mecanismo de atención", spotify: 1180, ivoox:  840, linkedin: 4180 },
  { id: "M6",    title: "Prompting avanzado",       spotify:  920, ivoox:  640, linkedin:  3420 },
];

// Sparkline component
function Spark({ values, color, height = 40, fill }) {
  const max = Math.max(...values);
  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * 100;
    const y = 100 - (v / max) * 92 - 4;
    return [x, y];
  });
  const path = "M " + pts.map(p => p.join(" ")).join(" L ");
  const areaPath = path + ` L 100 100 L 0 100 Z`;
  return (
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: "100%", height, display: "block" }}>
      {fill && <path d={areaPath} fill={color} fillOpacity={0.15}/>}
      <path d={path} fill="none" stroke={color} strokeWidth={1.4} vectorEffect="non-scaling-stroke"/>
      {pts.map(([x, y], i) => i === pts.length - 1 ? <circle key={i} cx={x} cy={y} r={1.6} fill={color}/> : null)}
    </svg>
  );
}

function PageMetricas({ onNav, onOpenAI }) {
  const [tab, setTab] = React.useState("global"); // global | spotify | ivoox | linkedin
  const [refreshing, setRefreshing] = React.useState(false);
  const [lastSync, setLastSync] = React.useState("hoy 12:38");

  const totalListeners = METRICS.spotify.listeners_30d + METRICS.ivoox.plays_30d;
  const totalPlays     = METRICS.spotify.plays_30d + METRICS.ivoox.plays_30d;
  const totalImpr      = METRICS.linkedin.impressions_30d;
  const totalFollowers = METRICS.spotify.followers + METRICS.ivoox.followers + METRICS.linkedin.followers;

  const refresh = () => {
    setRefreshing(true);
    setTimeout(() => {
      setRefreshing(false);
      const now = new Date();
      setLastSync(`hoy ${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`);
    }, 1100);
  };

  return (
    <div className="content">
      <PageHeader
        title="Métricas de difusión"
        sub="Spotify · iVoox · LinkedIn · oyentes, descargas, engagement"
        actions={
          <React.Fragment>
            <span className="mono dim" style={{ fontSize: 11, letterSpacing: "0.08em" }}>
              sync: {lastSync}
            </span>
            <Btn sm kind="ghost" onClick={refresh} icon={<Icon name="refresh" size={11}/>}>
              {refreshing ? "Sincronizando…" : "Sincronizar ahora"}
            </Btn>
            <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Métricas de difusión", purpose: "improve" })}
                 icon={<Icon name="spark" size={11}/>}>Analizar con IA</Btn>
          </React.Fragment>
        }
      />
      <SourcePills files={srcFor("metricas")}/>

      {/* KPIs cross-platform */}
      <div className="kpi-grid mb-12">
        <Kpi label="Reproducciones · 30d"
             value={(totalPlays / 1000).toFixed(1)} unit="K"
             delta="+18% vs mes anterior" deltaDir="up"/>
        <Kpi label="Oyentes únicos · 30d"
             value={(totalListeners / 1000).toFixed(1)} unit="K"
             delta="Spotify + iVoox"/>
        <Kpi label="Impresiones LinkedIn · 30d"
             value={(totalImpr / 1000).toFixed(1)} unit="K"
             delta={`${METRICS.linkedin.engagement_rate}% engagement`} deltaDir="up"/>
        <Kpi label="Seguidores totales"
             value={totalFollowers.toLocaleString("es-ES")}
             delta="+452 (30d)" deltaDir="up"/>
      </div>

      {/* Platform tabs */}
      <div className="tabs mb-12">
        {[
          { id: "global",   label: "Global"    },
          { id: "spotify",  label: "Spotify"   },
          { id: "ivoox",    label: "iVoox"     },
          { id: "linkedin", label: "LinkedIn"  },
        ].map((t) => (
          <div key={t.id} className={`tab ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
            {t.label}
            {t.id !== "global" && <StatusDot status={METRICS[t.id].auth.warn ? "warn" : "ok"} sm/>}
          </div>
        ))}
      </div>

      {tab === "global" && (
        <React.Fragment>
          {/* Platform cards with sparklines */}
          <div className="grid gap-8 mb-12" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
            {["spotify", "ivoox", "linkedin"].map((id) => {
              const m = METRICS[id];
              const primary = id === "linkedin"
                ? { lbl: "Impresiones · 30d", v: m.impressions_30d.toLocaleString("es-ES") }
                : { lbl: "Reproducciones · 30d", v: m.plays_30d.toLocaleString("es-ES") };
              const secondary = id === "spotify"  ? { lbl: "Oyentes", v: m.listeners_30d.toLocaleString("es-ES") }
                              : id === "ivoox"    ? { lbl: "Descargas", v: m.downloads_30d.toLocaleString("es-ES") }
                              : { lbl: "Engagement", v: m.engagement_30d.toLocaleString("es-ES") };

              return (
                <div key={id} className="panel"
                     onClick={() => setTab(id)}
                     style={{ padding: 0, cursor: "pointer", borderLeft: `3px solid ${m.color}` }}>
                  <div style={{ padding: "14px 18px", borderBottom: "1px solid var(--border)" }}>
                    <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
                      <div className="row gap-4">
                        <div style={{
                          width: 28, height: 28, background: m.color, color: "#fff",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontFamily: "var(--f-display)", fontSize: 14, fontWeight: 700, borderRadius: 4,
                        }}>{m.logo}</div>
                        <div className="display" style={{ fontSize: 14, letterSpacing: "0.04em" }}>{m.label}</div>
                      </div>
                      <StatusDot status={m.auth.warn ? "warn" : "ok"}/>
                    </div>
                    <div className="mono dim" style={{ fontSize: 10, letterSpacing: "0.06em" }}>
                      {m.followers.toLocaleString("es-ES")} seguidores · {m.followers_delta}
                    </div>
                  </div>
                  <div style={{ padding: "14px 18px" }}>
                    <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
                      <div>
                        <div className="display" style={{ fontSize: 9, color: "var(--text-mute)", letterSpacing: "0.16em" }}>{primary.lbl}</div>
                        <div className="mono" style={{ fontSize: 24, color: m.color, marginTop: 2 }}>{primary.v}</div>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <div className="display" style={{ fontSize: 9, color: "var(--text-mute)", letterSpacing: "0.16em" }}>{secondary.lbl}</div>
                        <div className="mono" style={{ fontSize: 14, color: "var(--text)", marginTop: 4 }}>{secondary.v}</div>
                      </div>
                    </div>
                    <div style={{ marginTop: 10 }}>
                      <Spark values={m.trend} color={m.color} height={48} fill/>
                    </div>
                    <div className="row mono" style={{ fontSize: 9, color: "var(--text-mute)", justifyContent: "space-between", marginTop: 4 }}>
                      <span>-30d</span><span>hoy</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Top episodios cross-platform */}
          <Panel
            title={<span><Icon name="episode" size={12}/> &nbsp;Top episodios · multi-plataforma</span>}
            meta="ranking por reproducciones agregadas"
            noPad
          >
            <table className="tbl">
              <thead>
                <tr>
                  <th style={{ width: 60 }}>#</th>
                  <th style={{ width: 80 }}>ID</th>
                  <th>Título</th>
                  <th style={{ width: 90,  textAlign: "right" }}>Spotify</th>
                  <th style={{ width: 90,  textAlign: "right" }}>iVoox</th>
                  <th style={{ width: 110, textAlign: "right" }}>LinkedIn</th>
                  <th style={{ width: 140 }}>Cuota Spotify</th>
                </tr>
              </thead>
              <tbody>
                {TOP_EPISODES.map((e, i) => {
                  const total = e.spotify + e.ivoox;
                  const pct = Math.round((e.spotify / total) * 100);
                  return (
                    <tr key={e.id} className="clickable" onClick={() => onNav("episodio", e.id)}>
                      <td className="mono dim" style={{ fontSize: 11 }}>{String(i + 1).padStart(2, "0")}</td>
                      <td className="mono" style={{ color: "var(--y)" }}>{e.id}</td>
                      <td style={{ fontSize: 13 }}>{e.title}</td>
                      <td className="mono tabular" style={{ textAlign: "right", color: METRICS.spotify.color }}>
                        {e.spotify.toLocaleString("es-ES")}
                      </td>
                      <td className="mono tabular" style={{ textAlign: "right", color: METRICS.ivoox.color }}>
                        {e.ivoox.toLocaleString("es-ES")}
                      </td>
                      <td className="mono tabular" style={{ textAlign: "right", color: METRICS.linkedin.color }}>
                        {e.linkedin.toLocaleString("es-ES")}
                      </td>
                      <td>
                        <div className="row gap-3">
                          <div style={{ flex: 1, height: 4, background: "var(--panel-3)", display: "flex", overflow: "hidden" }}>
                            <div style={{ width: `${pct}%`,        height: "100%", background: METRICS.spotify.color }}/>
                            <div style={{ width: `${100 - pct}%`,  height: "100%", background: METRICS.ivoox.color   }}/>
                          </div>
                          <span className="mono" style={{ fontSize: 10, color: "var(--text-mute)", minWidth: 36, textAlign: "right" }}>
                            {pct}/{100 - pct}
                          </span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Panel>
        </React.Fragment>
      )}

      {tab !== "global" && <PlatformDetail id={tab} m={METRICS[tab]} onNav={onNav}/>}
    </div>
  );
}

function PlatformDetail({ id, m, onNav }) {
  const isSpotify  = id === "spotify";
  const isIvoox    = id === "ivoox";
  const isLinkedin = id === "linkedin";

  return (
    <div className="col gap-8">
      {/* Header card with auth state */}
      <Panel noPad>
        <div style={{ padding: "16px 20px", borderLeft: `3px solid ${m.color}`, background: "var(--panel-2)" }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div className="row gap-4">
              <div style={{
                width: 40, height: 40, background: m.color, color: "#fff",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontFamily: "var(--f-display)", fontSize: 18, fontWeight: 700, borderRadius: 4,
              }}>{m.logo}</div>
              <div>
                <div className="display" style={{ fontSize: 18, letterSpacing: "0.04em" }}>{m.label}</div>
                <div className="mono dim" style={{ fontSize: 10, marginTop: 2, letterSpacing: "0.08em" }}>
                  {m.auth.type} · token expira {m.auth.expires}
                </div>
              </div>
            </div>
            <div className="row gap-3">
              <span className={`badge ${m.auth.warn ? "warn" : "ok"}`}>
                {m.auth.warn || "OPERATIVO"}
              </span>
              <Btn sm kind="ghost" icon={<Icon name="refresh" size={10}/>}
                   onClick={() => window.alert(`Para refrescar el token de ${m.label}, regenera la API key en su panel y actualízala en .env.`)}>
                Refrescar token
              </Btn>
            </div>
          </div>
        </div>
      </Panel>

      {/* KPIs */}
      <div className="kpi-grid">
        <Kpi label="Seguidores"
             value={m.followers.toLocaleString("es-ES")} delta={m.followers_delta} deltaDir="up"/>
        {isLinkedin ? (
          <React.Fragment>
            <Kpi label="Impresiones · 30d" value={m.impressions_30d.toLocaleString("es-ES")}/>
            <Kpi label="Engagements · 30d" value={m.engagement_30d.toLocaleString("es-ES")} delta={`${m.engagement_rate}% tasa`} deltaDir="up"/>
          </React.Fragment>
        ) : (
          <React.Fragment>
            <Kpi label="Reproducciones · 30d" value={m.plays_30d.toLocaleString("es-ES")}/>
            {isSpotify && <Kpi label="Oyentes únicos · 30d" value={m.listeners_30d.toLocaleString("es-ES")} delta={`${Math.round((m.listeners_30d / m.plays_30d) * 100)}% conversión`}/>}
            {isIvoox   && <Kpi label="Descargas · 30d" value={m.downloads_30d.toLocaleString("es-ES")}/>}
          </React.Fragment>
        )}
        <Kpi label={isLinkedin ? "Tasa engagement" : "Tasa de finalización"}
             value={isLinkedin ? m.engagement_rate : m.completion_rate} unit="%"
             delta={!isLinkedin ? `escucha media ${m.avg_listen}` : "vs 4.1% benchmark"}
             deltaDir="up"/>
      </div>

      <div className="grid gap-8" style={{ gridTemplateColumns: "1.4fr 1fr" }}>
        {/* Trend chart (bars) */}
        <Panel title={<span><Icon name="brain" size={12}/> &nbsp;Tendencia · últimos 30 días</span>} meta={isLinkedin ? "impresiones/día" : "reproducciones/día"}>
          <div style={{ position: "relative", height: 180, display: "flex", alignItems: "flex-end", gap: 2 }}>
            {m.trend.map((v, i) => {
              const max = Math.max(...m.trend);
              const h = (v / max) * 100;
              return (
                <div key={i} style={{ flex: 1, height: `${h}%`, background: m.color, opacity: 0.7, position: "relative" }}
                     title={`día ${i + 1}: ${v.toLocaleString("es-ES")}`}>
                </div>
              );
            })}
          </div>
          <div className="row mono mt-4" style={{ fontSize: 10, color: "var(--text-mute)", justifyContent: "space-between", letterSpacing: "0.08em" }}>
            <span>-30 días</span>
            <span>media: {Math.round(m.trend.reduce((s, v) => s + v, 0) / m.trend.length).toLocaleString("es-ES")}/día</span>
            <span>hoy</span>
          </div>
        </Panel>

        {/* Geo distribution */}
        <Panel title={<span><Icon name="map" size={12}/> &nbsp;Por país</span>}>
          <div className="col gap-4">
            {m.countries.map((c) => (
              <div key={c.c}>
                <div className="row" style={{ justifyContent: "space-between", marginBottom: 3 }}>
                  <span className="display" style={{ fontSize: 11, letterSpacing: "0.06em", color: "var(--text-dim)" }}>{c.c}</span>
                  <span className="mono" style={{ fontSize: 11, color: m.color }}>{c.pct}%</span>
                </div>
                <div style={{ height: 4, background: "var(--panel-3)" }}>
                  <div style={{ width: `${c.pct}%`, height: "100%", background: m.color }}/>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      {/* Top episodes for this platform */}
      <Panel
        title={<span><Icon name="episode" size={12}/> &nbsp;Top episodios en {m.label}</span>}
        meta={`${TOP_EPISODES.length} episodios`}
        noPad
      >
        <table className="tbl">
          <thead>
            <tr>
              <th style={{ width: 60 }}>#</th>
              <th style={{ width: 100 }}>ID</th>
              <th>Título</th>
              <th style={{ width: 140, textAlign: "right" }}>{isLinkedin ? "Impresiones" : "Reproducciones"}</th>
              <th style={{ width: 180 }}>Cuota</th>
            </tr>
          </thead>
          <tbody>
            {(() => {
              const sorted = [...TOP_EPISODES].sort((a, b) => (b[id] || 0) - (a[id] || 0));
              const max = sorted[0][id];
              return sorted.map((e, i) => (
                <tr key={e.id} className="clickable" onClick={() => onNav("episodio", e.id)}>
                  <td className="mono dim" style={{ fontSize: 11 }}>{String(i + 1).padStart(2, "0")}</td>
                  <td className="mono" style={{ color: "var(--y)" }}>{e.id}</td>
                  <td style={{ fontSize: 13 }}>{e.title}</td>
                  <td className="mono tabular" style={{ textAlign: "right", color: m.color, fontSize: 13 }}>
                    {(e[id] || 0).toLocaleString("es-ES")}
                  </td>
                  <td>
                    <div style={{ height: 4, background: "var(--panel-3)" }}>
                      <div style={{ width: `${(e[id] / max) * 100}%`, height: "100%", background: m.color }}/>
                    </div>
                  </td>
                </tr>
              ));
            })()}
          </tbody>
        </table>
      </Panel>

      {/* Auth detail */}
      <Panel title={<span><Icon name="key" size={12}/> &nbsp;Autenticación</span>}>
        <div className="grid gap-6" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
          <div>
            <div className="display" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.14em" }}>TIPO</div>
            <div className="mono" style={{ fontSize: 13, color: "var(--y)", marginTop: 4 }}>{m.auth.type}</div>
          </div>
          <div>
            <div className="display" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.14em" }}>EXPIRA</div>
            <div className="mono" style={{ fontSize: 13, color: m.auth.warn ? "var(--warn)" : "var(--text)", marginTop: 4 }}>
              {m.auth.expires}
            </div>
          </div>
          <div>
            <div className="display" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.14em" }}>SCOPES</div>
            <div className="row gap-2" style={{ marginTop: 4, flexWrap: "wrap" }}>
              {m.auth.scopes.map(s => <span key={s} className="badge mono" style={{ fontSize: 9 }}>{s}</span>)}
            </div>
          </div>
        </div>
      </Panel>
    </div>
  );
}

Object.assign(window, {
  PageMapa, PageConectores, PageLanzador, PageFuentes, PagePlayer,
  PageLogs, PageOptimizar, PageConsumo, PageAjustes, PageMetricas,
});


// ============================ app.jsx ============================

// app.jsx — Main app, routing, tweaks panel

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "yellowIntensity": 35,
  "font": "Oswald + Barlow",
  "mode": "industrial",
  "density": "regular",
  "masterView": "lista"
}/*EDITMODE-END*/;

// Parsea el hash de routing: "#modulo/M3" → { base: "modulo", payload: "M3" }
function parseHash() {
  const h = window.location.hash.replace("#", "");
  const [base, payload] = h.split("/");
  return { base, payload: payload ? decodeURIComponent(payload) : null };
}

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [page, setPage] = React.useState(() => {
    const { base } = parseHash();
    return WIRED.has(base) ? base : "home";
  });
  // Selección activa: qué módulo / episodio se está viendo. Inicializada
  // desde el hash para sobrevivir a un reload.
  const [sel, setSel] = React.useState(() => {
    const { base, payload } = parseHash();
    return {
      modulo:   base === "modulo"   ? payload : null,
      episodio: base === "episodio" ? payload : null,
    };
  });
  const [aiDrawer, setAIDrawer] = React.useState({ open: false, mode: "improve", context: null });

  // expose master view setter so the segmented control can update tweak
  React.useEffect(() => {
    window.__setMasterView = (v) => setTweak("masterView", v);
  }, [setTweak]);

  // Apply theme tweaks via inline style overrides on root
  React.useEffect(() => {
    const root = document.documentElement;
    // yellow intensity drives accent dominance
    const intensity = t.yellowIntensity / 35; // 1.0 baseline
    // Slightly tone-shift yellow soft / strength
    root.style.setProperty("--y-soft", `rgba(245, 196, 0, ${Math.min(0.05 + (t.yellowIntensity / 100) * 0.25, 0.32)})`);
    root.style.setProperty("--y-soft-2", `rgba(245, 196, 0, ${Math.min(0.02 + (t.yellowIntensity / 100) * 0.12, 0.16)})`);

    // Font swap
    if (t.font === "Oswald + Barlow") {
      root.style.setProperty("--f-display", '"Oswald", "Helvetica Neue", sans-serif');
      root.style.setProperty("--f-body",    '"Barlow Condensed", "Helvetica Neue", sans-serif');
    } else if (t.font === "Bebas + Inter") {
      root.style.setProperty("--f-display", '"Bebas Neue", "Helvetica Neue", sans-serif');
      root.style.setProperty("--f-body",    '"Inter", "Helvetica Neue", sans-serif');
    } else if (t.font === "Helvetica") {
      root.style.setProperty("--f-display", '"Helvetica Neue", "Helvetica", sans-serif');
      root.style.setProperty("--f-body",    '"Helvetica Neue", "Helvetica", sans-serif');
    }

    root.setAttribute("data-mode", t.mode);
    root.setAttribute("data-density", t.density);
  }, [t]);

  // nav(id) navega de página; nav("modulo", "M3") / nav("episodio", "M3_T2")
  // además fija qué módulo/episodio mostrar. Al abrir un episodio se deriva
  // también su módulo padre ("M3_T2" → "M3").
  const nav = (id, payload) => {
    if (!WIRED.has(id)) return;
    setPage(id);
    if (id === "modulo") {
      setSel((s) => ({ ...s, modulo: payload || s.modulo }));
    } else if (id === "episodio") {
      setSel((s) => ({
        ...s,
        episodio: payload || s.episodio,
        modulo: payload ? payload.split("_")[0] : s.modulo,
      }));
    }
    const hasSel = payload && (id === "modulo" || id === "episodio");
    window.location.hash = hasSel ? `${id}/${encodeURIComponent(payload)}` : id;
    window.scrollTo(0, 0);
  };

  const openAI  = (ctx) => setAIDrawer({ open: true, mode: "improve", context: ctx });
  const openFix = (ctx) => setAIDrawer({ open: true, mode: "fix",     context: ctx });
  const closeAI = ()    => setAIDrawer((s) => ({ ...s, open: false }));

  // Crumbs by page — modulo/episodio reflejan la selección activa
  const CRUMBS = {
    home:       [{ label: "Inicio" }],
    master:     [{ label: "Inicio", id: "home" }, { label: "Master" }],
    modulo:     [{ label: "Inicio", id: "home" }, { label: "Master", id: "master" }, { label: sel.modulo || "módulo" }],
    episodio:   [{ label: "Inicio", id: "home" }, { label: "Master", id: "master" }, { label: sel.modulo || "M3", id: "modulo" }, { label: sel.episodio || "episodio" }],
    pizarra:    [{ label: "Inicio", id: "home" }, { label: "Pizarra" }],
    mapa:       [{ label: "Inicio", id: "home" }, { label: "Mapa" }],
    conectores: [{ label: "Inicio", id: "home" }, { label: "Conectores" }],
    lanzador:   [{ label: "Inicio", id: "home" }, { label: "Conectores", id: "conectores" }, { label: "Lanzador" }],
    fuentes:    [{ label: "Inicio", id: "home" }, { label: "Recursos" }, { label: "Fuentes" }],
    player:     [{ label: "Inicio", id: "home" }, { label: "Recursos" }, { label: "Previsualizar" }],
    logs:       [{ label: "Inicio", id: "home" }, { label: "Observabilidad" }, { label: "Logs" }],
    optimizar:  [{ label: "Inicio", id: "home" }, { label: "Observabilidad" }, { label: "Optimizar" }],
    metricas:   [{ label: "Inicio", id: "home" }, { label: "Difusión" }, { label: "Métricas" }],
    consumo:    [{ label: "Inicio", id: "home" }, { label: "Cuenta" }, { label: "Consumo" }],
    ajustes:    [{ label: "Inicio", id: "home" }, { label: "Cuenta" }, { label: "Ajustes" }],
  };

  return (
    <div className="app" data-density={t.density}>
      <Sidebar current={page} onNav={nav}/>
      <main className="main">
        <Topbar
          crumbs={CRUMBS[page] || CRUMBS.home}
          onCrumb={nav}
          onOpenAI={() => openAI({ target: `Página · ${page}`, purpose: "improve" })}
          onOpenFix={page === "episodio" ? () => openFix({
            target: sel.episodio || "M3_T2",
            error: "ElevenLabs 502 en bloque 4 · audio truncado en 03:14",
            id: sel.episodio || "M3_T2",
          }) : null}
        />
        {t.mode === "industrial" && <HazardTape/>}

        {page === "home"       && <PageInicio     onNav={nav} onOpenAI={openAI}/>}
        {page === "master"     && <PageMaster     onNav={nav} onOpenAI={openAI} view={t.masterView} density={t.density}/>}
        {page === "modulo"     && <PageModulo     onNav={nav} onOpenAI={openAI} modId={sel.modulo}/>}
        {page === "episodio"   && <PageEpisodio   onNav={nav} onOpenAI={openAI} onOpenFix={openFix} epId={sel.episodio}/>}
        {page === "pizarra"    && <PagePizarra    onNav={nav} onOpenAI={openAI}/>}
        {page === "mapa"       && <PageMapa       onNav={nav} onOpenAI={openAI}/>}
        {page === "conectores" && <PageConectores onNav={nav} onOpenAI={openAI}/>}
        {page === "lanzador"   && <PageLanzador   onNav={nav} onOpenAI={openAI}/>}
        {page === "fuentes"    && <PageFuentes    onNav={nav} onOpenAI={openAI}/>}
        {page === "player"     && <PagePlayer     onNav={nav} onOpenAI={openAI}/>}
        {page === "logs"       && <PageLogs       onNav={nav} onOpenAI={openAI}/>}
        {page === "optimizar"  && <PageOptimizar  onNav={nav} onOpenAI={openAI}/>}
        {page === "metricas"   && <PageMetricas   onNav={nav} onOpenAI={openAI}/>}
        {page === "consumo"    && <PageConsumo    onNav={nav} onOpenAI={openAI}/>}
        {page === "ajustes"    && <PageAjustes    onNav={nav} onOpenAI={openAI}/>}
      </main>

      <AIDrawer
        open={aiDrawer.open}
        onClose={closeAI}
        mode={aiDrawer.mode}
        context={aiDrawer.context}
      />

      <TweaksPanel title="Tweaks · Maquinaria Pesada">
        <TweakSection label="Marca"/>
        <TweakSlider
          label="Intensidad amarillo"
          value={t.yellowIntensity}
          min={0} max={100} step={5}
          unit="%"
          onChange={(v) => setTweak("yellowIntensity", v)}
        />
        <TweakRadio
          label="Modo"
          value={t.mode}
          options={["industrial", "clean"]}
          onChange={(v) => setTweak("mode", v)}
        />

        <TweakSection label="Tipografía"/>
        <TweakSelect
          label="Familia"
          value={t.font}
          options={["Oswald + Barlow", "Bebas + Inter", "Helvetica"]}
          onChange={(v) => setTweak("font", v)}
        />

        <TweakSection label="Layout"/>
        <TweakRadio
          label="Densidad"
          value={t.density}
          options={["compact", "regular", "comfy"]}
          onChange={(v) => setTweak("density", v)}
        />

        {page === "master" && (
          <React.Fragment>
            <TweakSection label="Vista del Master"/>
            <TweakRadio
              label="Variante"
              value={t.masterView}
              options={["lista", "matriz", "gantt"]}
              onChange={(v) => setTweak("masterView", v)}
            />
          </React.Fragment>
        )}
      </TweaksPanel>
    </div>
  );
}

// Esperar al fetch de /api/bootstrap antes de montar (si está disponible).
// Si no hay servidor, la promesa resuelve a null y montamos con fixtures.
const __mp_mount = () =>
  createRoot(document.getElementById("root")).render(<App/>);

if (window.__BOOTSTRAP__ && typeof window.__BOOTSTRAP__.then === "function") {
  window.__BOOTSTRAP__.then(__mp_mount).catch(__mp_mount);
} else {
  __mp_mount();
}
