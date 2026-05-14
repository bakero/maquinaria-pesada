// app.jsx — Main app, routing, tweaks panel

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "yellowIntensity": 35,
  "font": "Oswald + Barlow",
  "mode": "industrial",
  "density": "regular",
  "masterView": "lista"
}/*EDITMODE-END*/;

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [page, setPage] = React.useState(() => {
    const h = window.location.hash.replace("#", "");
    return WIRED.has(h) ? h : "home";
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

  const nav = (id) => {
    if (!WIRED.has(id)) return;
    setPage(id);
    window.location.hash = id;
    window.scrollTo(0, 0);
  };

  const openAI  = (ctx) => setAIDrawer({ open: true, mode: "improve", context: ctx });
  const openFix = (ctx) => setAIDrawer({ open: true, mode: "fix",     context: ctx });
  const closeAI = ()    => setAIDrawer((s) => ({ ...s, open: false }));

  // Crumbs by page
  const CRUMBS = {
    home:       [{ label: "Inicio" }],
    master:     [{ label: "Inicio", id: "home" }, { label: "Master" }],
    modulo:     [{ label: "Inicio", id: "home" }, { label: "Master", id: "master" }, { label: "M3 · Transformers" }],
    episodio:   [{ label: "Inicio", id: "home" }, { label: "Master", id: "master" }, { label: "M3", id: "modulo" }, { label: "M3_T2" }],
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
            target: "M3_T2",
            error: "ElevenLabs 502 en bloque 4 · audio truncado en 03:14",
            id: "M3_T2",
          }) : null}
        />
        {t.mode === "industrial" && <HazardTape/>}

        {page === "home"       && <PageInicio     onNav={nav} onOpenAI={openAI}/>}
        {page === "master"     && <PageMaster     onNav={nav} onOpenAI={openAI} view={t.masterView} density={t.density}/>}
        {page === "modulo"     && <PageModulo     onNav={nav} onOpenAI={openAI}/>}
        {page === "episodio"   && <PageEpisodio   onNav={nav} onOpenAI={openAI} onOpenFix={openFix}/>}
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
  ReactDOM.createRoot(document.getElementById("root")).render(<App/>);

if (window.__BOOTSTRAP__ && typeof window.__BOOTSTRAP__.then === "function") {
  window.__BOOTSTRAP__.then(__mp_mount).catch(__mp_mount);
} else {
  __mp_mount();
}
