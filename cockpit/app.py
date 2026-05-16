"""Cockpit MaquinarIA Pesada — entry point.

Run: ``streamlit run cockpit/app.py``

La sidebar se construye con `st.navigation()` agrupando las páginas en seis
secciones lógicas para no saturar al usuario con 17 entradas planas.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the cockpit package is importable when run via `streamlit run cockpit/app.py`.
_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

import streamlit as st  # noqa: E402

from cockpit import connectors  # noqa: E402,F401  (auto-registers all)

st.set_page_config(
    page_title="MaquinarIA Pesada — Cockpit",
    page_icon="🎙️",
    layout="wide",
)


def _page(path: str, title: str, icon: str, **kwargs: object) -> st.Page:
    return st.Page(str(_HERE / path), title=title, icon=icon, **kwargs)


home = _page("home.py", "Inicio", "🎙️", default=True)

# Contenido — drill-down sobre lo generado.
master = _page("pages/0_🎓_Master.py", "Master", "🎓")
modulo = _page("pages/13_🎬_Modulo.py", "Módulo", "🎬")
episodio = _page("pages/14_📼_Episodio.py", "Episodio", "📼")
estado = _page("pages/1_📊_Estado.py", "Estado", "📊")
previsualizar = _page("pages/8_🎧_Previsualizar.py", "Previsualizar", "🎧")

# Producción — operación: lanzar pipelines y consultar logs.
generar_prompt = _page("pages/3_📝_Generar_Prompt.py", "Generar prompt", "📝")
fuentes = _page("pages/4_📚_Fuentes.py", "Fuentes", "📚")
logs = _page("pages/5_📜_Logs.py", "Logs", "📜")

# Coste IA — tracking económico.
tokens = _page("pages/7_💰_Tokens.py", "Tokens", "💰")
economics = _page("pages/11_💳_Economics.py", "Economics", "💳")
optimizar = _page("pages/10_🧠_Optimizar.py", "Optimizar", "🧠")

# Difusión — métricas post-publicación.
rendimiento = _page("pages/16_📊_Rendimiento.py", "Rendimiento", "📡")

# Sistema — arquitectura y configuración.
conectores = _page("pages/2_🔌_Conectores.py", "Conectores", "🔌")
api_keys = _page("pages/6_🔑_API_Keys.py", "API Keys", "🔑")
mapa = _page("pages/12_🗺️_Mapa.py", "Mapa", "🗺️")
pizarra = _page("pages/15_🎨_Pizarra.py", "Pizarra", "🎨")

# Asistente.
asistente = _page("pages/9_💬_Asistente.py", "Asistente", "💬")

nav = st.navigation(
    {
        "Inicio": [home],
        "🎓 Contenido": [master, modulo, episodio, estado, previsualizar],
        "🏭 Producción": [generar_prompt, fuentes, logs],
        "💸 Coste IA": [tokens, economics, optimizar],
        "📡 Difusión": [rendimiento],
        "⚙️ Sistema": [conectores, api_keys, mapa, pizarra],
        "🤖 Asistente": [asistente],
    }
)
nav.run()
