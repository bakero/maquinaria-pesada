// PageAjustes — API keys reales (Fase 2f).
// Estado desde /api/api-keys: presencia de cada key en .env / env vars.
import * as React from "react";
import { Btn, Icon, Panel, StatusDot, PageHeader, SourcePills } from "../components";
import { srcFor } from "../lib/nav";

function PageAjustes({ onNav, onOpenAI }) {
  const [checking, setChecking] = React.useState(true);
  const [keys, setKeys] = React.useState([]);

  const recheck = React.useCallback(() => {
    setChecking(true);
    fetch("/api/api-keys", { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => { setKeys((d && d.providers) || []); setChecking(false); })
      .catch(() => setChecking(false));
  }, []);

  React.useEffect(() => { recheck(); }, [recheck]);

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
        {checking && keys.length === 0 && (
          <div className="mono dim" style={{ fontSize: 12, padding: "16px 0" }}>Verificando…</div>
        )}
        {keys.map((k) => {
          const expected = k.expected || [];
          const found = k.found || [];
          const status = k.ok ? "ok" : "warn";
          const badge = k.ok ? "OK" : "FALTAN KEYS";
          const missing = expected.filter((n) => !found.some((f) => f.name === n));
          const detail = k.ok
            ? `${found.length}/${expected.length} keys presentes`
            : (k.error || `faltan: ${missing.join(", ") || "—"}`);
          return (
            <div key={k.provider} className="panel" style={{ padding: "14px 16px" }}>
              <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
                <div className="display" style={{ fontSize: 14, letterSpacing: "0.04em", textTransform: "capitalize" }}>
                  {k.provider}
                </div>
                <StatusDot status={status}/>
              </div>
              <div className="mono dim" style={{ fontSize: 10, marginBottom: 8 }}>{badge}</div>
              <div className="row" style={{ marginBottom: 8, flexWrap: "wrap", gap: 4 }}>
                {expected.map((n) => (
                  <span key={n} className="badge" style={{
                    color: found.some((f) => f.name === n) ? "var(--ok)" : "var(--warn)",
                  }}>{n}</span>
                ))}
              </div>
              <div className="mono" style={{ fontSize: 10, color: "var(--text-dim)", lineHeight: 1.4, minHeight: 28 }}>
                {detail}
              </div>
              <div className="row gap-3 mt-8">
                <Btn sm kind="ghost" style={{ flex: 1 }}
                     onClick={() => window.alert(`Rota la API key de ${k.provider} editando .env y reinicia el servidor.`)}>
                  <Icon name="settings" size={10}/> Rotar
                </Btn>
                <Btn sm kind="ghost" style={{ flex: 1 }} onClick={recheck}>
                  <Icon name="check" size={10}/> Re-verificar
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

export { PageAjustes };
