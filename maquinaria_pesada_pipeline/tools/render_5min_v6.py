#!/usr/bin/env python3
"""
Render directo de los primeros 5 min del M0 con escaleta v6 handcrafted.

Saltea escaleta_parser/escaleta_to_pipeline (que rotaban clips heuristicamente)
y construye scene_track.json + scene_timeline.json directamente desde un dict
Python con TODO explicito:
  - clip_slug por sub-segmento (con mode normal/reverse)
  - posicion zona por overlay
  - tiempos absolutos exactos

Coste: $0 (no llama a Kling, solo usa biblioteca ya generada + reverses).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT.parent / ".env", override=True)

from pipeline.logger import get_logger
from pipeline.asset_validator import validate_project_config
from pipeline.transcriber import transcribe_episode
from pipeline.content_extractor import extract_content
from pipeline.audio_analyzer import analyze_episode_audio
from pipeline.overlay_renderer import render_frames
from pipeline.subtitle_generator import generate_srt
from pipeline.video_compositor import compose_video, derive_video_basename
from pipeline.scene_library import SceneLibrary


PROJECT = ROOT.parent
LIB = SceneLibrary(PROJECT / "Videos" / "escenas_biblioteca")


def _clip(slug: str) -> str:
    """Devuelve path absoluto del clip dado su slug (el _rev ya esta registrado)."""
    entry = LIB.find(slug)
    if not entry:
        raise RuntimeError(f"Clip no en library: {slug}")
    p = Path(entry["path"])
    if not p.exists():
        raise RuntimeError(f"Clip falta en disco: {slug} -> {p}")
    return str(p)


# ── DATA · ESCALETA v6 · PRIMEROS 5 MINUTOS ────────────────────────

# Cada intervencion tiene:
#   tc_in, tc_out, speaker, text, tono, plano
#   pizarra: bool, pizarra_t_in (relativo)
#   clips_studio: lista (slug, scene_t_in, scene_t_out)  → body o intro pre-pizarra
#   clips_pip:    lista (slug, scene_t_in, scene_t_out)  → solo si pizarra
#   overlays:     lista de overlays con posicion y datos exactos

INTERVENTIONS = [
    # ── 0.1 LEAD SILENCE ────────────────────────────────────────
    {
        "id": "0.1", "section": "PRELUDIO",
        "tc_in": 0.000, "tc_out": 1.928,
        "speaker": "", "text": "", "tono": "silencio",
        "plano": "BLACK", "pizarra": False,
        "clips_studio": [],   # blank
        "overlays": [],
    },
    # ── 1.1 HOOK Maria · 16.93s · UN CLIP + pizarra ────────────
    {
        "id": "1.1", "section": "HOOK",
        "tc_in": 2.060, "tc_out": 18.990,
        "speaker": "MARIA", "tono": "ironico",
        "text": "En 2026, el 88% de las empresas dice que ya usa "
                "inteligencia artificial. El otro 12% dice que lo está "
                "evaluando. Básicamente, todo el mundo está en el tema, "
                "igual que todo el mundo ha leído los términos y "
                "condiciones de cada app que instala. Exactamente nadie.",
        "plano": "TWO_SHOT_M_ACTIVE",
        "pizarra": True, "pizarra_t_in": 4.0,
        # 1 clip cubre toda la intervencion (Maria solo 21.2s > 16.93s)
        "clips_studio": [
            ("studio_maria_solo_v1", 0.0, 16.93),
        ],
        # PIP cubre 12.93s (4.0 → 16.93). Encadena 2 clips para variedad
        "clips_pip": [
            ("studio_maria_solo_v2",     0.0, 10.4),    # 10.4s
            ("studio_two_m_active_v2",   10.4, 12.93),  # 2.53s mas
        ],
        "overlays": [
            {"t_in": 0.0,  "t_out": 16.93, "type": "name_tag",
             "position": "TOP_RIGHT",
             "data": {"name": "MARIA", "color": "#F5C400"}},
            {"t_in": 4.0,  "t_out": 16.93, "type": "stat_card",
             "position": "MID_LEFT",
             "data": {"label": "ADOPCIÓN 2026", "value": "88%",
                      "subtitle": "empresas usan IA", "color": "#F5C400"}},
            {"t_in": 8.0,  "t_out": 16.93, "type": "stat_card",
             "position": "MID_RIGHT",
             "data": {"label": "EVALUANDO", "value": "12%",
                      "subtitle": "siguen estudiándolo", "color": "#888888"}},
            # Sticker omitido (no tenemos PNG generado todavia)
        ],
    },
    # ── 1.2 HOOK Maria cierre · 15.13s · UN CLIP, sin pizarra ──
    {
        "id": "1.2", "section": "HOOK",
        "tc_in": 18.920, "tc_out": 34.050,
        "speaker": "MARIA", "tono": "firme",
        "text": "Hoy vemos qué hay de verdad detrás de ese número. "
                "Qué es la I.A., de dónde viene, cómo se estructura y "
                "qué implica para cualquier organización que tenga que "
                "tomar decisiones con ella encima de la mesa. Esto es "
                "MaquinarIA Pesada. Arrancamos.",
        "plano": "CLOSE_UP_MARIA",
        "pizarra": False,
        "clips_studio": [
            ("studio_maria_solo_v3", 0.0, 15.13),
        ],
        "overlays": [
            {"t_in": 0.0,  "t_out": 15.13, "type": "name_tag",
             "position": "TOP_RIGHT",
             "data": {"name": "MARIA", "color": "#F5C400"}},
        ],
    },
    # ── 2.1 SINTONIA ────────────────────────────────────────────
    # No es una intervencion con clip propio. El compositor pone
    # intro_video.mp4 como overlay en sintonia_start..sintonia_end.
    # Lo dejamos como segmento blank, el overlay se agrega en compose.
    {
        "id": "2.1", "section": "SINTONIA",
        "tc_in": 34.050, "tc_out": 46.720,
        "speaker": "", "text": "(sintonía instrumental)", "tono": "musica",
        "plano": "SINTONIA",
        "pizarra": False,
        "clips_studio": [],   # blank, intro_video manda
        "overlays": [],
    },
    # ── 3.1 SALUDO Yago · 16.02s · 2 clips (Yago solo dura 10s) ─
    {
        "id": "3.1", "section": "SALUDO",
        "tc_in": 46.720, "tc_out": 62.740,
        "speaker": "YAGO", "tono": "serio",
        "text": "Bienvenidos a MaquinarIA Pesada. Soy Yago, y esto es "
                "el módulo cero: la introducción estratégica a la I.A. "
                "El episodio que nadie quiere admitir que necesita pero "
                "que conviene escuchar antes de aprobar cualquier "
                "presupuesto de inteligencia artificial en tu empresa.",
        "plano": "TWO_SHOT_Y_ACTIVE",
        "pizarra": False,
        # 2 clips · cut a t=8.0s (entre frases naturales)
        "clips_studio": [
            ("studio_two_y_active_v1",   0.0,  8.0),
            ("studio_yago_solo_v1",      8.0, 16.02),
        ],
        "overlays": [
            {"t_in": 0.0, "t_out": 16.02, "type": "name_tag",
             "position": "TOP_RIGHT",
             "data": {"name": "YAGO", "color": "#4DB8FF"}},
            {"t_in": 2.0, "t_out": 10.0, "type": "section_indicator",
             "position": "TOP_CENTER",
             "data": {"label": "MÓDULO 0 · Introducción Estratégica"}},
        ],
    },
    # ── 3.2 SALUDO Maria advertencia · 16.41s · 1 clip Maria solo ─
    {
        "id": "3.2", "section": "SALUDO",
        "tc_in": 60.980, "tc_out": 77.390,
        "speaker": "MARIA", "tono": "tecnico",
        "text": "Y yo soy María. Antes de arrancar, la advertencia "
                "legal y sensata: este episodio está generado por un "
                "sistema automático de inteligencia artificial y puede "
                "contener errores. Contrastad con fuentes profesionales. "
                "Si algo suena demasiado bueno o demasiado catastrófico, "
                "probablemente está exagerado.",
        "plano": "CLOSE_UP_MARIA",
        "pizarra": False,
        "clips_studio": [
            ("studio_maria_solo_v4", 0.0, 16.41),
        ],
        "overlays": [
            {"t_in": 0.0, "t_out": 16.41, "type": "name_tag",
             "position": "TOP_RIGHT",
             "data": {"name": "MARIA", "color": "#F5C400"}},
            {"t_in": 3.0, "t_out": 16.41, "type": "warning_badge",
             "position": "TOP_LEFT",
             "data": {"label": "CONTENIDO GENERADO POR IA",
                      "color": "#CC2200"}},
        ],
    },
    # ── 3.3 SALUDO Yago objetivo · 15.24s · 2 clips ────────────
    {
        "id": "3.3", "section": "SALUDO",
        "tc_in": 80.600, "tc_out": 95.840,
        "speaker": "YAGO", "tono": "didactico",
        "text": "El objetivo de hoy: que al terminar tengas el mapa "
                "mental básico de la I.A. Qué tipos existen, por qué "
                "el momento actual es diferente a todos los intentos "
                "anteriores y qué impacto real tiene esto en las "
                "organizaciones.",
        "plano": "TWO_SHOT_Y_ACTIVE",
        "pizarra": False,
        "clips_studio": [
            ("studio_two_y_active_v3",   0.0, 7.5),
            ("studio_yago_solo_v2",      7.5, 15.24),
        ],
        "overlays": [
            {"t_in": 0.0, "t_out": 15.24, "type": "name_tag",
             "position": "TOP_RIGHT",
             "data": {"name": "YAGO", "color": "#4DB8FF"}},
            {"t_in": 3.0, "t_out": 15.24, "type": "recap_grid",
             "position": "BOTTOM_FULL_WIDTH",
             "data": {"items": ["TIPOS", "MOMENTO", "IMPACTO"]}},
        ],
    },
    # ── 3.4 "Vamos allá" · 0.78s · two-shot regla <3s ──────────
    {
        "id": "3.4", "section": "SALUDO",
        "tc_in": 93.080, "tc_out": 93.860,
        "speaker": "MARIA", "tono": "enfatico",
        "text": "Vamos allá.",
        "plano": "TWO_SHOT_M_ACTIVE",
        "pizarra": False,
        "clips_studio": [
            ("studio_two_m_active_v5", 0.0, 0.78),
        ],
        "overlays": [
            {"t_in": 0.0, "t_out": 0.78, "type": "name_tag",
             "position": "TOP_RIGHT",
             "data": {"name": "MARIA", "color": "#F5C400"}},
        ],
    },
    # ── 4.1 BLOQUE_1 Maria inviernos · 40.25s · 2 clips Maria + pizarra ──
    {
        "id": "4.1", "section": "BLOQUE_1",
        "tc_in": 94.660, "tc_out": 134.910,
        "speaker": "MARIA", "tono": "didactico",
        "text": "Para entender dónde estamos hay que saber de dónde "
                "venimos. Y la historia de la I.A. tiene un patrón que "
                "se repite con asombrosa regularidad: promesa enorme, "
                "entusiasmo masivo, resultados que no llegan a la "
                "velocidad prometida y financiación que se corta. Eso "
                "se llama invierno de la I.A. Hemos tenido dos antes "
                "de este momento. El primero a finales de los 70, "
                "cuando los sistemas basados en reglas no escalaron "
                "más allá de dominios muy acotados. El segundo a "
                "finales de los 90, cuando las redes neuronales de los "
                "80 no podían entrenarse por falta de datos y de "
                "potencia de cálculo.",
        "plano": "TWO_SHOT_M_ACTIVE",
        "pizarra": True, "pizarra_t_in": 15.0,
        # 2 clips Maria solo (21+21=42 cubre 40.25). 1 cut en t=20s
        "clips_studio": [
            ("studio_maria_solo_v2", 0.0, 20.0),
            ("studio_maria_solo_v3", 20.0, 40.25),
        ],
        # PIP 25.25s · encadena 3 clips
        "clips_pip": [
            ("studio_two_m_active_v3",     15.0, 25.4),  # 10.4s
            ("studio_two_m_active_v4",     25.4, 35.8),  # 10.4s
            ("studio_two_m_active_v5",     35.8, 40.25), # 4.45s
        ],
        "overlays": [
            {"t_in": 0.0,  "t_out": 40.25, "type": "name_tag",
             "position": "TOP_RIGHT",
             "data": {"name": "MARIA", "color": "#F5C400"}},
            {"t_in": 15.0, "t_out": 40.25, "type": "timeline_visual",
             "position": "BOTTOM_FULL_WIDTH",
             "data": {"items": [
                 {"year": "1956", "label": "Dartmouth"},
                 {"year": "70s",  "label": "1er INVIERNO"},
                 {"year": "90s",  "label": "2do INVIERNO"},
                 {"year": "2017", "label": "Transformers"},
                 {"year": "HOY",  "label": "GenAI"},
             ]}},
            {"t_in": 19.0, "t_out": 40.25, "type": "regulation_alert",
             "position": "MID_LEFT",
             "data": {"title": "INVIERNO IA",
                      "text": "promesa > resultado → corte de financiación"}},
            {"t_in": 26.0, "t_out": 40.25, "type": "warning_badge",
             "position": "TOP_CENTER",
             "data": {"label": "2 INVIERNOS PREVIOS", "color": "#CC2200"}},
            {"t_in": 33.0, "t_out": 40.25, "type": "stat_card",
             "position": "MID_RIGHT",
             "data": {"label": "1970s", "value": "REGLAS",
                      "subtitle": "no escalan", "color": "#888888"}},
        ],
    },
    # ── 4.2 Yago escepticismo · 12.12s · 2 clips Yago ────────────
    {
        "id": "4.2", "section": "BLOQUE_1",
        "tc_in": 132.660, "tc_out": 144.780,
        "speaker": "YAGO", "tono": "ironico",
        "text": "Lo que significa que tienes todo el derecho histórico "
                "del mundo a mirar con escepticismo a quien te diga "
                "que esta vez es diferente. Dicho eso, esta vez "
                "realmente lo es.",
        "plano": "CLOSE_UP_YAGO",
        "pizarra": False,
        "clips_studio": [
            ("studio_yago_solo_v3", 0.0,  8.0),
            ("studio_yago_solo_v4", 8.0, 12.12),
        ],
        "overlays": [
            {"t_in": 0.0, "t_out": 12.12, "type": "name_tag",
             "position": "TOP_RIGHT",
             "data": {"name": "YAGO", "color": "#4DB8FF"}},
        ],
    },
    # ── 4.3 Maria 3 factores · 33.61s · 2 clips Maria + pizarra ────
    {
        "id": "4.3", "section": "BLOQUE_1",
        "tc_in": 142.360, "tc_out": 175.970,
        "speaker": "MARIA", "tono": "tecnico",
        "text": "La diferencia es una convergencia de tres factores "
                "que nunca antes habían coincidido al mismo tiempo. "
                "Primero, potencia de cómputo: las ge pe us, unidades "
                "de procesamiento gráfico, actuales son miles de veces "
                "más potentes que las de los años 90. Segundo, datos "
                "masivos: internet generó cantidades de texto, "
                "comportamiento e imágenes que hace veinte años eran "
                "inimaginables. Y tercero, un salto arquitectónico "
                "concreto: la llegada de los Transformers, o "
                "arquitectura de atención, en 2017 con el paper, o "
                "artículo científico, \"Attention is All You Need\".",
        "plano": "TWO_SHOT_M_ACTIVE",
        "pizarra": True, "pizarra_t_in": 2.0,
        "clips_studio": [
            ("studio_maria_solo_v1_rev", 0.0, 17.0),
            ("studio_maria_solo_v4_rev", 17.0, 33.61),
        ],
        "clips_pip": [
            ("studio_two_m_active_v1",    2.0, 12.4),
            ("studio_two_m_active_v2_rev", 12.4, 22.8),
            ("studio_two_m_active_v3_rev", 22.8, 33.61),
        ],
        "overlays": [
            {"t_in": 0.0, "t_out": 33.61, "type": "name_tag",
             "position": "TOP_RIGHT",
             "data": {"name": "MARIA", "color": "#F5C400"}},
            {"t_in": 2.0, "t_out": 33.61, "type": "hierarchy_diagram",
             "position": "TOP_CENTER",
             "data": {"title": "3 FACTORES",
                      "items": ["CÓMPUTO", "DATOS", "ARQUITECTURA"]}},
            {"t_in": 9.0,  "t_out": 33.61, "type": "stat_card",
             "position": "MID_LEFT",
             "data": {"label": "1. CÓMPUTO", "value": "GPUs",
                      "subtitle": "miles× años 90", "color": "#F5C400"}},
            {"t_in": 16.0, "t_out": 33.61, "type": "stat_card",
             "position": "MID_CENTER",
             "data": {"label": "2. DATOS", "value": "20×",
                      "subtitle": "internet · 20 años", "color": "#F5C400"}},
            {"t_in": 24.0, "t_out": 33.61, "type": "stat_card",
             "position": "MID_RIGHT",
             "data": {"label": "3. ARQUITECT.", "value": "2017",
                      "subtitle": "Transformers", "color": "#F5C400"}},
            {"t_in": 28.0, "t_out": 33.61, "type": "regulation_alert",
             "position": "BOTTOM_LEFT",
             "data": {"title": "PAPER 2017",
                      "text": "Attention is All You Need"}},
        ],
    },
    # ── 4.4 Yago Transformers · 23.06s · 3 clips Yago ──────────
    {
        "id": "4.4", "section": "BLOQUE_1",
        "tc_in": 181.820, "tc_out": 204.880,
        "speaker": "YAGO", "tono": "tecnico",
        "text": "Ese paper resolvió el problema que había bloqueado "
                "todos los modelos anteriores: procesar texto de forma "
                "paralela y capturar relaciones entre palabras muy "
                "separadas dentro de un mismo documento. Gracias a "
                "esa arquitectura, desde 2020 tenemos los grandes "
                "modelos de lenguaje que hoy todo el mundo conoce. "
                "Sin los Transformers, el salto de la I.A. generativa "
                "no habría existido.",
        "plano": "CLOSE_UP_YAGO",
        "pizarra": False,
        "clips_studio": [
            ("studio_yago_solo_v1_rev",  0.0,  9.0),
            ("studio_yago_solo_v2_rev",  9.0, 17.0),
            ("studio_yago_solo_v4_rev", 17.0, 23.06),
        ],
        "overlays": [
            {"t_in": 0.0, "t_out": 23.06, "type": "name_tag",
             "position": "TOP_RIGHT",
             "data": {"name": "YAGO", "color": "#4DB8FF"}},
        ],
    },
    # ── 4.5 Maria aceleracion · 28.14s · 2 clips Maria, sin pizarra ──
    {
        "id": "4.5", "section": "BLOQUE_1",
        "tc_in": 203.540, "tc_out": 231.680,
        "speaker": "MARIA", "tono": "enfatico",
        "text": "Y la aceleración desde entonces no paró ni un "
                "trimestre. En 2022 llegó ChatGPT con los primeros "
                "cien millones de usuarios en dos meses, batiendo "
                "todos los récords de adopción tecnológica de la "
                "historia. En 2023 y 2024, los grandes laboratorios "
                "compitiendo abiertamente en capacidades. En 2026, "
                "el debate ya no es si adoptar I.A., sino qué hacer "
                "con el 70% del código que muchos equipos ya generan "
                "con ayuda de modelos.",
        "plano": "TWO_SHOT_M_ACTIVE",
        "pizarra": False,
        "clips_studio": [
            ("studio_maria_solo_v2_rev", 0.0, 14.0),
            ("studio_maria_solo_v3_rev", 14.0, 28.14),
        ],
        "overlays": [
            {"t_in": 0.0, "t_out": 28.14, "type": "name_tag",
             "position": "TOP_RIGHT",
             "data": {"name": "MARIA", "color": "#F5C400"}},
            {"t_in": 6.0, "t_out": 20.0, "type": "warning_badge",
             "position": "TOP_CENTER",
             "data": {"label": "RÉCORD · 100M USUARIOS EN 2 MESES",
                      "color": "#F5C400"}},
        ],
    },
    # ── 5.1 Yago jerarquia · 34.00s · 4 clips Yago + pizarra ────
    {
        "id": "5.1", "section": "BLOQUE_2",
        "tc_in": 232.940, "tc_out": 266.940,
        "speaker": "YAGO", "tono": "didactico",
        "text": "Necesitamos el mapa de taxonomía, porque nada genera "
                "más confusión en este campo que usar los mismos "
                "términos para cosas distintas. La I.A. es el campo "
                "más amplio. Dentro está el machine learning, o "
                "aprendizaje automático, que aprende patrones de datos. "
                "Dentro del machine learning está el deep learning, o "
                "aprendizaje profundo, con redes neuronales profundas. "
                "Y dentro del deep learning están los ele ele emes, "
                "grandes modelos de lenguaje. ChatGPT no es I.A. a "
                "secas: es la capa más específica de una jerarquía "
                "de cuatro niveles.",
        "plano": "TWO_SHOT_Y_ACTIVE",
        "pizarra": True, "pizarra_t_in": 4.0,
        "clips_studio": [
            ("studio_two_y_active_v1_rev",   0.0,  8.0),
            ("studio_yago_solo_v3",          8.0, 17.0),
            ("studio_yago_solo_v1",         17.0, 25.5),
            ("studio_two_y_active_v4",      25.5, 34.0),
        ],
        "clips_pip": [
            ("studio_yago_solo_v2",         4.0, 14.4),
            ("studio_yago_solo_v4",        14.4, 24.8),
            ("studio_two_y_active_v2_rev", 24.8, 34.0),
        ],
        "overlays": [
            {"t_in": 0.0, "t_out": 34.0, "type": "name_tag",
             "position": "TOP_RIGHT",
             "data": {"name": "YAGO", "color": "#4DB8FF"}},
            {"t_in": 4.0, "t_out": 34.0, "type": "hierarchy_diagram",
             "position": "MID_CENTER",
             "data": {"title": "Taxonomía IA",
                      "items": ["IA", "ML", "DL", "LLMs"]}},
            {"t_in": 11.0, "t_out": 18.0, "type": "stat_card",
             "position": "MID_LEFT",
             "data": {"label": "ML", "value": "patrones",
                      "subtitle": "aprendizaje automático",
                      "color": "#888888"}},
            {"t_in": 18.0, "t_out": 34.0, "type": "stat_card",
             "position": "MID_LEFT",
             "data": {"label": "DL", "value": "redes",
                      "subtitle": "neuronales profundas",
                      "color": "#888888"}},
            {"t_in": 24.0, "t_out": 34.0, "type": "stat_card",
             "position": "MID_RIGHT",
             "data": {"label": "LLMs", "value": "GPT-4",
                      "subtitle": "Claude · Gemini", "color": "#F5C400"}},
            {"t_in": 30.0, "t_out": 34.0, "type": "warning_badge",
             "position": "TOP_CENTER",
             "data": {"label": "4 NIVELES · NO sinónimos",
                      "color": "#CC2200"}},
        ],
    },
    # ── 5.2 Maria LinkedIn meme · 14.07s · 1 clip Maria solo ──
    {
        "id": "5.2", "section": "BLOQUE_2",
        "tc_in": 266.460, "tc_out": 280.530,
        "speaker": "MARIA", "tono": "ironico",
        "text": "Lo cual no impide que en LinkedIn todo el mundo use "
                "los cuatro términos como si fueran exactamente lo "
                "mismo. Pero a partir de hoy tú ya no lo harás. Eso "
                "ya es ventaja competitiva inmediata.",
        "plano": "CLOSE_UP_MARIA",
        "pizarra": False,
        "clips_studio": [
            ("studio_maria_solo_v4", 0.0, 14.07),
        ],
        "overlays": [
            {"t_in": 0.0, "t_out": 14.07, "type": "name_tag",
             "position": "TOP_RIGHT",
             "data": {"name": "MARIA", "color": "#F5C400"}},
        ],
    },
    # ── 5.3 Yago estrecha vs general · 29.70s · 3 clips + pizarra ──
    {
        "id": "5.3", "section": "BLOQUE_2",
        "tc_in": 277.700, "tc_out": 307.400,
        "speaker": "YAGO", "tono": "didactico",
        "text": "Otra distinción clave: I.A. estrecha frente a I.A. "
                "general. Toda la I.A. que existe hoy, sin excepción, "
                "es I.A. estrecha. Sistemas extraordinariamente "
                "potentes dentro de su dominio específico, pero "
                "incapaces de generalizar fuera de él. Un modelo que "
                "genera imágenes no conduce un coche. Un chatbot que "
                "escribe código no diagnostica una radiografía. La "
                "I.A. general, esa que razona en cualquier dominio "
                "como lo haría un humano, sigue siendo un horizonte "
                "teórico sin fecha de llegada.",
        "plano": "TWO_SHOT_Y_ACTIVE",
        "pizarra": True, "pizarra_t_in": 4.0,
        "clips_studio": [
            ("studio_two_y_active_v3",       0.0, 10.0),
            ("studio_two_y_active_v5",      10.0, 20.0),
            ("studio_yago_solo_v2_rev",     20.0, 29.70),
        ],
        "clips_pip": [
            ("studio_yago_solo_v4_rev",      4.0, 14.4),
            ("studio_two_y_active_v1",      14.4, 24.8),
            ("studio_two_y_active_v4_rev",  24.8, 29.70),
        ],
        "overlays": [
            {"t_in": 0.0, "t_out": 29.70, "type": "name_tag",
             "position": "TOP_RIGHT",
             "data": {"name": "YAGO", "color": "#4DB8FF"}},
            {"t_in": 4.0, "t_out": 12.0, "type": "two_column_compare",
             "position": "MID_CENTER",
             "data": {"left_title": "IA ESTRECHA",
                      "right_title": "IA GENERAL",
                      "left_items":  [],
                      "right_items": []}},
            {"t_in": 12.0, "t_out": 29.70, "type": "stat_card",
             "position": "MID_LEFT",
             "data": {"label": "ESTRECHA", "value": "100%",
                      "subtitle": "de la IA hoy", "color": "#4DB8FF"}},
            {"t_in": 19.0, "t_out": 29.70, "type": "stat_card",
             "position": "MID_RIGHT",
             "data": {"label": "GENERAL", "value": "?",
                      "subtitle": "horizonte teórico",
                      "color": "#888888"}},
            {"t_in": 25.0, "t_out": 29.70, "type": "regulation_alert",
             "position": "BOTTOM_LEFT",
             "data": {"title": "AGI",
                      "text": "sin fecha de llegada"}},
        ],
    },
]


# ── CONSTRUCCION scene_track + scene_timeline ────────────────────

def build_scene_track(interventions: list[dict]) -> list[dict]:
    """Cada intervencion -> 1+ track segments.
    - Si studio puro: un seg studio por cada clips_studio
    - Si pizarra: pre-pizarra studio segs + pizarra segs (uno por cada clips_pip)
    """
    track = []
    for iv in interventions:
        tc_in = float(iv["tc_in"])
        tc_out = float(iv["tc_out"])
        plano = iv.get("plano", "ESTABLISHING")

        if plano == "BLACK" or not iv.get("clips_studio"):
            # Blank
            track.append({
                "start": tc_in, "end": tc_out, "type": "blank",
                "speaker": iv.get("speaker", ""),
                "section": iv.get("section", ""),
                "plano": plano,
                "iv_id": iv["id"],
            })
            continue

        if iv.get("pizarra") and iv.get("clips_pip"):
            piz_t_in = float(iv["pizarra_t_in"])
            piz_abs_in = tc_in + piz_t_in
            # Pre-pizarra: studio segs cuyo scene_t_out <= piz_t_in
            pre_segs = []
            mid_seg = None
            post_segs = []
            for slug, s_in, s_out in iv["clips_studio"]:
                abs_in = tc_in + s_in
                abs_out = tc_in + s_out
                if abs_out <= piz_abs_in + 0.01:
                    pre_segs.append((slug, abs_in, abs_out))
                elif abs_in >= piz_abs_in - 0.01:
                    post_segs.append((slug, abs_in, abs_out))
                else:
                    # Cross-boundary: split
                    pre_segs.append((slug, abs_in, piz_abs_in))
                    post_segs.append((slug, piz_abs_in, abs_out))
            for slug, a, b in pre_segs:
                track.append({
                    "start": a, "end": b, "type": "studio",
                    "source": _clip(slug),
                    "clip_slug": slug,
                    "speaker": iv["speaker"], "section": iv["section"],
                    "plano": plano, "iv_id": iv["id"],
                })
            # Pizarra segs: uno por cada PIP clip
            for slug, s_in, s_out in iv["clips_pip"]:
                abs_in = tc_in + s_in
                abs_out = tc_in + s_out
                track.append({
                    "start": abs_in, "end": abs_out, "type": "pizarra",
                    "pip_source": _clip(slug),
                    "pip_clip_slug": slug,
                    "speaker": iv["speaker"], "section": iv["section"],
                    "plano": plano, "iv_id": iv["id"],
                })
        else:
            # Studio puro: cada clip un seg
            for slug, s_in, s_out in iv["clips_studio"]:
                track.append({
                    "start": tc_in + s_in, "end": tc_in + s_out,
                    "type": "studio",
                    "source": _clip(slug),
                    "clip_slug": slug,
                    "speaker": iv["speaker"], "section": iv["section"],
                    "plano": plano, "iv_id": iv["id"],
                })

    track.sort(key=lambda s: s["start"])
    # Sanidad: redondear a ms
    for s in track:
        s["start"] = round(s["start"], 3)
        s["end"] = round(s["end"], 3)
    return track


def build_scene_timeline(interventions: list[dict]) -> dict:
    """Cada intervencion = 1 escena con sus overlays absolutos."""
    scenes = []
    for iv in interventions:
        tc_in = float(iv["tc_in"])
        tc_out = float(iv["tc_out"])
        ovs = []
        for o in iv.get("overlays", []):
            ovs.append({
                "type":     o["type"],
                "position": o["position"],
                "data":     o["data"],
                "start":    round(tc_in + o["t_in"], 3),
                "end":      round(tc_in + o["t_out"], 3),
            })
        scenes.append({
            "start":      tc_in, "end": tc_out,
            "section":    iv.get("section", ""),
            "speaker":    iv.get("speaker", ""),
            "background": "industrial_grid",
            "text":       iv.get("text", ""),
            "tones":      [iv.get("tono", "")] if iv.get("tono") else [],
            "plano":      iv.get("plano", ""),
            "overlays":   ovs,
            "stickers":   [],
            "_v6_handcrafted": True,
        })
    return {"background": "industrial_grid", "scenes": scenes}


# ── RENDER ───────────────────────────────────────────────────────

def main():
    log = get_logger("render_5min_v6", log_file=PROJECT / "maquinaria_pesada_pipeline" / "outputs" / "logs" / "v6_render.log")
    pipe_root = PROJECT / "maquinaria_pesada_pipeline"
    config = validate_project_config(pipe_root / "project_config.json")
    output_folder = Path(config["assets"]["output_folder"])
    episode_id = config["episode_defaults"].get("episode_id", "EP-MOD000")

    log.info("=" * 60)
    log.info(f"  RENDER v6 · 5min · {episode_id}")
    log.info("=" * 60)

    # 1) Whisper (cache)
    log.info("[1/7] Whisper cache...")
    transcription = transcribe_episode(
        config["assets"]["episode_audio"], output_folder,
        model_size="medium", force=False,
    )

    # 2) Content (cache)
    log.info("[2/7] Content cache...")
    content = extract_content(
        config["assets"]["episode_script"],
        config["assets"].get("episode_pdf"),
        output_folder, force=False,
    )

    # 3) Audio analyzer (cache)
    log.info("[3/7] Audio cache...")
    audio_structure = analyze_episode_audio(
        config["assets"]["episode_audio"],
        config["assets"].get("intro_video"),
        output_folder, force=False,
    )

    # 4) Build v6 scene_timeline + scene_track
    log.info("[4/7] Build v6 scene_timeline + scene_track...")
    timeline = build_scene_timeline(INTERVENTIONS)
    track = build_scene_track(INTERVENTIONS)
    (output_folder / "scene_timeline.json").write_text(
        json.dumps(timeline, indent=2, ensure_ascii=False),
        encoding="utf-8")
    (output_folder / "scene_track.json").write_text(
        json.dumps(track, indent=2, ensure_ascii=False),
        encoding="utf-8")
    log.info(f"  scenes={len(timeline['scenes'])}  track_segs={len(track)}")

    # 5) Render frames PNG (preview 310s para cubrir 5 min completos)
    log.info("[5/7] Render frames PNG (preview 310s)...")
    frames_index = render_frames(
        timeline, transcription, config, output_folder,
        preview_seconds=310, force=True,
    )

    # 6) SRT
    log.info("[6/7] SRT...")
    base_name = derive_video_basename(config["assets"].get("episode_audio"), episode_id)
    base_name = base_name + "_v6"
    videos_folder = config["assets"].get("videos_folder")
    srt_path = generate_srt(
        transcription, content, output_folder, episode_id,
        force=True, videos_folder=videos_folder,
        base_name=base_name, audio_structure=audio_structure,
    )

    # 7) Compose
    log.info("[7/7] Compose...")
    final = compose_video(
        config, frames_index,
        config["assets"]["episode_audio"], srt_path,
        output_folder, episode_id, preview=True,
        audio_structure=audio_structure,
        scene_track=track,
    )
    log.info("=" * 60)
    log.info(f"  DONE · {final}")
    log.info("=" * 60)
    return 0


if __name__ == "__main__":
    # Bitácora diaria centralizada (logs/run/). Localiza daylog.py subiendo
    # directorios; si fallara, el script sigue con un nullcontext de respaldo.
    import sys as _sys
    from pathlib import Path as _Path
    for _p in _Path(__file__).resolve().parents:
        if (_p / "daylog.py").exists():
            if str(_p) not in _sys.path:
                _sys.path.insert(0, str(_p))
            break
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script=_Path(__file__).name, params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        raise SystemExit(main())
