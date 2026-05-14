// PageMetricas — métricas de difusión reales (Fase 2).
// Datos de /api/metrics: connectors/analytics/{spotify,ivoox,linkedin}.
// Sin credenciales en .env, cada plataforma se muestra como "no configurado"
// (degradación honesta — sin datos sintéticos).
import * as React from "react";
import { Btn, Icon, Kpi, Panel, StatusDot, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";

const PLATFORMS = ["spotify", "ivoox", "linkedin"];
const COLORS = { spotify: "#1DB954", ivoox: "#E5005B", linkedin: "#0A66C2" };

function num(n) {
  return (n || 0).toLocaleString("es-ES");
}

function PlatformDetail({ p }) {
  if (!p) return null;
  const color = COLORS[p.source] || "var(--y)";
  const show = p.show;
  const episodes = p.episodes || [];
  const posts = p.posts || [];

  if (!p.configured) {
    return (
      <Panel title={<span>{p.label}</span>} meta="no configurado">
        <div className="mono dim" style={{ fontSize: 12, lineHeight: 1.6, padding: "12px 0" }}>
          Conector sin credenciales. {p.detail}
          {p.missing && p.missing.length > 0 && (
            <div style={{ marginTop: 8, color: "var(--warn)" }}>
              Añade a <span style={{ color: "var(--y)" }}>.env</span>: {p.missing.join(", ")}
            </div>
          )}
        </div>
      </Panel>
    );
  }
  if (p.error) {
    return (
      <Panel title={<span>{p.label}</span>} meta="error">
        <div className="mono" style={{ fontSize: 12, color: "var(--alert)", padding: "12px 0" }}>{p.error}</div>
      </Panel>
    );
  }

  return (
    <div className="col gap-8">
      <div className="kpi-grid">
        <Kpi label="Seguidores" value={num(show?.followers)}
             delta={show?.new_followers ? `+${num(show.new_followers)} nuevos` : ""} deltaDir="up"/>
        <Kpi label={`Streams · ${show?.window_days || 30}d`} value={num(show?.total_streams_window)}/>
        <Kpi label={p.source === "linkedin" ? "Publicaciones" : "Episodios"}
             value={p.source === "linkedin" ? posts.length : episodes.length}/>
      </div>

      {p.source === "linkedin" ? (
        <Panel title={<span><Icon name="episode" size={12}/> &nbsp;Publicaciones</span>} noPad>
          <table className="tbl">
            <thead><tr>
              <th>Publicación</th>
              <th style={{ width: 110, textAlign: "right" }}>Impresiones</th>
              <th style={{ width: 80, textAlign: "right" }}>Clicks</th>
              <th style={{ width: 90, textAlign: "right" }}>Engagement</th>
            </tr></thead>
            <tbody>
              {posts.map((post) => (
                <tr key={post.post_id}>
                  <td style={{ fontSize: 13 }}>{post.text_preview || post.post_id}</td>
                  <td className="mono tabular" style={{ textAlign: "right", color }}>{num(post.impressions)}</td>
                  <td className="mono tabular" style={{ textAlign: "right" }}>{num(post.clicks)}</td>
                  <td className="mono tabular" style={{ textAlign: "right" }}>
                    {post.engagement_rate != null ? `${(post.engagement_rate * 100).toFixed(1)}%` : "—"}
                  </td>
                </tr>
              ))}
              {posts.length === 0 && (
                <tr><td colSpan={4} className="mono dim" style={{ textAlign: "center", padding: 16 }}>
                  Sin publicaciones en la ventana.
                </td></tr>
              )}
            </tbody>
          </table>
        </Panel>
      ) : (
        <Panel title={<span><Icon name="episode" size={12}/> &nbsp;Episodios</span>} noPad>
          <table className="tbl">
            <thead><tr>
              <th>Episodio</th>
              <th style={{ width: 100, textAlign: "right" }}>Streams</th>
              <th style={{ width: 100, textAlign: "right" }}>Oyentes</th>
              <th style={{ width: 110, textAlign: "right" }}>Finalización</th>
            </tr></thead>
            <tbody>
              {episodes.map((e) => (
                <tr key={e.episode_id}>
                  <td style={{ fontSize: 13 }}>{e.title || e.episode_id}</td>
                  <td className="mono tabular" style={{ textAlign: "right", color }}>{num(e.streams)}</td>
                  <td className="mono tabular" style={{ textAlign: "right" }}>{num(e.listeners)}</td>
                  <td className="mono tabular" style={{ textAlign: "right" }}>
                    {e.completion_rate != null ? `${Math.round(e.completion_rate * 100)}%` : "—"}
                  </td>
                </tr>
              ))}
              {episodes.length === 0 && (
                <tr><td colSpan={4} className="mono dim" style={{ textAlign: "center", padding: 16 }}>
                  Sin episodios en la ventana.
                </td></tr>
              )}
            </tbody>
          </table>
        </Panel>
      )}
    </div>
  );
}

function PageMetricas({ onNav, onOpenAI }) {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [tab, setTab] = React.useState("global");

  const load = React.useCallback(() => {
    setLoading(true);
    fetch("/api/metrics", { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false); })
      .catch((e) => { setData({ ok: false, error: String(e), platforms: {} }); setLoading(false); });
  }, []);
  React.useEffect(() => { load(); }, [load]);

  const platforms = (data && data.platforms) || {};
  const list = PLATFORMS.map((s) => platforms[s]).filter(Boolean);
  const configured = list.filter((p) => p.configured);
  const totalFollowers = configured.reduce((s, p) => s + ((p.show && p.show.followers) || 0), 0);
  const totalStreams = configured.reduce((s, p) => s + ((p.show && p.show.total_streams_window) || 0), 0);

  return (
    <div className="content">
      <PageHeader
        title="Métricas de difusión"
        sub="Spotify · iVoox · LinkedIn · datos reales de los conectores de analytics"
        actions={
          <React.Fragment>
            <Btn sm kind="ghost" onClick={load} icon={<Icon name="refresh" size={11}/>}>
              {loading ? "Sincronizando…" : "Sincronizar ahora"}
            </Btn>
            <Btn sm kind="primary" onClick={() => onOpenAI({ target: "Métricas de difusión", purpose: "improve" })}
                 icon={<Icon name="spark" size={11}/>}>Analizar con IA</Btn>
          </React.Fragment>
        }
      />
      <SourcePills files={srcFor("metricas")}/>

      {loading ? (
        <div className="mono dim" style={{ fontSize: 12, padding: "40px 0", textAlign: "center" }}>
          Consultando conectores de analytics…
        </div>
      ) : data && !data.ok ? (
        <div className="mono" style={{ fontSize: 12, padding: "40px 0", textAlign: "center", color: "var(--alert)" }}>
          No se pudieron cargar las métricas: {data.error || "error"}
        </div>
      ) : (
        <React.Fragment>
          <div className="kpi-grid mb-12">
            <Kpi label="Plataformas activas" value={`${configured.length}`} unit={`/ ${list.length}`}/>
            <Kpi label="Seguidores totales" value={num(totalFollowers)}/>
            <Kpi label="Streams · 30d" value={num(totalStreams)}/>
            <Kpi label="Conectores" value={list.length} delta="analytics/"/>
          </div>

          <div className="tabs mb-12">
            {[{ id: "global", label: "Global" }, ...PLATFORMS.map((s) => ({
              id: s, label: (platforms[s] && platforms[s].label) || s,
            }))].map((t) => (
              <div key={t.id} className={`tab ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
                {t.label}
                {t.id !== "global" && platforms[t.id] && (
                  <StatusDot status={platforms[t.id].configured ? "ok" : "empty"} sm/>
                )}
              </div>
            ))}
          </div>

          {tab === "global" ? (
            <div className="grid gap-8" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
              {list.map((p) => (
                <div key={p.source} className="panel"
                     onClick={() => setTab(p.source)}
                     style={{ padding: "14px 18px", cursor: "pointer", borderLeft: `3px solid ${COLORS[p.source] || "var(--y)"}` }}>
                  <div className="row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
                    <div className="display" style={{ fontSize: 14, letterSpacing: "0.04em" }}>{p.label}</div>
                    <StatusDot status={p.configured ? "ok" : "empty"}/>
                  </div>
                  {p.configured ? (
                    <div className="mono" style={{ fontSize: 12, color: "var(--text-dim)" }}>
                      {num(p.show && p.show.followers)} seguidores · {num(p.show && p.show.total_streams_window)} streams/30d
                    </div>
                  ) : (
                    <div className="mono dim" style={{ fontSize: 11, lineHeight: 1.5 }}>
                      No configurado{p.missing && p.missing.length ? ` · faltan: ${p.missing.join(", ")}` : ""}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <PlatformDetail p={platforms[tab]}/>
          )}
        </React.Fragment>
      )}
    </div>
  );
}

export { PageMetricas };
