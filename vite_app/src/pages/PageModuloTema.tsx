// PageModuloTema — página unificada para módulo (Mn) y tema (Mn_Tk).
//
// Misma estructura para ambos:
//   - Breadcrumb Master / Mn [/ Tk]
//   - ID grande + título + progreso global
//   - Rejilla lateral de hermanos/hijos (si soy módulo: padre + temas; si
//     soy tema: padre + hermanos)
//   - 5 slots (PDF, GUIÓN, ESCALETA, AUDIO, VIDEO) cada uno con su última
//     generación y expandible al visor inline.
//   - Panel live a la derecha: stream del proceso activo + última actividad.
//
// 1-click: cada slot tiene su botón Generar/Regenerar que ejecuta YA con
// parámetros pre-rellenados desde el contexto. "Generar…" lleva al
// formulario avanzado.

import * as React from "react";
import { Icon } from "../components";
import { FIXTURE_EPISODES, FIXTURE_MODULES, getLiveProc } from "../data";
import type { Episode } from "../types";

const SLOT_KINDS = ["pdf", "guion", "escaleta", "audio", "video"] as const;
type SlotKind = typeof SLOT_KINDS[number];

const SLOT_LABEL: Record<SlotKind, string> = {
  pdf:      "PDF",
  guion:    "Guion",
  escaleta: "Escaleta",
  audio:    "Audio",
  video:    "Vídeo",
};

const SLOT_PIPELINE: Record<SlotKind, string> = {
  pdf:      "—",
  guion:    "generar_guion",
  escaleta: "generar_escaleta",
  audio:    "generar_episodio_v2",
  video:    "generar_video",
};

export interface PageModuloTemaProps {
  entityId: string;            // "M3" | "M3_T1" | ...
  onNav: (page: string, payload?: string) => void;
  onOpenAI: (ctx?: unknown) => void;
  onOpenFix?: (ctx?: unknown) => void;
}

export function PageModuloTema({ entityId, onNav, onOpenAI }: PageModuloTemaProps) {
  const all = FIXTURE_EPISODES;
  // Resolve entity (module or tema). Module id matches "Mn" (no underscore).
  const ent = all.find((e) => e.id === entityId) || all.find((e) => e.id === "M3")!;
  const isModule = ent.kind === "M";
  const modId = ent.mod;
  const moduleMeta = FIXTURE_MODULES.find((m) => m.id === modId);

  // Children: si soy módulo → mis temas. Si soy tema → mis hermanos (siblings del mismo módulo).
  const moduleEpisode = all.find((e) => e.kind === "M" && e.mod === modId);
  const temas = all.filter((e) => e.kind === "T" && e.mod === modId);
  const siblings = isModule ? temas : temas; // hermanos cuando soy tema = temas del mismo módulo

  // Progreso: cuento contenidos OK del entity actual sobre 5 slots.
  function pctOf(ep: Episode): number {
    let n = 0;
    for (const k of SLOT_KINDS) {
      if (ep.state[k] === "ok") n++;
    }
    return Math.round((n / SLOT_KINDS.length) * 100);
  }

  // Para módulo: progreso = (slots completos del M + Σ slots de sus T) / total
  function modulePctTotal(): number {
    if (!isModule || !moduleEpisode) return pctOf(ent);
    const items = [moduleEpisode, ...temas];
    let total = 0, done = 0;
    for (const ep of items) {
      for (const k of SLOT_KINDS) {
        total++;
        if (ep.state[k] === "ok") done++;
      }
    }
    return Math.round((done / total) * 100);
  }

  const progressPct = isModule ? modulePctTotal() : pctOf(ent);

  // Slot expansion state
  const [expanded, setExpanded] = React.useState<SlotKind | null>(null);

  return (
    <div className="v3-page">
      {/* Header */}
      <header className="v3-mt-hd">
        <div>
          <nav className="v3-mt-crumbs">
            <a onClick={() => onNav("produccion")}>Master</a>
            <span className="sep">/</span>
            {isModule ? (
              <span className="cur">{modId}</span>
            ) : (
              <>
                <a onClick={() => onNav("modulo", modId)}>{modId}</a>
                <span className="sep">/</span>
                <span className="cur">{ent.id.split("_")[1]}</span>
              </>
            )}
          </nav>
          <div className="v3-mt-title">
            <span className="v3-mt-id">{ent.id.replace("_", " · ")}</span>
            <h1 className="v3-mt-name">{ent.title.replace(/^Episodio [A-Z0-9_]+ — /, "")}</h1>
          </div>
          <div className="v3-mt-sub">
            {isModule
              ? `${moduleMeta?.name || ""} · módulo principal · ${temas.length} tema${temas.length !== 1 ? "s" : ""} · ${ent.dur}`
              : `tema corto · ${moduleMeta?.name || modId} · ${ent.dur}`}
          </div>
        </div>
        <div className="v3-mt-progress">
          <div className="v3-mt-progress-val">{progressPct}%</div>
          <div className="v3-mt-progress-bar">
            <div className="v3-mt-progress-fill" style={{ width: `${progressPct}%` }}/>
          </div>
        </div>
      </header>

      {/* Sibling rail (módulo + sus temas) */}
      {(isModule || temas.length > 0) && (
        <div className="v3-mt-rail">
          {/* Cell of module itself */}
          {moduleEpisode && (
            <div
              className={`v3-mt-rail-cell${isModule ? " active" : ""}${!isModule ? " parent" : ""}`}
              onClick={() => onNav("modulo", modId)}
              title={moduleEpisode.title}
            >
              <span>{modId}</span>
              <span className="v3-mt-rail-cell-dot ok"/>
            </div>
          )}
          {/* Cells of temas */}
          {temas.map((t) => {
            const tnum = t.id.split("_")[1];
            const active = !isModule && t.id === ent.id;
            const slotDone = SLOT_KINDS.filter((k) => t.state[k] === "ok").length;
            const dot = slotDone === 5 ? "ok"
                      : slotDone >= 3 ? "warn"
                      : slotDone >= 1 ? "warn"
                      : "alert";
            return (
              <div
                key={t.id}
                className={`v3-mt-rail-cell${active ? " active" : ""}`}
                onClick={() => onNav("tema", t.id)}
                title={t.title}
              >
                <span>{tnum}</span>
                <span className={`v3-mt-rail-cell-dot ${dot}`}/>
              </div>
            );
          })}
        </div>
      )}

      {/* Two-column body: slots + live panel */}
      <div className="v3-mt">
        <div>
          {/* Slots */}
          {SLOT_KINDS.map((kind) => (
            <Slot
              key={kind}
              kind={kind}
              entity={ent}
              expanded={expanded === kind}
              onToggle={() => setExpanded(expanded === kind ? null : kind)}
              onGenerate={() => {
                // 1-click generation — sends params to backend.
                onNav("lanzador");
              }}
              onGenerateAdvanced={() => onNav("lanzador")}
              onOpenAI={onOpenAI}
            />
          ))}

          {/* If this is a module, show its temas grid below */}
          {isModule && temas.length > 0 && (
            <>
              <header className="v3-hd">
                <div className="v3-hd-left">
                  <span className="v3-hd-eyebrow">Sub-temas</span>
                  <h2 className="v3-hd-title">{temas.length} temas en {modId}</h2>
                </div>
                <div className="v3-hd-meta">
                  {temas.filter((t) => SLOT_KINDS.every((k) => t.state[k] === "ok")).length} / {temas.length} completos
                </div>
              </header>
              <div className="v3-mods">
                {temas.map((t) => (
                  <TemaCard key={t.id} tema={t} onClick={() => onNav("tema", t.id)} />
                ))}
              </div>
            </>
          )}
        </div>

        {/* Live stream panel */}
        <aside>
          <LivePanel entityId={ent.id} />
        </aside>
      </div>
    </div>
  );
}

// ════════════════════════════ Slot ════════════════════════════

interface SlotProps {
  kind: SlotKind;
  entity: Episode;
  expanded: boolean;
  onToggle: () => void;
  onGenerate: () => void;
  onGenerateAdvanced: () => void;
  onOpenAI: (ctx?: unknown) => void;
}

function Slot({ kind, entity, expanded, onToggle, onGenerate, onGenerateAdvanced, onOpenAI }: SlotProps) {
  const status = entity.state[kind];
  const has = status === "ok" || status === "warn";
  const failed = status === "alert";
  const running = status === "run";

  // Mock metadata por slot — en real esto viene de /api/episode/<id>
  const meta = mockSlotMeta(entity, kind);

  return (
    <div className={`v3-slot ${has ? "has" : "missing"}${failed ? " failed" : ""}`}>
      <div className="v3-slot-row" onClick={onToggle}>
        <div className="v3-slot-kind">{SLOT_LABEL[kind]}</div>
        <div className="v3-slot-info">
          <div className="v3-slot-name">{meta.name || `Sin ${SLOT_LABEL[kind].toLowerCase()}`}</div>
          <div className="v3-slot-meta">{meta.subtitle}</div>
        </div>
        <div className="v3-slot-status">
          <SlotStatus status={status} />
          <span style={{ color: "var(--text-mute)" }}>{meta.when}</span>
        </div>
        <div className="v3-slot-actions" onClick={(e) => e.stopPropagation()}>
          {has ? (
            <>
              <button className="v3-btn xs" onClick={onGenerate} title={`Regenerar ${SLOT_LABEL[kind].toLowerCase()}`}>
                Regenerar
              </button>
              <button className="v3-btn xs ghost" onClick={onGenerateAdvanced} title="Formulario avanzado">
                …
              </button>
              <button className="v3-btn xs ghost" onClick={onToggle}
                      title={expanded ? "Cerrar visor" : "Abrir visor"}>
                {expanded ? <Icon name="close" size={10}/> : <Icon name="arrow" size={10}/>}
              </button>
            </>
          ) : kind === "pdf" ? (
            <span className="v3-pill dim">solo lectura</span>
          ) : (
            <>
              <button className="v3-btn xs primary" onClick={onGenerate}>
                Generar {SLOT_LABEL[kind].toLowerCase()}
              </button>
              <button className="v3-btn xs ghost" onClick={onGenerateAdvanced} title="Formulario avanzado">
                …
              </button>
            </>
          )}
        </div>
      </div>

      {/* Inline tail (always visible when there's last-gen info) */}
      {meta.tail && !expanded && (
        <div className={`v3-slot-tail ${failed ? "failed" : has ? "ok" : ""}`}>
          {meta.tail}
        </div>
      )}

      {/* Expanded viewer */}
      {expanded && (
        <div className="v3-slot-body">
          <SlotViewer kind={kind} entity={entity} />
          <SlotLogFull kind={kind} entity={entity} onOpenAI={onOpenAI} />
        </div>
      )}
    </div>
  );
}

function SlotStatus({ status }: { status: string }) {
  if (status === "ok")    return <span className="v3-pill ok"><span className="v3-pill-dot"/>OK</span>;
  if (status === "warn")  return <span className="v3-pill warn"><span className="v3-pill-dot"/>warn</span>;
  if (status === "alert") return <span className="v3-pill alert"><span className="v3-pill-dot"/>fail</span>;
  if (status === "run")   return <span className="v3-pill y"><span className="v3-pill-dot"/>generando</span>;
  return <span className="v3-pill dim"><span className="v3-pill-dot"/>—</span>;
}

// Mock metadata (replace with /api/episode/<id> data in real integration)
function mockSlotMeta(entity: Episode, kind: SlotKind) {
  const status = entity.state[kind];
  if (status === "empty") return { name: "", subtitle: "Sin generar", when: "—", tail: "" };
  const paths: Record<SlotKind, string> = {
    pdf:      `PDFs/${entity.id}.pdf`,
    guion:    `Guiones/${entity.id}_${slugify(entity.title)}.txt`,
    escaleta: `escaletas/${entity.id}_${slugify(entity.title)}.md`,
    audio:    `episodios/${entity.id}.mp3`,
    video:    `Videos/${entity.id}.mp4`,
  };
  const sizes: Record<SlotKind, string> = {
    pdf:      "2.4 MB · 18 pág.",
    guion:    "42 kB · 9 842 palabras · 142 turnos",
    escaleta: "8.1 kB · 8 bloques",
    audio:    "58 MB · 32:08 · 192 kbps",
    video:    "—",
  };
  const whens: Record<SlotKind, string> = {
    pdf:      "12 may 09:21",
    guion:    "12 may 14:08",
    escaleta: "12 may 14:30",
    audio:    "12 may 17:12",
    video:    status === "warn" ? "drift 1.8s @ 41:22" : "—",
  };
  const tails: Record<SlotKind, string> = {
    pdf:      "",
    guion:    status === "ok"
      ? "[validate] 9 842 palabras · 142 turnos · balance 48/52 · OK"
      : status === "warn"
      ? "[validate] guion truncado en bloque 4 — re-generar"
      : "",
    escaleta: status === "ok"
      ? "[validate] 8/8 bloques con contenido · OK"
      : "",
    audio:    status === "alert"
      ? "[render] ERROR ElevenLabs 502 en bloque 7 — reintenta con --solo-bloque 7"
      : status === "ok"
      ? "[render] 1 silencio de 4.2s @ 23:18 · LUFS −15.8 · OK"
      : status === "run"
      ? "[render] bloque 7/12 sintetizando MARIA (3 442 chars)…"
      : "",
    video:    status === "warn"
      ? "[align] drift 1.8s @ 41:22 — re-render escena 6"
      : "",
  };
  return {
    name: paths[kind],
    subtitle: sizes[kind],
    when: whens[kind],
    tail: tails[kind],
  };
}

function slugify(s: string): string {
  return s.toLowerCase()
    .replace(/^episodio [a-z0-9_]+ — /i, "")
    .replace(/[áàä]/g, "a").replace(/[éèë]/g, "e").replace(/[íìï]/g, "i")
    .replace(/[óòö]/g, "o").replace(/[úùü]/g, "u").replace(/ñ/g, "n")
    .replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "").slice(0, 24);
}

// ════════════════════════════ Slot viewer ════════════════════════════

function SlotViewer({ kind, entity }: { kind: SlotKind; entity: Episode }) {
  if (entity.state[kind] === "empty") {
    return (
      <div className="v3-empty">
        <p className="v3-empty-title">Sin contenido todavía</p>
        <p className="v3-empty-hint">Pulsa Generar para producir este contenido</p>
      </div>
    );
  }
  if (kind === "pdf") {
    return (
      <iframe src={`/file/PDFs/${entity.id}.pdf`} title={`PDF ${entity.id}`}/>
    );
  }
  if (kind === "guion" || kind === "escaleta") {
    return (
      <pre>{`# ${entity.id} · ${SLOT_LABEL[kind]}\n\n[contenido cargado desde /api/episode/${entity.id}]\n\n# BLOQUE_INTRO\n\nIAGO: Vale María, hoy nos metemos con los Transformers.\nMARIA: Buena entrada. ${entity.title}.\n…`}</pre>
    );
  }
  if (kind === "audio") {
    return (
      <audio controls src={`/file/episodios/${entity.id}.mp3`}>
        Tu navegador no soporta el player de audio
      </audio>
    );
  }
  if (kind === "video") {
    return (
      <div className="v3-empty">
        <p className="v3-empty-title">Vídeopodcast no disponible</p>
        <p className="v3-empty-hint">El pipeline de vídeo aún no está cableado</p>
      </div>
    );
  }
  return null;
}

function SlotLogFull({ kind, entity, onOpenAI }: { kind: SlotKind; entity: Episode; onOpenAI: (c?: unknown) => void }) {
  if (kind === "pdf") return null;
  const pipe = SLOT_PIPELINE[kind];
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        marginBottom: 8,
      }}>
        <span style={{ fontFamily: "var(--f-mono)", fontSize: 10.5, letterSpacing: "0.14em",
                       textTransform: "uppercase", color: "var(--text-mute)" }}>
          Log de generación · {pipe}
        </span>
        <button className="v3-btn xs ghost"
                onClick={() => onOpenAI({ target: entity.id, kind, purpose: "diagnose" })}>
          Diagnosticar con IA
        </button>
      </div>
      <pre>{`[2026-05-12 14:08:13] ${pipe}.py --ep ${entity.id} --spec PODCAST_M_SPEC.md\n[2026-05-12 14:08:14] reading PDF: PDFs/${entity.id}.pdf (18 pages)\n[2026-05-12 14:08:18] sending to claude-sonnet-4-5 (max_tokens=18000)\n[2026-05-12 14:08:42] received 9842 words · 142 turns\n[2026-05-12 14:08:43] validating with podcast_spec.py\n[2026-05-12 14:08:43] OK · 9 842 palabras · 142 turnos · balance 48/52\n[2026-05-12 14:08:43] written to Guiones/${entity.id}_${slugify(entity.title)}.txt\n[2026-05-12 14:08:43] tokens: in=12 489 · out=14 322 · cost=$0.18\n[2026-05-12 14:08:43] done in 30.2s · exit 0`}</pre>
    </div>
  );
}

// ════════════════════════════ TemaCard ════════════════════════════

function TemaCard({ tema, onClick }: { tema: Episode; onClick: () => void }) {
  const done = SLOT_KINDS.filter((k) => tema.state[k] === "ok").length;
  const total = SLOT_KINDS.length;
  const pct = Math.round((done / total) * 100);
  const tnum = tema.id.split("_")[1];
  return (
    <div className="v3-mod" onClick={onClick}>
      <span className="v3-mod-pct">{pct}%</span>
      <div className="v3-mod-row">
        <span className="v3-mod-id">{tnum}</span>
      </div>
      <div className="v3-mod-name">{tema.title.replace(/^T\d+ — /, "")}</div>
      <div className="v3-mod-children">
        {SLOT_KINDS.map((k) => (
          <span key={k} className={`v3-mod-child ${tema.state[k] === "ok" ? "ok" : tema.state[k] === "warn" ? "warn" : tema.state[k] === "alert" ? "alert" : ""}`}/>
        ))}
      </div>
    </div>
  );
}

// ════════════════════════════ Live Panel ════════════════════════════

function LivePanel({ entityId }: { entityId: string }) {
  const live = getLiveProc();
  const relevant = live.filter((p) => p.cmd.includes(entityId.split("_")[0]));
  return (
    <div className="v3-live">
      <div className="v3-live-hd">
        <span className={`v3-live-dot${relevant.length > 0 ? " running" : ""}`}/>
        Live stream
        <span className="v3-live-meta">refresh 5s</span>
      </div>
      <div className="v3-live-body">
        {relevant.length === 0 ? (
          <div className="v3-live-empty">
            Sin procesos activos sobre {entityId}.<br/>
            Al lanzar una generación aparecerá aquí en tiempo real.
          </div>
        ) : (
          relevant.map((p) => (
            <div key={p.id} className="v3-live-card">
              <div className="v3-live-card-head">
                <span className="v3-live-card-pill">RUNNING</span>
                <span className="v3-live-card-elapsed">{p.t}</span>
              </div>
              <div className="v3-live-card-script">{p.cmd}</div>
              <div className="v3-live-card-tail">{`[bloque 7/12] sintetizando MARIA (3 442 chars)…\n[ElevenLabs] streaming chunk 14/22 · 1.2 KB/s\n[stitch] mp3 bytes=58 442 391`}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
