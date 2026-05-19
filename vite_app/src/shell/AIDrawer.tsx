import * as React from "react";
import { Btn, Icon } from "../components";

interface Msg { role: "user" | "ai" | "system"; body: string; }
interface Usage { model: string; input_tokens?: number; output_tokens?: number; cost_usd?: number; }

export interface AIDrawerProps {
  open: boolean;
  onClose: () => void;
  mode: "improve" | "fix" | string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  context: any;
}

export function AIDrawer({ open, onClose, mode, context }: AIDrawerProps) {
  const [input, setInput] = React.useState("");
  const [messages, setMessages] = React.useState<Msg[]>([]);
  const [streaming, setStreaming] = React.useState(false);
  const [streamText, setStreamText] = React.useState("");
  const [lastUsage, setLastUsage] = React.useState<Usage | null>(null);

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

  const send = async () => {
    if (!input.trim()) return;
    const userText = input;
    setMessages((m) => [...m, { role: "user", body: input }]);
    setInput("");
    setStreaming(true);
    setStreamText("");

    // Llamada real al backend. Si falla, mostramos un error CLARO y honesto
    // en vez de una respuesta inventada (la versión anterior simulaba un
    // diagnóstico falso de "audio M3_T2 falla en bloque 4" que confundía
    // al usuario haciéndole creer que era análisis real).
    let reply = "";
    let usage: Usage | null = null;
    let failed = false;
    let failureReason = "";
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
        if (data && data.ok && data.text) {
          reply = data.text;
          usage = data.usage || null;
        } else {
          failed = true;
          failureReason = (data && data.text) || "respuesta sin texto";
        }
      } else {
        failed = true;
        failureReason = `HTTP ${res.status}`;
      }
    } catch (e) {
      failed = true;
      failureReason = String(e);
    }

    if (failed) {
      reply = [
        "⚠ No se pudo contactar con Claude.",
        "",
        `Razón: ${failureReason}`,
        "",
        "Comprueba que la API key de Anthropic está en .env (variable",
        "ANTHROPIC_API_KEY) y que el servidor cockpit está sirviendo /api/ai/chat.",
        "Mira el panel Sistema → Ajustes para verificar credenciales.",
      ].join("\n");
    }

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

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  };

  const title = mode === "fix" ? "Arreglar con Claude" : "Mejorar con IA";

  return (
    <React.Fragment>
      <div className={`drawer-overlay ${open ? "open" : ""}`} onClick={onClose} />
      <aside className={`drawer ${open ? "open" : ""}`}>
        <div className="drawer-hd">
          <div className="drawer-title">
            <Icon name={mode === "fix" ? "wrench" : "spark"} size={14} />
            {title}
          </div>
          <button className="btn ghost sm" onClick={onClose}><Icon name="close" size={11} /></button>
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
          <Btn kind="primary" sm onClick={send}><Icon name="arrow" size={11} /> Enviar</Btn>
        </div>

        <div className="drawer-foot" style={{ borderTop: 0, paddingTop: 0 }}>
          <div className="ai-cost">
            {lastUsage ? (
              <React.Fragment>
                <span>Modelo <b>{lastUsage.model}</b></span>
                <span>Tokens <b>{(lastUsage.input_tokens || 0) + (lastUsage.output_tokens || 0)}</b></span>
                <span>Coste <b>{(lastUsage.cost_usd || 0).toFixed(4)}$</b></span>
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
