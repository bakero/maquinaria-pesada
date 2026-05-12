import { useEffect, useState } from "react";
import { Btn, Icon, Kpi, Panel, StatusDot } from "./components";
import { aiChat, fetchBootstrap } from "./api";
import type { AIUsage, BootstrapPayload } from "./types";

export function App() {
  const [data, setData] = useState<BootstrapPayload | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBootstrap().then((d) => {
      setData(d);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="loading">Cargando bootstrap…</div>;

  if (!data) {
    return (
      <div className="content">
        <Panel title="Sin conexión con web_server.py">
          <p className="mono dim">
            Arranca el backend con <code>python web_server.py</code> y refresca.
          </p>
        </Panel>
      </div>
    );
  }

  const okMods = data.MODULES.filter((m) => m.status === "ok").length;

  return (
    <div className="app">
      <main className="main">
        <header className="topbar">
          <div className="crumbs">
            <span className="cur">Maquinaria Pesada · Vite + TS</span>
          </div>
          <div className="topbar-actions">
            <span className="badge y">v0.1 · TS</span>
          </div>
        </header>

        <div className="content">
          <h1 className="page-title">Estado de obra</h1>

          <div className="kpi-grid mb-12">
            <Kpi label="Módulos completos" value={okMods} unit={`/ ${data.MODULES.length}`} />
            <Kpi label="Episodios" value={data.EPISODES.length} unit="total" />
            <Kpi
              label="Coste 30d"
              value={data.TOKEN_DATA.cost_30d.toFixed(2)}
              unit="$"
              delta={`${Math.round((data.TOKEN_DATA.cost_30d / Math.max(data.TOKEN_DATA.budget, 1)) * 100)}% del budget`}
            />
            <Kpi label="Tokens 30d" value={(data.TOKEN_DATA.total_30d / 1_000_000).toFixed(2)} unit="M" />
          </div>

          <div className="grid gap-8" style={{ gridTemplateColumns: "1.4fr 1fr" }}>
            <Panel
              title={<span><Icon name="grid" size={12} /> &nbsp;Módulos</span>}
              meta={`${data.MODULES.length} módulos`}
            >
              <div className="col gap-3">
                {data.MODULES.map((m) => (
                  <div key={m.id} className="row gap-3" style={{ padding: "8px 10px", border: "1px solid var(--border)" }}>
                    <StatusDot status={m.status} />
                    <span className="mono" style={{ minWidth: 32 }}>{m.id}</span>
                    <span className="display" style={{ flex: 1 }}>{m.name}</span>
                    <span className="mono dim">{m.pct}%</span>
                  </div>
                ))}
              </div>
            </Panel>

            <Panel title={<span><Icon name="spark" size={12} /> &nbsp;Asistente</span>}>
              <ChatBox />
            </Panel>
          </div>
        </div>
      </main>
    </div>
  );
}

function ChatBox() {
  const [input, setInput] = useState("");
  const [reply, setReply] = useState<string>("");
  const [usage, setUsage] = useState<AIUsage | null>(null);
  const [pending, setPending] = useState(false);

  const send = async () => {
    if (!input.trim()) return;
    setPending(true);
    setReply("");
    const res = await aiChat("improve", null, input);
    setReply(res.text);
    setUsage(res.usage);
    setPending(false);
  };

  return (
    <div className="col gap-4">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Pregunta lo que necesites…"
        rows={3}
        className="ai-input"
        style={{ width: "100%", resize: "vertical" }}
      />
      <Btn kind="primary" onClick={send} disabled={pending} icon={<Icon name="arrow" size={11} />}>
        {pending ? "Pensando…" : "Enviar"}
      </Btn>
      {reply && (
        <pre className="mono" style={{ whiteSpace: "pre-wrap", fontSize: 11 }}>{reply}</pre>
      )}
      {usage && (
        <div className="ai-cost">
          <span>Modelo <b>{usage.model}</b></span>
          <span>Tokens <b>{usage.input_tokens + usage.output_tokens}</b></span>
          <span>Coste <b>{usage.cost_usd.toFixed(4)}$</b></span>
        </div>
      )}
    </div>
  );
}
