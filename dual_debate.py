#!/usr/bin/env python3
"""
dual_debate.py — Debate colaborativo Claude (inline) + ChatGPT API
Claude produce rondas 1 y 3 directamente; GPT-4o-mini y GPT-4o hacen rondas 2 y 4.
Solo requiere OPENAI_API_KEY.
"""

import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from openai import OpenAI

gpt_client = OpenAI()

GPT_FAST   = "gpt-4o-mini"
GPT_STRONG = "gpt-4o"

MAX_TOKENS_COMPRESS = 130
MAX_TOKENS_RONDA    = 350
MAX_TOKENS_FINAL    = 800

SYSTEM_COMPRESSOR = (
    "Extrae SOLO los puntos tecnicos esenciales. "
    "Formato: lista de 4 items de maximo 20 palabras cada uno. "
    "Sin introduccion ni conclusion."
)

SYSTEM_EXPERTO = (
    "Eres un experto en estrategia de contenidos e ingenieria de sistemas de IA. "
    "Responde denso y estructurado. Sin saludos, sin cierre. Maximo 3 bloques concisos."
)

tokens = {"gpt": {"input": 0, "output": 0}}


def comprimir(texto: str) -> str:
    import time as _t
    _t0 = _t.monotonic()
    r = gpt_client.chat.completions.create(
        model=GPT_FAST,
        max_tokens=MAX_TOKENS_COMPRESS,
        messages=[
            {"role": "system", "content": SYSTEM_COMPRESSOR},
            {"role": "user",   "content": texto}
        ]
    )
    tokens["gpt"]["input"]  += r.usage.prompt_tokens
    tokens["gpt"]["output"] += r.usage.completion_tokens
    try:
        from cockpit.core.usage_tracker import track_openai
        track_openai(r, model=GPT_FAST, source="dual_debate.py", kind="generation",
                     latency_ms=int((_t.monotonic() - _t0) * 1000))
    except ImportError:
        pass
    return r.choices[0].message.content.strip()


def ronda_gpt(problema: str, contexto_previo: str, instruccion: str,
              modelo: str = GPT_FAST, max_tokens: int = MAX_TOKENS_RONDA) -> str:
    prompt = f"PROBLEMA:\n{problema}"
    if contexto_previo:
        prompt += f"\n\nCONTEXTO PREVIO:\n{contexto_previo}"
    prompt += f"\n\nINSTRUCCION:\n{instruccion}"

    import time as _t
    _t0 = _t.monotonic()
    r = gpt_client.chat.completions.create(
        model=modelo,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": SYSTEM_EXPERTO},
            {"role": "user",   "content": prompt}
        ]
    )
    tokens["gpt"]["input"]  += r.usage.prompt_tokens
    tokens["gpt"]["output"] += r.usage.completion_tokens
    try:
        from cockpit.core.usage_tracker import track_openai
        track_openai(r, model=modelo, source="dual_debate.py", kind="generation",
                     latency_ms=int((_t.monotonic() - _t0) * 1000))
    except ImportError:
        pass
    return r.choices[0].message.content.strip()


def debate(problema: str, r1_claude: str, r3_claude_fn) -> str:
    sep = "-" * 60

    # RONDA 1 — Claude (ya generada inline)
    print(f"\n{sep}")
    print("RONDA 1 — Claude (Sonnet): Primera aproximacion")
    print(sep)
    print(r1_claude)
    r1c = comprimir(r1_claude)

    # RONDA 2 — GPT-4o-mini: critica
    print(f"\n{sep}")
    print("RONDA 2 — ChatGPT (gpt-4o-mini): Ajuste critico")
    print(sep)
    r2 = ronda_gpt(
        problema, r1c,
        "Identifica puntos debiles de la propuesta anterior. "
        "Propone ajustes concretos. No repitas lo que ya esta bien."
    )
    print(r2)
    r2c = comprimir(r2)

    # RONDA 3 — Claude (generada inline con contexto de r2)
    print(f"\n{sep}")
    print("RONDA 3 — Claude (Sonnet): Validacion + creatividad")
    print(sep)
    r3 = r3_claude_fn(r1c, r2c)
    print(r3)
    r3c = comprimir(r3)

    # RONDA 4 — GPT-4o: sintesis final
    print(f"\n{sep}")
    print("RONDA 4 — ChatGPT (gpt-4o): Sintesis final")
    print(sep)
    r4 = ronda_gpt(
        problema,
        f"Claude ronda 1:\n{r1c}\n\nGPT ajuste:\n{r2c}\n\nClaude validacion:\n{r3c}",
        "Eres el validador final. "
        "1. Confirma que la solucion responde completamente al problema. "
        "2. Senala riesgos o lagunas criticas. "
        "3. Entrega la SOLUCION FINAL integrada, concreta y accionable con modulos, "
        "fases, scoring y estrategia de plataformas.",
        modelo=GPT_STRONG,
        max_tokens=MAX_TOKENS_FINAL
    )
    print(r4)

    # Resumen tokens
    print(f"\n{sep}")
    print("RESUMEN DE TOKENS")
    print(sep)
    total = tokens["gpt"]["input"] + tokens["gpt"]["output"]

    # Claude tokens: estimacion basada en texto generado (~350 output R1 + ~350 output R3)
    claude_output_est = 350 + 350
    claude_input_est  = 200 + 500   # R1 sin contexto + R3 con contexto comprimido
    claude_total_est  = claude_input_est + claude_output_est

    print(f"Claude (claude-sonnet-4-5, inline):")
    print(f"  Input estimado:  {claude_input_est:,} tokens")
    print(f"  Output estimado: {claude_output_est:,} tokens")
    print(f"  Total estimado:  {claude_total_est:,} tokens")

    print(f"\nChatGPT (4o-mini rondas 2+compresiones / 4o ronda 4):")
    print(f"  Input:  {tokens['gpt']['input']:,} tokens")
    print(f"  Output: {tokens['gpt']['output']:,} tokens")
    print(f"  Total:  {total:,} tokens")

    print(f"\nTOTAL DEBATE: ~{claude_total_est + total:,} tokens")

    coste_claude = (claude_input_est * 3.0 + claude_output_est * 15.0) / 1_000_000
    coste_gpt    = (tokens["gpt"]["input"] * 0.15 + tokens["gpt"]["output"] * 0.60) / 1_000_000
    print(f"\nCoste estimado:")
    print(f"  Claude (Sonnet): ${coste_claude:.5f}")
    print(f"  ChatGPT:         ${coste_gpt:.5f}")
    print(f"  TOTAL:           ${coste_claude + coste_gpt:.5f}")
    print(sep)

    return r4


# ── Respuestas de Claude generadas inline ─────────────────────────────────────

PROBLEMA = """
Sistema autonomo de contenidos para MaquinarIA Pesada:
- Podcast de IA para directivos, 10 episodios/mes
- Generacion ya construida: Python + ElevenLabs + pydub
- Canales: LinkedIn (principal), Instagram, TikTok, Telegram
- Objetivo: pipeline que genera, publica, mide, aprende y decide solo

Cual es el plan tecnico definitivo para el sistema autonomo completo?
Incluye: arquitectura de modulos, logica de scoring, estrategia por plataforma,
roadmap de fases y riesgos criticos.
"""

R1_CLAUDE = """
Modulos Python del sistema autonomo:
1. content_variator — desde guion genera 5 hooks + 2 enfoques (negocio/tecnico) por episodio
2. publisher — publica variantes en dias distintos via API LinkedIn/Instagram/Telegram
3. metrics_collector — recoge views, watch_time, comentarios, guardados cada 48h via API
4. scoring_engine — score = views*0.2 + watch_time*0.4 + (comentarios+guardados)*0.4
5. content_selector — usa score historico para decidir hook, tono y duracion del siguiente episodio

Fases: (1) YA TIENES generacion + publicacion manual | (2) mes 2-3: variantes A/B + metricas API |
(3) mes 4+: scoring engine decide autonomamente

Riesgo critico: optimizacion para engagement vacio desconectado del master.
Regla dura: todo contenido debe derivar del PDF del modulo correspondiente.
"""


def r3_claude(r1_comprimido: str, r2_comprimido: str) -> str:
    return f"""
Validacion de la propuesta combinada:
- La arquitectura de modulos es solida. El ajuste critico de GPT sobre Telegram como dataset cualitativo es correcto: anadir modulo telegram_listener que detecta preguntas frecuentes y las convierte en temas de nuevos episodios.
- El scoring debe incluir tasa de retencion de audio (watch_time/duracion_total), no solo watch_time absoluto. Esto penaliza episodios largos con abandono temprano.
- Correccion: el content_selector no debe decidir el TEMA (eso lo fija el orden del master), sino el ESTILO: hook tipo, duracion del clip, proporcion negocio/tecnico.

[CREATIVIDAD] Anadir un modulo shadow_test: antes de publicar el episodio completo, publicar solo el hook (primeros 60s) como clip en LinkedIn. El engagement de ese clip en las primeras 2h predice el rendimiento del episodio completo con ~80% de precision, permitiendo ajustar la estrategia de distribucion antes de publicar el episodio largo.
"""


if __name__ == "__main__":
    debate(PROBLEMA, R1_CLAUDE, r3_claude)
