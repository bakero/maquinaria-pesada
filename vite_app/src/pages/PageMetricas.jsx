// PageMetricas — extraído del monolito (Fase 1b).
import * as React from "react";
import { Btn, Icon, Panel, StatusDot, Kpi, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";

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

export { PageMetricas };
