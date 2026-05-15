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
  FIXTURE_RECENT_FILES as RECENT_FILES, FIXTURE_TOKEN_DATA as TOKEN_DATA,
  FIXTURE_AI_LOG as AI_LOG, GUION_PREVIEW, CHECKS_M3, applyBootstrap,
} from "./data";
import { Sidebar, Topbar, AIDrawer } from "./shell";
import {
  useTweaks, TweaksPanel, TweakSection, TweakSlider, TweakRadio, TweakSelect,
} from "./components/tweaks/TweaksPanel";
import {
  PageInicio, PageMaster, PageModulo, PagePizarra, PageMapa, PageConectores,
  PageLanzador, PageFuentes, PagePlayer, PageLogs, PageOptimizar, PageConsumo,
  PageAjustes, PageMetricas, PageEpisodio,
} from "./pages";


// ============================ data.jsx ============================

// data.jsx — Fixtures for Maquinaria Pesada cockpit
// 22 episodios = 15 M + 7 T

Object.assign(window, {
  MODULES, EPISODES, RECENT_FILES, TOKEN_DATA, AI_LOG,
  GUION_PREVIEW, CHECKS_M3, KINDS, SOURCES, pathOf,
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

// ============================ pages-1.jsx ============================

// pages-1.jsx — Inicio + Master + Módulo

// ════════════════════════════════════════════════════════════
// INICIO — was "Landing". Now also explains the IA reorganization.
// ════════════════════════════════════════════════════════════
// ============================ pages-2.jsx ============================

// pages-2.jsx — Episodio + Pizarra

// ════════════════════════════════════════════════════════════
// PIZARRA — generador de episodios real (audio + video pipelines)
// ════════════════════════════════════════════════════════════

// ============================ pages-3.jsx ============================

// pages-3.jsx — Mapa, Conectores, Lanzador, Fuentes, Previsualizar,
//                Logs, Optimizar, Consumo, Ajustes
// ────────────────────────────────────────────────────────────────

// ════════════════════════════════════════════════════════════
// SHARED FIXTURES (local to these pages)
// ════════════════════════════════════════════════════════════
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
    pizarra:    [{ label: "Inicio", id: "home" }, { label: "Diseño" }, { label: "Pizarra" }],
    mapa:       [{ label: "Inicio", id: "home" }, { label: "Diseño" }, { label: "Mapa" }],
    conectores: [{ label: "Inicio", id: "home" }, { label: "Pipeline" }, { label: "Conectores" }],
    lanzador:   [{ label: "Inicio", id: "home" }, { label: "Pipeline" }, { label: "Lanzador" }],
    fuentes:    [{ label: "Inicio", id: "home" }, { label: "Recursos" }, { label: "Fuentes" }],
    player:     [{ label: "Inicio", id: "home" }, { label: "Recursos" }, { label: "Previsualizar" }],
    metricas:   [{ label: "Inicio", id: "home" }, { label: "Recursos" }, { label: "Métricas" }],
    logs:       [{ label: "Inicio", id: "home" }, { label: "Sistema" }, { label: "Logs" }],
    optimizar:  [{ label: "Inicio", id: "home" }, { label: "Sistema" }, { label: "Optimizar" }],
    consumo:    [{ label: "Inicio", id: "home" }, { label: "Sistema" }, { label: "Consumo" }],
    ajustes:    [{ label: "Inicio", id: "home" }, { label: "Sistema" }, { label: "Ajustes" }],
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
