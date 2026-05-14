#!/usr/bin/env python3
"""
dual_debate_maquinaria.py
Debate colaborativo Claude ↔ ChatGPT sobre la estrategia de lanzamiento
y sistema autónomo del podcast "Maquinaria Pesada".

Uso:
    python dual_debate_maquinaria.py
    python dual_debate_maquinaria.py "pregunta personalizada"

Requiere:
    export ANTHROPIC_API_KEY="sk-ant-..."
    export OPENAI_API_KEY="sk-proj-..."
    pip install anthropic openai
"""

import os
import sys
import anthropic
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Fix UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ── Verificación de claves ────────────────────────────────────────────────────
def verificar_claves():
    errores = []
    if not os.environ.get("ANTHROPIC_API_KEY"):
        errores.append("❌ ANTHROPIC_API_KEY no encontrada")
    if not os.environ.get("OPENAI_API_KEY"):
        errores.append("❌ OPENAI_API_KEY no encontrada")
    if errores:
        print("\n".join(errores))
        print("\nConfigura las claves:")
        print('  export ANTHROPIC_API_KEY="sk-ant-..."')
        print('  export OPENAI_API_KEY="sk-proj-..."')
        sys.exit(1)
    print("✅ Claves API detectadas correctamente\n")

# ── Clientes ──────────────────────────────────────────────────────────────────
verificar_claves()
claude_client = anthropic.Anthropic()
gpt_client    = OpenAI()

# ── Modelos ───────────────────────────────────────────────────────────────────
CLAUDE_FAST  = "claude-haiku-4-5"
GPT_FAST     = "gpt-4o-mini"
GPT_STRONG   = "gpt-4o"

MAX_TOKENS_RONDA    = 350
MAX_TOKENS_COMPRESS = 150
MAX_TOKENS_FINAL    = 800

# ── Contexto del proyecto (precargado) ───────────────────────────────────────
CONTEXTO_PROYECTO = """
CONTEXTO DEL PROYECTO — "Maquinaria Pesada" (podcast):
- Podcast 100% autogenerado por IA, sin intervención humana (guión, voz, edición)
- Temática: IA y tecnología aplicada a empresas
- Contenido: resúmenes de episodios de un máster de IA (un episodio por módulo)
- Estado actual: 1-2 episodios piloto grabados
- Canal principal de difusión: LinkedIn
- Objetivo: crecer audiencia rápido
- Ideas ya barajadas: canal Telegram de pago/exclusivo, clips cortos, meta-contenido sobre el proceso IA
- GPT propone evolucionar hacia un sistema autónomo con: generación de variantes (A/B testing),
  scoring engine basado en métricas, módulo de aprendizaje que decide qué publicar,
  integración n8n + Python backend
- Stack técnico mencionado: n8n + Python backend
"""

SYSTEM_EXPERTO = (
    "Eres un experto en estrategia de contenido digital, growth hacking y sistemas autónomos con IA. "
    "Contexto del proyecto:\n" + CONTEXTO_PROYECTO +
    "\nResponde de forma densa y estructurada. "
    "Sé directo: sin saludos, sin cierre, sin repetir el enunciado. "
    "Máximo 4 bloques concisos con títulos en negrita."
)

SYSTEM_COMPRESSOR = (
    "Extrae SOLO los puntos estratégicos esenciales de este texto. "
    "Formato: lista de 4-5 ítems de máximo 25 palabras cada uno. "
    "Sin introducción ni conclusión."
)

# ── Funciones de debate ───────────────────────────────────────────────────────
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
    try:
        from cockpit.core.usage_tracker import track_openai
        track_openai(r, model=GPT_FAST, source="dual_debate_maquinaria.py",
                     kind="generation", latency_ms=int((_t.monotonic() - _t0) * 1000))
    except ImportError:
        pass
    return r.choices[0].message.content.strip()


def ronda_claude(problema: str, contexto_previo: str, instruccion_extra: str = "") -> str:
    prompt = f"PROBLEMA A RESOLVER:\n{problema}"
    if contexto_previo:
        prompt += f"\n\nPUNTOS CLAVE DE RONDAS ANTERIORES:\n{contexto_previo}"
    if instruccion_extra:
        prompt += f"\n\nINSTRUCCIÓN PARA ESTA RONDA:\n{instruccion_extra}"

    import time as _t
    _t0 = _t.monotonic()
    r = claude_client.messages.create(
        model=CLAUDE_FAST,
        max_tokens=MAX_TOKENS_RONDA,
        system=SYSTEM_EXPERTO,
        messages=[{"role": "user", "content": prompt}]
    )
    try:
        from cockpit.core.usage_tracker import track_anthropic
        track_anthropic(r, model=CLAUDE_FAST, source="dual_debate_maquinaria.py",
                        kind="generation", latency_ms=int((_t.monotonic() - _t0) * 1000))
    except ImportError:
        pass
    return r.content[0].text.strip()


def ronda_gpt(problema: str, contexto_previo: str, instruccion_extra: str = "",
              modelo: str = GPT_FAST, max_tokens: int = MAX_TOKENS_RONDA) -> str:
    prompt = f"PROBLEMA A RESOLVER:\n{problema}"
    if contexto_previo:
        prompt += f"\n\nPUNTOS CLAVE DE RONDAS ANTERIORES:\n{contexto_previo}"
    if instruccion_extra:
        prompt += f"\n\nINSTRUCCIÓN PARA ESTA RONDA:\n{instruccion_extra}"

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
    try:
        from cockpit.core.usage_tracker import track_openai
        track_openai(r, model=modelo, source="dual_debate_maquinaria.py",
                     kind="generation", latency_ms=int((_t.monotonic() - _t0) * 1000))
    except ImportError:
        pass
    return r.choices[0].message.content.strip()


# ── Orquestador principal ─────────────────────────────────────────────────────
def debate(problema: str, verbose: bool = True) -> str:
    sep = "─" * 65

    # RONDA 1 — Claude: Primera aproximación
    if verbose:
        print(f"\n{sep}")
        print("🔵 RONDA 1 — Claude (Haiku): Primera aproximación estratégica")
        print(sep)

    r1 = ronda_claude(
        problema=problema,
        contexto_previo="",
        instruccion_extra=(
            "Propón la estrategia inicial más sólida para este problema. "
            "Sé específico con pasos, prioridades y timing."
        )
    )
    if verbose:
        print(r1)

    r1c = comprimir(r1)

    # RONDA 2 — GPT-4o-mini: Crítica y ajuste
    if verbose:
        print(f"\n{sep}")
        print("🟢 RONDA 2 — ChatGPT (GPT-4o-mini): Crítica y ajustes")
        print(sep)

    r2 = ronda_gpt(
        problema=problema,
        contexto_previo=r1c,
        instruccion_extra=(
            "Identifica los 2-3 puntos débiles o ausencias críticas de la propuesta anterior. "
            "Propón mejoras concretas y accionables. No repitas lo que ya funciona bien."
        )
    )
    if verbose:
        print(r2)

    r2c = comprimir(r2)

    # RONDA 3 — Claude: Validación + elemento creativo
    if verbose:
        print(f"\n{sep}")
        print("🔵 RONDA 3 — Claude (Haiku): Validación + creatividad")
        print(sep)

    r3 = ronda_claude(
        problema=problema,
        contexto_previo=f"Propuesta inicial:\n{r1c}\n\nCríticas y ajustes GPT:\n{r2c}",
        instruccion_extra=(
            "1. Verifica que la solución combinada responde al problema original completamente. "
            "2. Corrige inconsistencias si las hay. "
            "3. Añade UN elemento creativo no obvio que marque diferencia — "
            "   puede ser una táctica sorprendente, una automatización elegante o un ángulo inesperado. "
            "Márcalo claramente con [💡 CREATIVIDAD]."
        )
    )
    if verbose:
        print(r3)

    r3c = comprimir(r3)

    # RONDA 4 — GPT-4o: Síntesis final ejecutable
    if verbose:
        print(f"\n{sep}")
        print("🟢 RONDA 4 — ChatGPT (GPT-4o): Síntesis final ejecutable")
        print(sep)

    r4 = ronda_gpt(
        problema=problema,
        contexto_previo=(
            f"Propuesta Claude R1:\n{r1c}\n\n"
            f"Crítica GPT R2:\n{r2c}\n\n"
            f"Validación + creatividad Claude R3:\n{r3c}"
        ),
        instruccion_extra=(
            "Eres el validador final. Entrega la PROPUESTA DEFINITIVA integrada:\n"
            "1. Confirma que responde al problema original.\n"
            "2. Señala cualquier riesgo o laguna pendiente.\n"
            "3. Estructura la solución final con: QUÉ hacer, CUÁNDO, CÓMO y POR QUÉ.\n"
            "Debe ser directamente ejecutable, sin ambigüedades."
        ),
        modelo=GPT_STRONG,
        max_tokens=MAX_TOKENS_FINAL
    )
    if verbose:
        print(r4)
        print(f"\n{sep}")
        print("✅ DEBATE COMPLETADO — Solución final arriba")
        print(sep)

    return r4


# ── Problema por defecto (Maquinaria Pesada) ─────────────────────────────────
PROBLEMA_DEFAULT = """
¿Cuál es la estrategia óptima de lanzamiento y crecimiento para el podcast
"Maquinaria Pesada" (100% autogenerado por IA, temática IA para empresas,
resúmenes de módulos de máster), considerando:

1. Canal principal: LinkedIn (objetivo: crecer audiencia rápido)
2. Canales secundarios: Instagram, TikTok (¿sí o no? ¿cómo?)
3. Comunidad: Telegram con contenido exclusivo (¿cuándo activar? ¿qué ofrecer?)
4. Sistema autónomo: ¿merece la pena construir un scoring engine + A/B testing
   de hooks desde el principio, o es prematuro con 1-2 episodios piloto?
5. El meta-contenido (mostrar el proceso IA) ¿debe ser el gancho principal
   o secundario?

Dame un plan de acción por fases con decisiones claras.
"""


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        problema = " ".join(sys.argv[1:])
        print(f"📋 Problema personalizado: {problema[:80]}...")
    else:
        problema = PROBLEMA_DEFAULT
        print("📋 Usando problema por defecto: estrategia Maquinaria Pesada")

    print("\n🚀 Iniciando debate Claude ↔ ChatGPT (4 rondas)...\n")
    debate(problema, verbose=True)
