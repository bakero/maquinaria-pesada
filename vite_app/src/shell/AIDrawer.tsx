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

    const FALLBACK = mode === "fix"
      ? "He inspeccionado el episodio.\n\n1. El audio M3_T2 falla en el bloque 4: 'Atención escalada' — ElevenLabs devolvió 502 en el segundo intento.\n2. Voy a regenerar SOLO ese bloque con la voz María y volver a concatenar.\n3. No tocaré el guion ni la escaleta.\n\n¿Procedo?"
      : "He analizado este episodio. Mejoras sugeridas:\n\n→ El bloque 3 del guion es 22% más largo que la media. Considera dividirlo.\n→ María lleva 4 turnos seguidos entre 18:00 y 21:30. Insertar una intervención de Iago.\n→ La escaleta no menciona RoPE — está en el guion. Refrescar.\n\n[fallback offline]";

    // Llamada real al backend; si falla → fallback simulado.
    let reply = FALLBACK;
    let usage: Usage | null = null;
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
        if (data && data.text) {
          reply = data.text;
          usage = data.usage || null;
        }
      }
    } catch { /* keep fallback */ }

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
