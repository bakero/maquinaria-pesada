// PageProduccion — entrada por defecto. Master grid + KPIs + recordatorios.
//
// Industrial sobrio · sin emojis · todo a un click.

import * as React from "react";
import { Icon } from "../components";
import { cleanEpisodeTitle, getEpisodes, getModules, getShorts } from "../data";

const SLOT_KINDS = ["pdf", "guion", "escaleta", "audio", "video"] as const;

export interface PageProduccionProps {
  onNav: (page: string, payload?: string) => void;
  onOpenPalette: () => void;
}

export function PageProduccion({ onNav, onOpenPalette }: PageProduccionProps) {
  // getModules/getEpisodes leen el estado mutable de data.ts que
  // applyBootstrap() rellena con la respuesta real de /api/bootstrap.
  // Sin servidor, devuelven los fixtures como fallback.
  const modules = getModules();
  const allEps = getEpisodes();
  const shorts = getShorts();

  // KPIs reales: progreso global, módulos terminados, episodios completos,
  // contenidos producidos, en alerta, sin empezar.
  let totalSlots = 0;
  let doneSlots  = 0;
  let warnSlots  = 0;
  let alertSlots = 0;
  for (const e of allEps) {
    for (const k of SLOT_KINDS) {
      totalSlots++;
      if (e.state[k] === "ok") doneSlots++;
      else if (e.state[k] === "warn") warnSlots++;
      else if (e.state[k] === "alert") alertSlots++;
    }
  }
  const globalPct = Math.round((doneSlots / totalSlots) * 100);
  const modsListos  = modules.filter((m) => m.status === "ok").length;
  const modsEnCurso = modules.filter((m) => m.status === "warn").length;
  const modsAlerta  = modules.filter((m) => m.status === "alert").length;
  const epsTotal = allEps.length;
  const epsTotalCompletos = allEps.filter((e) =>
    SLOT_KINDS.every((k) => e.state[k] === "ok"),
  ).length;

  // Module → per-module aggregated progress (M + sus T)
  function moduleProgress(modId: string) {
    const eps = allEps.filter((e) => e.mod === modId);
    let t = 0, d = 0, w = 0, a = 0;
    for (const e of eps) for (const k of SLOT_KINDS) {
      t++;
      if (e.state[k] === "ok") d++;
      else if (e.state[k] === "warn") w++;
      else if (e.state[k] === "alert") a++;
    }
    return {
      done: d, warn: w, alert: a, total: t,
      pct: Math.round((d / Math.max(t, 1)) * 100),
      childrenStates: eps.map((e) => {
        const status = e.state.audio === "alert" || e.state.guion === "alert" ? "alert"
                     : e.state.audio === "warn" || e.state.guion === "warn"   ? "warn"
                     : e.state.audio === "ok"   && e.state.guion === "ok"    ? "ok"
                     : "empty";
        return { id: e.id, kind: e.kind, status };
      }),
    };
  }

  // Alertas operacionales (top 3)
  const alerts: { id: string; kind: "alert"|"warn"; head: string; body: string; nav: () => void }[] = [];
  for (const e of allEps) {
    if (alerts.length >= 4) break;
    if (e.state.audio === "alert") {
      alerts.push({
        id: e.id, kind: "alert",
        head: e.id,
        body: "audio falló — revisar logs y regenerar",
        nav: () => onNav(e.kind === "M" ? "modulo" : "tema", e.id),
      });
    }
  }
  for (const e of allEps) {
    if (alerts.length >= 4) break;
    if (e.state.guion === "alert" || e.state.guion === "warn") {
      alerts.push({
        id: e.id, kind: e.state.guion === "alert" ? "alert" : "warn",
        head: e.id,
        body: e.state.guion === "alert" ? "guion con error de validación" : "guion truncado / incompleto",
        nav: () => onNav(e.kind === "M" ? "modulo" : "tema", e.id),
      });
    }
  }

  return (
    <div className="v3-page">
      {/* KPIs */}
      <section className="v3-stats">
        <div className="v3-stat">
          <div className="v3-stat-label">Progreso global</div>
          <div className={`v3-stat-value ${globalPct >= 70 ? "ok" : globalPct >= 40 ? "warn" : "alert"}`}>
            {globalPct}%
          </div>
          <div className="v3-stat-meta">{doneSlots} / {totalSlots} contenidos</div>
        </div>
        <div className="v3-stat">
          <div className="v3-stat-label">Módulos</div>
          <div className="v3-stat-value">
            <span className="ok">{modsListos}</span>
            <span style={{ color: "var(--text-mute)" }}> / </span>
            <span>{modules.length}</span>
          </div>
          <div className="v3-stat-meta">{modsEnCurso} en curso · {modsAlerta} alerta</div>
        </div>
        <div className="v3-stat">
          <div className="v3-stat-label">Episodios completos</div>
          <div className="v3-stat-value">{epsTotalCompletos} / {epsTotal}</div>
          <div className="v3-stat-meta">{allEps.filter((e) => e.kind === "M").length} módulos · {allEps.filter((e) => e.kind === "T").length} temas</div>
        </div>
        <div className="v3-stat">
          <div className="v3-stat-label">Contenidos warn</div>
          <div className={`v3-stat-value ${warnSlots > 0 ? "warn" : ""}`}>{warnSlots}</div>
          <div className="v3-stat-meta">requieren revisión manual</div>
        </div>
        <div className="v3-stat">
          <div className="v3-stat-label">Contenidos en fallo</div>
          <div className={`v3-stat-value ${alertSlots > 0 ? "alert" : ""}`}>{alertSlots}</div>
          <div className="v3-stat-meta">re-generación necesaria</div>
        </div>
      </section>

      {/* Alertas operacionales */}
      {alerts.length > 0 && (
        <>
          <header className="v3-hd">
            <div className="v3-hd-left">
              <span className="v3-hd-eyebrow">Operación</span>
              <h2 className="v3-hd-title">Requieren atención</h2>
            </div>
            <div className="v3-hd-meta">{alerts.length} pendiente{alerts.length !== 1 ? "s" : ""}</div>
          </header>
          <div style={{ border: "1px solid var(--border-2)" }}>
            {alerts.map((a, i) => (
              <div key={i}
                   onClick={a.nav}
                   style={{
                     display: "grid",
                     gridTemplateColumns: "auto auto 1fr auto",
                     gap: 16,
                     alignItems: "center",
                     padding: "12px 16px",
                     borderTop: i > 0 ? "1px solid var(--border-2)" : "none",
                     background: "var(--bg)",
                     cursor: "pointer",
                     transition: "background var(--dur-fast) var(--ease)",
                   }}>
                <span className={`v3-pill ${a.kind}`}>
                  <span className="v3-pill-dot"/>{a.kind === "alert" ? "FALLO" : "WARN"}
                </span>
                <span style={{ fontFamily: "var(--f-mono)", fontSize: 12, color: "var(--text)", fontWeight: 600 }}>
                  {a.head}
                </span>
                <span style={{ fontSize: 13, color: "var(--text-dim)" }}>{a.body}</span>
                <Icon name="arrow" size={11}/>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Master grid */}
      <header className="v3-hd">
        <div className="v3-hd-left">
          <span className="v3-hd-eyebrow">Master</span>
          <h2 className="v3-hd-title">15 módulos · {epsTotal} episodios</h2>
        </div>
        <div className="v3-hd-right">
          <button className="v3-btn sm" onClick={onOpenPalette}>
            <Icon name="search" size={11}/>
            Buscar
            <span className="v3-kbd">⌘K</span>
          </button>
        </div>
      </header>
      <div className="v3-mods">
        {modules.map((m) => {
          const prog = moduleProgress(m.id);
          return (
            <div key={m.id} className="v3-mod" onClick={() => onNav("modulo", m.id)}>
              <div className="v3-mod-row">
                <span className="v3-mod-id">{m.id}</span>
                <span className={`v3-mod-state-dot ${m.status}`}/>
                <span className="v3-mod-meta">
                  {prog.done}/{prog.total} · {prog.pct}%
                  {prog.alert > 0 && <span style={{ color: "var(--alert)" }}> · {prog.alert}f</span>}
                  {prog.warn > 0  && <span style={{ color: "var(--warn)" }}> · {prog.warn}w</span>}
                </span>
              </div>
              <div className="v3-mod-name">{m.name}</div>
              <div style={{ fontSize: 11, color: "var(--text-mute)", fontFamily: "var(--f-mono)", marginTop: 2 }}>
                {m.short}
              </div>
              <div className="v3-mod-children">
                {prog.childrenStates.map((c, i) => (
                  <span key={i} className={`v3-mod-child ${c.status}`} title={`${c.id} · ${c.status}`}/>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Sección Shorts · píldoras de glosario, independientes de los módulos */}
      {shorts.length > 0 && (
        <>
          <header className="v3-hd" style={{ marginTop: 32 }}>
            <div className="v3-hd-left">
              <span className="v3-hd-eyebrow">Shorts</span>
              <h2 className="v3-hd-title">
                {shorts.length} píldora{shorts.length !== 1 ? "s" : ""} de glosario · 60-90 s
              </h2>
            </div>
            <div className="v3-hd-meta">
              {shorts.filter((s) =>
                SLOT_KINDS.every((k) => s.state[k] === "ok" || k === "pdf" || k === "escaleta"),
              ).length} / {shorts.length} completos
            </div>
          </header>
          <div className="v3-mods">
            {shorts.map((s) => {
              // Shorts solo tienen 3 slots aplicables: guion / audio / video
              const slots: ("guion" | "audio" | "video")[] = ["guion", "audio", "video"];
              const done = slots.filter((k) => s.state[k] === "ok").length;
              const total = slots.length;
              const pct = Math.round((done / total) * 100);
              const status: "ok" | "warn" | "empty" =
                done === total ? "ok" : done > 0 ? "warn" : "empty";
              return (
                <div key={s.id} className="v3-mod" onClick={() => onNav("short", s.id)}>
                  <div className="v3-mod-row">
                    <span className="v3-mod-id">{s.id}</span>
                    <span className={`v3-mod-state-dot ${status}`}/>
                    <span className="v3-mod-meta">{done}/{total} · {pct}%</span>
                  </div>
                  <div className="v3-mod-name">{s.term || cleanEpisodeTitle(s.title, "T")}</div>
                  <div style={{
                    fontSize: 11, color: "var(--text-mute)",
                    fontFamily: "var(--f-mono)", marginTop: 2,
                  }}>
                    píldora · sin módulo
                  </div>
                  <div className="v3-mod-children">
                    {slots.map((k) => (
                      <span key={k} className={`v3-mod-child ${
                        s.state[k] === "ok"   ? "ok"
                      : s.state[k] === "warn" ? "warn"
                      : s.state[k] === "alert"? "alert" : ""
                      }`} title={`${k} · ${s.state[k]}`}/>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
