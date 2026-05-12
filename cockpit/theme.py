"""Industrial CAT theme for the cockpit.

Cohesive dark + CAT yellow + steel-gray palette with angular industrial fonts.
Streamlit's native theming via .streamlit/config.toml handles the base palette;
this module injects additional CSS to override component styling and embed
Google Fonts.

Call ``inject_theme()`` from each page right after ``set_page_config()`` and
*before* calling ``render_status_sidebar()``.
"""
from __future__ import annotations

# ---- Color constants (Python-side, exposed for code that needs them) ---

COLORS = {
    "bg":         "#0D0D0D",   # carbón
    "panel":      "#1A1A1A",   # acero oscuro
    "panel_2":    "#262626",   # acero medio
    "border":     "#3A3A3A",   # divisores
    "text":       "#F2F2F2",   # off-white
    "text_dim":   "#A8A8A8",   # acero claro
    "primary":    "#F5C400",   # CAT yellow
    "primary_dk": "#D4A800",   # CAT yellow hover
    "iago":       "#4DB8FF",   # azul eléctrico (speaker)
    "maria":      "#F5C400",   # amarillo (speaker)
    "alert":      "#CC2200",   # rojo alerta
    "ok":         "#00B894",   # verde OK
    "warn":       "#E87211",   # naranja peligro
}

# ---- CSS payload -------------------------------------------------------

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Barlow+Condensed:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
    --mp-bg:        #0D0D0D;
    --mp-panel:     #1A1A1A;
    --mp-panel-2:   #262626;
    --mp-border:    #3A3A3A;
    --mp-text:      #F2F2F2;
    --mp-text-dim:  #A8A8A8;
    --mp-primary:   #F5C400;
    --mp-primary-dk:#D4A800;
    --mp-iago:      #4DB8FF;
    --mp-maria:     #F5C400;
    --mp-alert:     #CC2200;
    --mp-ok:        #00B894;
    --mp-warn:      #E87211;
}

/* ============================ TIPOGRAFÍA ============================ */
html, body, [class*="css"], .stApp, .main, .block-container,
section[data-testid="stSidebar"] {
    font-family: 'Barlow Condensed', system-ui, -apple-system, sans-serif !important;
    font-size: 1.02rem;
    letter-spacing: 0.01em;
}

h1, h2, h3, h4, h5, h6,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
    font-family: 'Oswald', 'Barlow Condensed', sans-serif !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--mp-text);
}

/* H1 con barra amarilla a la izquierda — bandera de obra */
h1, .stMarkdown h1 {
    border-left: 6px solid var(--mp-primary);
    padding-left: 14px;
    margin-bottom: 0.6rem !important;
}

/* Code, métricas, números: monospace técnico */
code, pre, kbd, samp,
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', 'Consolas', monospace !important;
}

/* Captions más sutiles, en mayúsculas para sensación HUD */
[data-testid="stCaptionContainer"], .stCaption, small {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.78rem !important;
    color: var(--mp-text-dim) !important;
}

/* ============================ SIDEBAR ============================ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F0F0F 0%, #161616 100%);
    border-right: 2px solid var(--mp-primary);
}
section[data-testid="stSidebar"] h3 {
    color: var(--mp-primary) !important;
    border-left: 4px solid var(--mp-primary);
    padding-left: 10px;
    margin-bottom: 12px !important;
}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: var(--mp-text-dim) !important;
}
section[data-testid="stSidebar"] hr {
    border-color: var(--mp-border) !important;
}

/* ============================ BOTONES ============================ */
.stButton > button,
[data-testid="stFormSubmitButton"] > button {
    font-family: 'Oswald', sans-serif !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border: 1px solid var(--mp-border);
    border-radius: 2px;
    background: var(--mp-panel-2);
    color: var(--mp-text);
    transition: all 0.12s ease;
}
.stButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    border-color: var(--mp-primary) !important;
    color: var(--mp-primary) !important;
    background: var(--mp-panel) !important;
    box-shadow: 0 0 0 1px var(--mp-primary) inset;
}
.stButton > button:focus,
.stButton > button:active {
    background: var(--mp-primary) !important;
    color: #0D0D0D !important;
    border-color: var(--mp-primary) !important;
}

/* Botón "primary" tipo CAT: amarillo lleno */
.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button[kind="primary"] {
    background: var(--mp-primary) !important;
    color: #0D0D0D !important;
    border-color: var(--mp-primary-dk) !important;
}

/* ============================ CONTAINERS BORDED ============================ */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid var(--mp-border) !important;
    border-radius: 2px !important;
    background: var(--mp-panel) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4);
}

/* ============================ EXPANDERS ============================ */
[data-testid="stExpander"] {
    border: 1px solid var(--mp-border) !important;
    border-radius: 2px !important;
    background: var(--mp-panel) !important;
}
[data-testid="stExpander"] summary {
    font-family: 'Oswald', sans-serif !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: 600;
    color: var(--mp-text) !important;
}
[data-testid="stExpander"] summary:hover {
    color: var(--mp-primary) !important;
}

/* ============================ INPUTS ============================ */
input, textarea, select,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea,
[data-baseweb="select"] > div {
    background: var(--mp-panel) !important;
    border: 1px solid var(--mp-border) !important;
    color: var(--mp-text) !important;
    border-radius: 2px !important;
}
input:focus, textarea:focus, select:focus {
    border-color: var(--mp-primary) !important;
    box-shadow: 0 0 0 1px var(--mp-primary) inset !important;
}

/* ============================ CHECKBOX / TOGGLE ============================ */
[data-testid="stCheckbox"] label,
[data-testid="stToggle"] label {
    font-family: 'Barlow Condensed', sans-serif !important;
}

/* ============================ DATAFRAME / TABLA ============================ */
[data-testid="stDataFrame"] {
    border: 1px solid var(--mp-border);
    border-radius: 2px;
}

/* ============================ CODE / LOG BLOCKS ============================ */
.stCode, [data-testid="stCodeBlock"] {
    border: 1px solid var(--mp-border) !important;
    border-radius: 2px !important;
    background: #050505 !important;
}
.stCode pre, [data-testid="stCodeBlock"] pre {
    color: var(--mp-text) !important;
}

/* ============================ ALERTS / INFO BOXES ============================ */
[data-testid="stAlert"] {
    border-radius: 2px !important;
    border-left: 4px solid var(--mp-primary) !important;
    background: var(--mp-panel) !important;
}

/* Info: izquierda azul Iago */
.stAlert[data-baseweb="notification"] [data-testid="stAlertContentInfo"],
div[data-testid="stAlert"][class*="info"] {
    border-left-color: var(--mp-iago) !important;
}

/* Success: izquierda verde OK */
div[data-testid="stAlert"][class*="success"] {
    border-left-color: var(--mp-ok) !important;
}

/* Warning: izquierda naranja peligro */
div[data-testid="stAlert"][class*="warning"] {
    border-left-color: var(--mp-warn) !important;
}

/* Error: izquierda roja alerta */
div[data-testid="stAlert"][class*="error"] {
    border-left-color: var(--mp-alert) !important;
}

/* ============================ METRICS ============================ */
[data-testid="stMetric"] {
    background: var(--mp-panel);
    border: 1px solid var(--mp-border);
    border-left: 4px solid var(--mp-primary);
    border-radius: 2px;
    padding: 10px 14px;
}
[data-testid="stMetricLabel"] {
    font-family: 'Oswald', sans-serif !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--mp-text-dim) !important;
    font-size: 0.72rem !important;
}
[data-testid="stMetricValue"] {
    color: var(--mp-primary) !important;
    font-weight: 600 !important;
}

/* ============================ DIALOGOS / MODALES ============================ */
[role="dialog"] {
    background: var(--mp-bg) !important;
    border: 1px solid var(--mp-primary) !important;
    border-radius: 2px !important;
}
[role="dialog"] h2,
[role="dialog"] h3 {
    color: var(--mp-primary) !important;
}

/* ============================ DIVIDERS ============================ */
hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, var(--mp-primary), transparent 60%) !important;
    margin: 1.2rem 0 !important;
}

/* ============================ TABS ============================ */
[data-testid="stTabs"] button {
    font-family: 'Oswald', sans-serif !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--mp-primary) !important;
    border-bottom: 3px solid var(--mp-primary) !important;
}

/* ============================ TÍTULO PRINCIPAL ============================ */
.stApp [data-testid="stMarkdownContainer"] h1:first-child {
    text-transform: uppercase;
    background: linear-gradient(90deg, var(--mp-text) 0%, var(--mp-text) 70%, var(--mp-primary) 100%);
    -webkit-background-clip: text;
    background-clip: text;
}

/* ============================ STICKY BAR (futuro, placeholder) ============================ */
.mp-sticky-bar {
    position: sticky;
    top: 0;
    z-index: 999;
    background: linear-gradient(180deg, var(--mp-bg) 0%, rgba(13,13,13,0.92) 100%);
    backdrop-filter: blur(6px);
    border-bottom: 1px solid var(--mp-primary);
    padding: 8px 0;
}

/* ============================ SCROLLBARS (Webkit) ============================ */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--mp-panel); }
::-webkit-scrollbar-thumb {
    background: var(--mp-border);
    border-radius: 0;
}
::-webkit-scrollbar-thumb:hover { background: var(--mp-primary); }

/* ============================ MISC ============================ */
a, a:visited {
    color: var(--mp-primary) !important;
    text-decoration: none;
    border-bottom: 1px dotted var(--mp-primary);
}
a:hover { border-bottom-style: solid; }
</style>
"""


def inject_theme() -> None:
    """Inject the industrial CAT CSS into the page.

    Call once per page, right after ``st.set_page_config()``. Idempotent —
    multiple calls only add (harmless) duplicate <style> blocks.
    """
    import streamlit as st
    st.markdown(_CSS, unsafe_allow_html=True)


def render_logo() -> None:
    """Show the project logo in the sidebar via st.logo (Streamlit ≥ 1.35).

    Falls back to a markdown title if st.logo is unavailable or the file
    can't be found.
    """
    import streamlit as st
    from cockpit.core import paths

    logo_path = paths.logos_dir() / "logo sin fondo.png"
    if not logo_path.exists():
        # Fallback: alternative logos
        for alt in ("logo metálico.png", "logo todo metalico.png", "logo fondo amarillo.png"):
            cand = paths.logos_dir() / alt
            if cand.exists():
                logo_path = cand
                break
        else:
            return

    try:
        # st.logo signature varies across versions; size kwarg added in 1.36.
        st.logo(str(logo_path), size="large")
    except TypeError:
        try:
            st.logo(str(logo_path))
        except Exception:
            pass
    except Exception:
        pass
