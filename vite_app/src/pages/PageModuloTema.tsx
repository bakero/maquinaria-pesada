// PageModuloTema — página unificada para módulo (Mn) y tema (Mn_Tk).
//
// Datos reales del backend (web_server.py):
//   - GET /api/episode/<id>   → detail con slots[kind].{exists,path,size,mtime,tail}
//   - GET /api/module/<id>    → módulo + children (M + temas) + progreso agregado
//   - GET /api/stream  (SSE)  → live procs + recent files en tiempo real
//   - POST /api/episode/<id>/generate  ó  /api/run  → lanza generación
//
// Cuando el backend devuelve null/error, degrada elegantemente a los
// fixtures de data.ts para que el desarrollo del frontend no se bloquee.

import * as React from "react";
import { Icon } from "../components";
import { FIXTURE_EPISODES, FIXTURE_MODULES, cleanEpisodeTitle, getShorts } from "../data";
import type { Episode } from "../types";
import {
  generateSlot,
  useEntity, useEntityLogLines, useEntityRuns, useLiveStream, useModule,
  type EpisodeDetail, type LiveProcess, type RunSummary, type SlotMeta, type StreamSnapshot,
} from "../lib/useEntity";

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
  entityId: string;
  onNav: (page: string, payload?: string) => void;
  onOpenAI: (ctx?: unknown) => void;
  onOpenFix?: (ctx?: unknown) => void;
}

export function PageModuloTema({ entityId, onNav, onOpenAI }: PageModuloTemaProps) {
  // ── Datos reales con degradación a fixture si el backend falla.
  const { data: entityReal, refresh: refreshEntity } = useEntity(entityId);
  const isModuleGuess = !entityId.includes("_");
  const modIdGuess = entityId.split("_")[0];
  const { data: moduleReal, refresh: refreshModule } = useModule(isModuleGuess ? modIdGuess : modIdGuess);
  const { snapshot } = useLiveStream();

  // Fallback al fixture si el backend no devuelve nada.
  const fallbackEp = FIXTURE_EPISODES.find((e) => e.id === entityId)
    || FIXTURE_EPISODES.find((e) => e.id === "M3")!;
  const ent: Episode = entityReal ? episodeFromDetail(entityReal) : fallbackEp;
  const isModule = ent.kind === "M";
  const isShort = ent.kind === "S";
  const modId = ent.mod;
  const moduleMeta = FIXTURE_MODULES.find((m) => m.id === modId);

  // Los Shorts no tienen PDF ni escaleta — la "fuente" es el propio prompt
  // del generador. Filtramos los slots visibles para evitar pintar bloques
  // vacíos sin uso.
  const visibleSlots: readonly SlotKind[] = isShort
    ? (["guion", "audio", "video"] as const)
    : SLOT_KINDS;

  // Children: del backend si disponibles, si no del fixture.
  const childrenReal = moduleReal?.children ?? [];
  const temasReal = childrenReal.filter((c) => c.kind === "T");
  const fallbackTemas = FIXTURE_EPISODES.filter((e) => e.kind === "T" && e.mod === modId);
  const temas: (Episode | typeof temasReal[number])[] = temasReal.length > 0 ? temasReal : fallbackTemas;
  const moduleEpisodeFromChildren = childrenReal.find((c) => c.kind === "M");
  const moduleEpisode = moduleEpisodeFromChildren || FIXTURE_EPISODES.find((e) => e.kind === "M" && e.mod === modId);

  function slotState(item: { state: Record<string, string> | Episode["state"] }, kind: SlotKind): string {
    return (item.state as Record<string, string>)[kind] ?? "empty";
  }

  function pctOfChild(item: { state: Record<string, string> | Episode["state"] }): number {
    const ok = SLOT_KINDS.filter((k) => slotState(item, k) === "ok").length;
    return Math.round((ok / SLOT_KINDS.length) * 100);
  }

  // Progreso agregado: del backend si está, si no calcula sobre fixture
  const progressPct = moduleReal && isModule
    ? moduleReal.pct
    : isModule
    ? Math.round((temas.reduce((acc, t) => acc + SLOT_KINDS.filter((k) => slotState(t, k) === "ok").length, 0)
       + (moduleEpisode ? SLOT_KINDS.filter((k) => slotState(moduleEpisode, k) === "ok").length : 0))
       / ((temas.length + 1) * SLOT_KINDS.length) * 100)
    : isShort
    ? Math.round(visibleSlots.filter((k) => slotState(ent, k) === "ok").length / visibleSlots.length * 100)
    : pctOfChild(ent);

  const [expanded, setExpanded] = React.useState<SlotKind | null>(null);

  // Acción de generar con feedback.
  const [pending, setPending] = React.useState<SlotKind | null>(null);
  const [toast, setToast] = React.useState<string | null>(null);
  const launchSlot = React.useCallback(async (kind: SlotKind) => {
    setPending(kind);
    const r = await generateSlot(ent.id, kind);
    setPending(null);
    if (r.error) {
      setToast(`Error al lanzar ${SLOT_LABEL[kind]}: ${r.error}`);
    } else if (r.pid) {
      setToast(`${SLOT_LABEL[kind]} en producción · pid ${r.pid}`);
    } else if ((r as { ok?: boolean }).ok) {
      setToast(`${SLOT_LABEL[kind]} generado`);
    } else {
      setToast(`${SLOT_LABEL[kind]}: ${JSON.stringify(r).slice(0, 80)}`);
    }
    setTimeout(() => { setToast(null); refreshEntity(); refreshModule(); }, 3000);
  }, [ent.id, refreshEntity, refreshModule]);

  return (
    <div className="v3-page">
      {/* Header */}
      <header className="v3-mt-hd">
        <div>
          <nav className="v3-mt-crumbs">
            <a onClick={() => onNav("produccion")}>Master</a>
            <span className="sep">/</span>
            {isShort ? (
              <span className="cur">Shorts · {ent.id}</span>
            ) : isModule ? (
              <span className="cur">{modId}</span>
            ) : (
              <>
                <a onClick={() => onNav("modulo", modId)}>{modId}</a>
                <span className="sep">/</span>
                <span className="cur">{ent.id.split("_").slice(1).join("_")}</span>
              </>
            )}
          </nav>
          <div className="v3-mt-title">
            <span className="v3-mt-id">{ent.id.replace("_", " · ")}</span>
            <h1 className="v3-mt-name">{cleanEpisodeTitle(ent.title, ent.kind)}</h1>
          </div>
          <div className="v3-mt-sub">
            {isShort
              ? `Short · píldora de glosario · 60-90 s${ent.dur && ent.dur !== "—" ? ` · ${ent.dur}` : ""}`
              : isModule
              ? `${moduleReal?.name || moduleMeta?.name || ""} · módulo principal · ${temas.length} tema${temas.length !== 1 ? "s" : ""}${ent.dur && ent.dur !== "—" ? ` · ${ent.dur}` : ""}`
              : `tema corto · ${moduleReal?.name || moduleMeta?.name || modId}${ent.dur && ent.dur !== "—" ? ` · ${ent.dur}` : ""}`}
          </div>
        </div>
        <div className="v3-mt-progress">
          <div className="v3-mt-progress-val">{progressPct}%</div>
          <div className="v3-mt-progress-bar">
            <div className="v3-mt-progress-fill" style={{ width: `${progressPct}%` }}/>
          </div>
        </div>
      </header>

      {/* Sibling rail entre Shorts (S1..S5) cuando estamos en uno */}
      {isShort && (() => {
        const allShorts = getShorts();
        if (allShorts.length === 0) return null;
        const completados = allShorts.filter(
          (s) => ["guion","audio","video"].every((k) => s.state[k as SlotKind] === "ok"),
        ).length;
        return (
          <div className="v3-mt-rail-wrap">
            <div className="v3-mt-rail-meta">
              <span className="v3-mt-rail-meta-label">Navegación · Shorts</span>
              <span className="v3-mt-rail-meta-count">
                <strong>{completados}</strong>
                <span style={{ color: "var(--text-mute)" }}> completos · </span>
                <strong>{allShorts.length}</strong>
                <span style={{ color: "var(--text-mute)" }}> shorts</span>
              </span>
            </div>
            <div className="v3-mt-rail">
              {allShorts.map((s) => {
                const active = s.id === ent.id;
                const done = (["guion","audio","video"] as SlotKind[])
                  .filter((k) => s.state[k] === "ok").length;
                const dot = done === 3 ? "ok" : done >= 1 ? "warn" : "alert";
                return (
                  <div
                    key={s.id}
                    className={`v3-mt-rail-cell${active ? " active" : ""}`}
                    onClick={() => onNav("short", s.id)}
                    title={s.title}
                  >
                    <span>{s.id} · {s.term}</span>
                    <span className={`v3-mt-rail-cell-dot ${dot}`}/>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })()}

      {/* Sibling rail · navegación rápida entre módulo paraguas y sus temas */}
      {!isShort && (isModule || temas.length > 0) && (() => {
        const temasCompletos = temas.filter(
          (t) => SLOT_KINDS.every((k) => slotState(t, k) === "ok"),
        ).length;
        const temasConAlgo = temas.filter(
          (t) => SLOT_KINDS.some((k) => slotState(t, k) === "ok"),
        ).length;
        return (
          <div className="v3-mt-rail-wrap">
            <div className="v3-mt-rail-meta">
              <span className="v3-mt-rail-meta-label">Navegación · {modId}</span>
              <span className="v3-mt-rail-meta-count">
                <strong>{temasCompletos}</strong>
                <span style={{ color: "var(--text-mute)" }}> completos · </span>
                <strong>{temasConAlgo}</strong>
                <span style={{ color: "var(--text-mute)" }}> con algo · </span>
                <strong>{temas.length}</strong>
                <span style={{ color: "var(--text-mute)" }}> temas</span>
              </span>
            </div>
            <div className="v3-mt-rail">
              {moduleEpisode && (
                <div
                  className={`v3-mt-rail-cell${isModule ? " active" : " parent"}`}
                  onClick={() => onNav("modulo", modId)}
                  title={moduleEpisode.title}
                >
                  <span>{modId} · paraguas</span>
                  <span className="v3-mt-rail-cell-dot ok"/>
                </div>
              )}
              {temas.map((t) => {
                const tnum = t.id.split("_").slice(1).join("_");
                const active = !isModule && t.id === ent.id;
                const slotDone = SLOT_KINDS.filter((k) => slotState(t, k) === "ok").length;
                const dot = slotDone === 5 ? "ok"
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
          </div>
        );
      })()}

      {/* Sub-temas · grid prominente justo debajo del rail cuando hay temas */}
      {!isShort && isModule && temas.length > 0 && (
        <section className="v3-mt-subtemas">
          <header className="v3-hd">
            <div className="v3-hd-left">
              <span className="v3-hd-eyebrow">Temas de {modId}</span>
              <h2 className="v3-hd-title">{temas.length} tema{temas.length !== 1 ? "s" : ""} · click para abrir</h2>
            </div>
            <div className="v3-hd-meta">
              {temas.filter((t) => SLOT_KINDS.every((k) => slotState(t, k) === "ok")).length} / {temas.length} completos
            </div>
          </header>
          <div className="v3-mods">
            {temas.map((t) => (
              <TemaCard
                key={t.id}
                tema={{ id: t.id, title: t.title, state: t.state as Record<string, string> }}
                onClick={() => onNav("tema", t.id)}
              />
            ))}
          </div>
        </section>
      )}

      {/* Aviso si esperamos temas pero el backend no los devolvió todavía */}
      {!isShort && isModule && temas.length === 0 && (
        <section className="v3-mt-subtemas">
          <header className="v3-hd">
            <div className="v3-hd-left">
              <span className="v3-hd-eyebrow">Temas de {modId}</span>
              <h2 className="v3-hd-title">cargando o sin temas</h2>
            </div>
          </header>
          <div className="v3-empty" style={{ padding: 32 }}>
            <p className="v3-empty-title">Sin temas detectados todavía</p>
            <p className="v3-empty-hint">
              El backend no devolvió sub-temas para {modId}.
              Comprueba que existan PDFs <code>{modId}_T*.pdf</code> en la carpeta <code>PDFs/</code>.
            </p>
          </div>
        </section>
      )}

      {/* Toast */}
      {toast && (
        <div style={{
          position: "fixed", bottom: 24, left: "50%", transform: "translateX(-50%)",
          padding: "10px 20px", background: "var(--y)", color: "var(--bg)",
          fontFamily: "var(--f-mono)", fontSize: 12, fontWeight: 600, letterSpacing: "0.02em",
          zIndex: 900,
        }}>{toast}</div>
      )}

      {/* Two-column body */}
      <div className="v3-mt">
        <div>
          {visibleSlots.map((kind) => (
            <Slot
              key={kind}
              kind={kind}
              entity={ent}
              detail={entityReal}
              expanded={expanded === kind}
              busy={pending === kind}
              onToggle={() => setExpanded(expanded === kind ? null : kind)}
              onGenerate={() => launchSlot(kind)}
              onGenerateAdvanced={() => onNav("sistema")}
              onOpenAI={onOpenAI}
            />
          ))}

        </div>

        <aside>
          <LivePanel entityId={ent.id} snapshot={snapshot} />
          <EpisodeRunsPanel entityId={ent.id} />
        </aside>
      </div>
    </div>
  );
}

// cleanTitle se centralizó en data.ts → cleanEpisodeTitle.

// ════════════════════════════ Slot ════════════════════════════

interface SlotProps {
  kind: SlotKind;
  entity: Episode;
  detail: EpisodeDetail | null;
  expanded: boolean;
  busy: boolean;
  onToggle: () => void;
  onGenerate: () => void;
  onGenerateAdvanced: () => void;
  onOpenAI: (ctx?: unknown) => void;
}

function Slot({ kind, entity, detail, expanded, busy, onToggle, onGenerate, onGenerateAdvanced, onOpenAI }: SlotProps) {
  const status = entity.state[kind];
  const has = status === "ok" || status === "warn";
  const failed = status === "alert";
  const slotMeta = detail?.slots?.[kind] ?? null;

  // Datos reales si disponibles, fallback informativo si no.
  const path = slotMeta?.path ?? (has ? `${kind}/${entity.id}.*` : "");
  const sizeHuman = slotMeta?.size_human ?? (has ? "—" : "");
  const whenHuman = slotMeta?.mtime_human ?? "—";
  const tail = slotMeta?.tail ?? "";

  return (
    <div className={`v3-slot ${has ? "has" : "missing"}${failed ? " failed" : ""}`}>
      <div className="v3-slot-row" onClick={onToggle}>
        <div className="v3-slot-kind">{SLOT_LABEL[kind]}</div>
        <div className="v3-slot-info">
          <div className="v3-slot-name">{path || `Sin ${SLOT_LABEL[kind].toLowerCase()}`}</div>
          <div className="v3-slot-meta">{sizeHuman}</div>
        </div>
        <div className="v3-slot-status">
          <SlotStatus status={status} busy={busy} />
          <span style={{ color: "var(--text-mute)" }}>{whenHuman}</span>
        </div>
        <div className="v3-slot-actions" onClick={(e) => e.stopPropagation()}>
          {kind === "pdf" ? (
            <>
              {slotMeta?.path && (
                <a className="v3-btn xs ghost" href={`/files/${slotMeta.path}`} target="_blank" rel="noreferrer">
                  Abrir
                </a>
              )}
              <span className="v3-pill dim">solo lectura</span>
            </>
          ) : has ? (
            <>
              <button
                className={`v3-btn xs${kind === "guion" ? " primary" : ""}`}
                onClick={onGenerate}
                disabled={busy}
                title={`Regenerar ${SLOT_LABEL[kind].toLowerCase()}`}
              >
                {busy ? "lanzando…" : "Regenerar"}
              </button>
              <button className="v3-btn xs ghost" onClick={onGenerateAdvanced} title="Formulario avanzado">
                …
              </button>
              <button className="v3-btn xs ghost" onClick={onToggle}
                      title={expanded ? "Cerrar visor" : "Abrir visor"}>
                {expanded ? <Icon name="close" size={10}/> : <Icon name="arrow" size={10}/>}
              </button>
            </>
          ) : (
            <>
              <button className="v3-btn xs primary" onClick={onGenerate} disabled={busy}>
                {busy ? "lanzando…" : `Generar ${SLOT_LABEL[kind].toLowerCase()}`}
              </button>
              <button className="v3-btn xs ghost" onClick={onGenerateAdvanced} title="Formulario avanzado">
                …
              </button>
            </>
          )}
        </div>
      </div>

      {tail && !expanded && (
        <div className={`v3-slot-tail ${failed ? "failed" : has ? "ok" : ""}`}>
          {tail}
        </div>
      )}

      {expanded && (
        <div className={`v3-slot-body kind-${kind}`}>
          <SlotViewer kind={kind} entity={entity} slotMeta={slotMeta} />
          <SlotLogFull kind={kind} entity={entity} slotMeta={slotMeta} onOpenAI={onOpenAI} />
        </div>
      )}
    </div>
  );
}

function SlotStatus({ status, busy }: { status: string; busy: boolean }) {
  if (busy)               return <span className="v3-pill y"><span className="v3-pill-dot"/>lanzando</span>;
  if (status === "ok")    return <span className="v3-pill ok"><span className="v3-pill-dot"/>OK</span>;
  if (status === "warn")  return <span className="v3-pill warn"><span className="v3-pill-dot"/>warn</span>;
  if (status === "alert") return <span className="v3-pill alert"><span className="v3-pill-dot"/>fail</span>;
  if (status === "run")   return <span className="v3-pill y"><span className="v3-pill-dot"/>generando</span>;
  return <span className="v3-pill dim"><span className="v3-pill-dot"/>—</span>;
}

// ════════════════════════════ Slot viewer ════════════════════════════

function SlotViewer({ kind, entity, slotMeta }: { kind: SlotKind; entity: Episode; slotMeta: SlotMeta | null }) {
  if (entity.state[kind] === "empty") {
    return (
      <div className="v3-empty">
        <p className="v3-empty-title">Sin contenido todavía</p>
        <p className="v3-empty-hint">Pulsa Generar para producir este contenido</p>
      </div>
    );
  }
  const url = slotMeta?.path ? `/files/${slotMeta.path}` : null;

  if (kind === "pdf") {
    if (!url) return <div className="v3-empty"><p className="v3-empty-title">PDF no disponible</p></div>;
    return <iframe src={url} title={`PDF ${entity.id}`}/>;
  }
  if (kind === "guion" || kind === "escaleta") {
    return <TextFileViewer url={url} entityId={entity.id} kind={kind}/>;
  }
  if (kind === "audio") {
    if (!url) return <div className="v3-empty"><p className="v3-empty-title">Audio no disponible</p></div>;
    return <audio controls src={url}>Tu navegador no soporta el player de audio</audio>;
  }
  if (kind === "video") {
    if (!url) {
      return (
        <div className="v3-empty">
          <p className="v3-empty-title">Vídeopodcast no disponible</p>
          <p className="v3-empty-hint">El pipeline de vídeo aún no está cableado</p>
        </div>
      );
    }
    return <video controls src={url} style={{ width: "100%", maxHeight: 480, background: "black" }}/>;
  }
  return null;
}

function TextFileViewer({ url, entityId, kind }: { url: string | null; entityId: string; kind: string }) {
  const [text, setText] = React.useState<string>("Cargando…");
  React.useEffect(() => {
    if (!url) {
      setText(`# ${entityId} · ${kind}\n\n(archivo no encontrado)`);
      return;
    }
    let cancel = false;
    fetch(url)
      .then((r) => r.ok ? r.text() : Promise.reject(r.status))
      .then((t) => { if (!cancel) setText(t.slice(0, 20_000)); })
      .catch((e) => { if (!cancel) setText(`# ${entityId} · ${kind}\n\n(error al leer: ${e})`); });
    return () => { cancel = true; };
  }, [url, entityId, kind]);
  return <pre>{text}</pre>;
}

function SlotLogFull({ kind, entity, slotMeta, onOpenAI }: {
  kind: SlotKind; entity: Episode; slotMeta: SlotMeta | null;
  onOpenAI: (c?: unknown) => void;
}) {
  if (kind === "pdf") return null;
  // Si no hay log asociado al pipeline, no renderizamos nada: evita el
  // bloque "(sin log de X para Y)" que ensucia el visor en slots vacíos.
  if (!slotMeta?.log_path) return null;

  const pipe = SLOT_PIPELINE[kind];
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        marginBottom: 8,
      }}>
        <span style={{ fontFamily: "var(--f-mono)", fontSize: 10.5, letterSpacing: "0.14em",
                       textTransform: "uppercase", color: "var(--text-mute)" }}>
          Actividad · {pipe}
          {slotMeta.log_mtime_human && slotMeta.log_mtime_human !== "—"
            ? <span style={{ marginLeft: 8, letterSpacing: 0, textTransform: "none" }}>· última run {slotMeta.log_mtime_human}</span>
            : null}
        </span>
        <button className="v3-btn xs ghost"
                onClick={() => onOpenAI({ target: entity.id, kind, purpose: "diagnose" })}>
          Diagnosticar con IA
        </button>
      </div>
      <EntityLogViewer entityId={entity.id} kind={kind}/>
    </div>
  );
}

/**
 * Visor del log de actividad de una entidad. Consume /api/entity/{id}/log-lines
 * vía useEntityLogLines: el backend filtra el daylog por la entidad y devuelve
 * solo las líneas relevantes (en vez de bajar el log entero al cliente).
 */
function EntityLogViewer({ entityId, kind }: { entityId: string; kind: string }) {
  const { data, loading } = useEntityLogLines(entityId, 7, 200);
  if (loading) return <pre>Cargando actividad…</pre>;
  if (!data.ok && data.error) return <pre>(error: {data.error})</pre>;
  if (!data.entries.length) {
    return <pre>(sin actividad de {kind} para {entityId} en los últimos 7 días)</pre>;
  }
  const text = data.entries.map((e) => `[${e.day}] ${e.line}`).join("\n");
  return <pre>{text}</pre>;
}

// ════════════════════════════ TemaCard ════════════════════════════

function TemaCard({ tema, onClick }: { tema: { id: string; title: string; state: Record<string, string> }; onClick: () => void }) {
  const done = SLOT_KINDS.filter((k) => (tema.state[k] ?? "empty") === "ok").length;
  const total = SLOT_KINDS.length;
  const pct = Math.round((done / total) * 100);
  const tnum = tema.id.split("_").slice(1).join("_");
  const status: "ok" | "warn" | "empty" = done === total ? "ok" : done > 0 ? "warn" : "empty";
  return (
    <div className="v3-mod" onClick={onClick} title={`Abrir ${tema.id}`}>
      <div className="v3-mod-row">
        <span className="v3-mod-id">{tnum}</span>
        <span className={`v3-mod-state-dot ${status}`}/>
        <span className="v3-mod-meta">{done}/{total} · {pct}%</span>
      </div>
      <div className="v3-mod-name">{cleanEpisodeTitle(tema.title, "T")}</div>
      <div className="v3-mod-children">
        {SLOT_KINDS.map((k) => (
          <span key={k} className={`v3-mod-child ${(tema.state[k] ?? "empty") === "ok" ? "ok" : (tema.state[k] ?? "empty") === "warn" ? "warn" : (tema.state[k] ?? "empty") === "alert" ? "alert" : ""}`}/>
        ))}
      </div>
    </div>
  );
}

// ════════════════════════════ Live Panel ════════════════════════════

function LivePanel({ entityId, snapshot }: { entityId: string; snapshot: StreamSnapshot }) {
  const allLive = snapshot.live || [];
  const idShort = entityId.split("_")[0];
  // procesos cuyo comando menciona la entidad o su módulo padre
  const relevant: LiveProcess[] = allLive.filter((p) =>
    p.cmd.includes(entityId) || p.cmd.includes(idShort + " ") || p.cmd.includes(idShort + ".pdf")
  );
  const otros = allLive.filter((p) => !relevant.includes(p));

  return (
    <div className="v3-live">
      <div className="v3-live-hd">
        <span className={`v3-live-dot${allLive.length > 0 ? " running" : ""}`}/>
        Live stream
        <span className="v3-live-meta">
          {allLive.length === 0 ? "sin procesos" : `${allLive.length} activo${allLive.length !== 1 ? "s" : ""}`}
        </span>
      </div>
      <div className="v3-live-body">
        {allLive.length === 0 ? (
          <div className="v3-live-empty">
            Sin procesos activos.<br/>
            Al lanzar una generación aparecerá aquí en tiempo real.
          </div>
        ) : (
          <>
            {relevant.length > 0 && relevant.map((p) => (
              <ProcCard key={p.id} proc={p} highlight />
            ))}
            {otros.length > 0 && (
              <>
                {relevant.length > 0 && (
                  <div style={{
                    fontFamily: "var(--f-mono)", fontSize: 10, letterSpacing: "0.12em",
                    textTransform: "uppercase", color: "var(--text-mute)",
                    margin: "12px 0 6px",
                  }}>Otros</div>
                )}
                {otros.map((p) => (
                  <ProcCard key={p.id} proc={p} />
                ))}
              </>
            )}
          </>
        )}

        {/* Actividad reciente (si no hay procesos activos) */}
        {allLive.length === 0 && snapshot.recent.length > 0 && (
          <>
            <div style={{
              fontFamily: "var(--f-mono)", fontSize: 10, letterSpacing: "0.12em",
              textTransform: "uppercase", color: "var(--text-mute)",
              margin: "20px 0 8px",
            }}>Actividad reciente</div>
            {snapshot.recent.slice(0, 6).map((r, i) => (
              <div key={i} style={{
                fontFamily: "var(--f-mono)", fontSize: 10.5, color: "var(--text-dim)",
                padding: "4px 0", borderTop: i > 0 ? "1px solid var(--border-2)" : "none",
              }}>
                <span style={{ color: "var(--text-mute)" }}>{r.t}</span>
                <span style={{ marginLeft: 8 }}>{shortenPath(r.path)}</span>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}

function ProcCard({ proc, highlight }: { proc: LiveProcess; highlight?: boolean }) {
  return (
    <div className="v3-live-card" style={highlight ? { borderColor: "var(--y)" } : undefined}>
      <div className="v3-live-card-head">
        <span className="v3-live-card-pill">RUN</span>
        <span className="v3-live-card-elapsed">{proc.t}</span>
      </div>
      <div className="v3-live-card-script">{proc.cmd}</div>
      <div style={{
        fontFamily: "var(--f-mono)", fontSize: 10, color: "var(--text-mute)",
        marginTop: 4,
      }}>pid {proc.pid} · {proc.cost}</div>
    </div>
  );
}

function shortenPath(p: string): string {
  if (!p) return "";
  const parts = p.split("/");
  if (parts.length <= 2) return p;
  return parts.slice(-2).join("/");
}

// ════════════════════════ Episode Runs Panel ═════════════════════════
//
// Timeline de las ejecuciones reales (runs) del día-log asociadas a este
// episodio. Lee /api/entity/<id>/runs (parseado por
// cockpit.core.log_validator.parse_log) y pinta una card por run con:
//   · estado (ok / error / running) + script + tiempo transcurrido
//   · pasos completados (load_spec ✓ generate ✓ validate ✓ save ✓)
//   · llamadas IA (intentadas / OK / error)
//   · retries · último error si lo hay
//
// Es la pieza que conecta la página del episodio con el sistema de logs
// nuevo (docs/logging.md): cada vez que el operador ejecuta un pipeline
// (M, T o S), aquí aparece en tiempo real el detalle de lo que pasó.

function EpisodeRunsPanel({ entityId }: { entityId: string }) {
  const { data, loading, refresh } = useEntityRuns(entityId, 14, 20);
  const runs = data.runs || [];

  return (
    <div className="v3-live" style={{ marginTop: 16 }}>
      <div className="v3-live-hd">
        <span className={`v3-live-dot${runs.some((r) => r.status === "running") ? " running" : ""}`}/>
        Ejecuciones
        <span className="v3-live-meta">
          {loading ? "cargando…"
            : runs.length === 0 ? "sin actividad"
            : `${runs.length} run${runs.length !== 1 ? "s" : ""}`}
        </span>
        <button
          className="v3-btn xs ghost"
          style={{ marginLeft: "auto" }}
          onClick={refresh}
          title="Recargar el día-log"
        >
          <Icon name="check" size={10}/>
        </button>
      </div>
      <div className="v3-live-body">
        {!loading && runs.length === 0 && (
          <div className="v3-live-empty">
            Sin runs registrados en los últimos 14 días.<br/>
            Cuando lances el pipeline (Regenerar guion / audio / vídeo)
            aparecerá aquí.
          </div>
        )}
        {runs.map((r) => (
          <RunCard key={r.run_id} run={r}/>
        ))}
      </div>
    </div>
  );
}

function RunCard({ run }: { run: RunSummary }) {
  const status = run.status;
  const pillCls = status === "ok"      ? "ok"
                : status === "error"   ? "alert"
                : status === "running" ? "y"
                : "dim";
  const elapsed = run.elapsed_s != null ? `${run.elapsed_s.toFixed(1)}s` : "—";
  const started = run.started_at ? new Date(run.started_at) : null;
  const startedHuman = started
    ? started.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" })
        + " · " + started.toLocaleDateString("es-ES", { day: "2-digit", month: "short" })
    : "—";
  const scriptShort = run.script.replace(/\.py$/, "");
  const aiSummary = (() => {
    const { started: s, ok, error } = run.ai_calls;
    if (s === 0 && ok === 0 && error === 0) return null;
    const parts: string[] = [];
    if (ok > 0) parts.push(`${ok} ok`);
    if (error > 0) parts.push(`${error} fail`);
    if (s !== ok + error) parts.push(`${s - ok - error} sin cerrar`);
    return parts.join(" · ");
  })();

  return (
    <div className="v3-live-card" style={{ borderLeft: `3px solid ${
      status === "ok"    ? "var(--ok)"
    : status === "error" ? "var(--alert)"
    : status === "running" ? "var(--y)"
    : "var(--border-2)"
    }` }}>
      <div className="v3-live-card-head" style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <span className={`v3-pill ${pillCls}`}>
          <span className="v3-pill-dot"/>{status}
        </span>
        <span className="v3-live-card-elapsed">{elapsed}</span>
        <span style={{
          marginLeft: "auto",
          fontFamily: "var(--f-mono)", fontSize: 10,
          color: "var(--text-mute)",
        }}>
          {startedHuman}
        </span>
      </div>
      <div className="v3-live-card-script" style={{ marginTop: 4 }}>{scriptShort}</div>
      {run.steps.length > 0 && (
        <div style={{
          marginTop: 6, display: "flex", flexWrap: "wrap", gap: 4,
          fontFamily: "var(--f-mono)", fontSize: 10,
        }}>
          {run.steps.map((s, i) => (
            <span key={i} style={{
              color: "var(--ok)", padding: "2px 6px",
              border: "1px solid var(--border-2)",
            }}>
              ✓ {s}
            </span>
          ))}
        </div>
      )}
      {(aiSummary || run.retries > 0) && (
        <div style={{
          marginTop: 6,
          fontFamily: "var(--f-mono)", fontSize: 10, color: "var(--text-mute)",
        }}>
          {aiSummary && <span>IA · {aiSummary}</span>}
          {run.retries > 0 && (
            <span style={{ marginLeft: 10, color: "var(--warn)" }}>
              retries · {run.retries}
            </span>
          )}
          <span style={{ marginLeft: 10 }}>run {run.run_id}</span>
        </div>
      )}
      {run.last_error && (
        <div style={{
          marginTop: 6,
          fontFamily: "var(--f-mono)", fontSize: 10, color: "var(--alert)",
          padding: "4px 6px", background: "var(--bg)",
          whiteSpace: "pre-wrap", wordBreak: "break-all",
        }}>
          {run.last_error}
        </div>
      )}
    </div>
  );
}

// ────────────────── helpers ──────────────────

function episodeFromDetail(d: EpisodeDetail): Episode {
  return {
    id: d.id,
    mod: d.mod,
    kind: d.kind as "M" | "T",
    title: d.title,
    dur: d.dur,
    state: d.state as Episode["state"],
  };
}
