"""Cockpit theme — refined editorial dark with a CAT-yellow accent.

The previous theme leaned hard into a brutalist, all-uppercase industrial look
(Oswald + Barlow Condensed, sharp 2px borders, mandatory CAPS on every
heading). It made the app feel shouty and dense. This module replaces that
with a calmer, more editorial dark theme:

    - Inter for UI + display (multiple weights, normal-case).
    - JetBrains Mono for code, metrics and tabular numbers.
    - Softer panels (#13171D / #1A1F27), thin 1px borders, 10px radius.
    - CAT yellow stays as the only accent, but used sparingly.
    - Mayor leading, padding and rhythm — el contenido respira.

Public API kept stable (`inject_theme`, `render_logo`, `COLORS`) so the 17
pages and helpers don't need to change to pick up the new look.
"""
from __future__ import annotations

COLORS = {
    "bg":          "#0B0D10",   # base canvas (warm-tinted near-black)
    "panel":       "#13171D",   # default surface
    "panel_2":     "#1A1F27",   # raised surface (hover, modal)
    "border":      "#262C36",   # subtle dividers
    "border_str":  "#353D49",   # active / focused dividers
    "text":        "#E8EAED",   # primary text
    "text_dim":    "#A0A6AE",   # secondary text
    "text_mute":   "#6E7480",   # tertiary / metadata
    "primary":     "#F2C53D",   # CAT yellow (softened a touch)
    "primary_dk":  "#D7A91F",
    "primary_sft": "rgba(242,197,61,0.14)",
    "iago":        "#60A5FA",   # speaker blue
    "maria":       "#F2C53D",   # speaker yellow
    "ok":          "#4ADE80",
    "warn":        "#F59E0B",
    "alert":       "#EF4444",
    "info":        "#60A5FA",
}


_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --mp-bg:        #0B0D10;
    --mp-panel:     #13171D;
    --mp-panel-2:   #1A1F27;
    --mp-border:    #262C36;
    --mp-border-str:#353D49;
    --mp-text:      #E8EAED;
    --mp-text-dim:  #A0A6AE;
    --mp-text-mute: #6E7480;
    --mp-primary:   #F2C53D;
    --mp-primary-dk:#D7A91F;
    --mp-primary-sft: rgba(242,197,61,0.14);
    --mp-iago:      #60A5FA;
    --mp-maria:     #F2C53D;
    --mp-ok:        #4ADE80;
    --mp-warn:      #F59E0B;
    --mp-alert:     #EF4444;
    --mp-info:      #60A5FA;
    --mp-radius:    10px;
    --mp-radius-sm: 6px;
    --mp-shadow-sm: 0 1px 2px rgba(0,0,0,0.4);
    --mp-shadow-md: 0 6px 24px rgba(0,0,0,0.45);
}

/* ============================ TYPOGRAPHY ============================ */
html, body, [class*="css"], .stApp, .main, .block-container,
section[data-testid="stSidebar"], .stMarkdown, .stMarkdown p, label, button,
input, textarea, select {
    font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif !important;
    font-feature-settings: "cv02","cv03","cv04","cv11";
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

.stMarkdown, .stMarkdown p, .stApp p {
    color: var(--mp-text);
    font-size: 0.97rem;
    line-height: 1.6;
}

h1, h2, h3, h4, h5, h6,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
    color: var(--mp-text);
    font-weight: 600 !important;
    letter-spacing: -0.01em;
    line-height: 1.25;
    text-transform: none !important;
}

h1, .stMarkdown h1 {
    font-size: 1.9rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
    margin: 0.2rem 0 0.6rem 0 !important;
}
h2, .stMarkdown h2 {
    font-size: 1.35rem !important;
    margin-top: 1.6rem !important;
    margin-bottom: 0.55rem !important;
}
h3, .stMarkdown h3 {
    font-size: 1.1rem !important;
    color: var(--mp-text);
    margin-top: 1.1rem !important;
    margin-bottom: 0.4rem !important;
}
h4, .stMarkdown h4 { font-size: 0.97rem !important; color: var(--mp-text-dim); }

/* Code, métricas, tabular numbers */
code, pre, kbd, samp,
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace !important;
    font-variant-numeric: tabular-nums;
}

code:not(pre code) {
    background: var(--mp-panel-2);
    border: 1px solid var(--mp-border);
    border-radius: var(--mp-radius-sm);
    padding: 1px 6px;
    font-size: 0.86em;
    color: var(--mp-primary);
}

/* Captions: softer, tracked uppercase — used as eyebrows */
[data-testid="stCaptionContainer"], .stCaption, .stApp small {
    color: var(--mp-text-mute) !important;
    font-size: 0.81rem !important;
    line-height: 1.5;
    letter-spacing: 0.01em;
    text-transform: none;
}

/* ============================ LAYOUT ============================ */
.block-container {
    padding-top: 2.2rem !important;
    padding-bottom: 4rem !important;
    max-width: 1320px;
}

/* ============================ SIDEBAR ============================ */
section[data-testid="stSidebar"] {
    background: #0E1115;
    border-right: 1px solid var(--mp-border);
}
section[data-testid="stSidebar"] .block-container { padding-top: 1.2rem !important; }

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--mp-text-mute) !important;
    font-weight: 600 !important;
    margin: 1.1rem 0 0.45rem 0 !important;
    border: none !important;
    padding: 0 !important;
}
section[data-testid="stSidebar"] hr {
    border: none !important;
    height: 1px !important;
    background: var(--mp-border) !important;
    margin: 0.6rem 0 !important;
}

/* st.navigation links — calmer than default */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
    border-radius: var(--mp-radius-sm) !important;
    padding: 6px 10px !important;
    color: var(--mp-text-dim) !important;
    transition: background 0.12s ease, color 0.12s ease;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {
    background: var(--mp-panel) !important;
    color: var(--mp-text) !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {
    background: var(--mp-primary-sft) !important;
    color: var(--mp-primary) !important;
    font-weight: 600 !important;
}

/* ============================ BUTTONS ============================ */
.stButton > button,
[data-testid="stFormSubmitButton"] > button,
.stDownloadButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
    border: 1px solid var(--mp-border) !important;
    border-radius: var(--mp-radius) !important;
    background: var(--mp-panel) !important;
    color: var(--mp-text) !important;
    padding: 0.45rem 0.95rem !important;
    transition: background 0.14s ease, border-color 0.14s ease, color 0.14s ease, transform 0.05s ease;
    box-shadow: var(--mp-shadow-sm);
}
.stButton > button:hover,
.stDownloadButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    border-color: var(--mp-border-str) !important;
    background: var(--mp-panel-2) !important;
    color: var(--mp-text) !important;
}
.stButton > button:active { transform: translateY(1px); }

.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button[kind="primary"],
.stDownloadButton > button[kind="primary"] {
    background: var(--mp-primary) !important;
    color: #0B0D10 !important;
    border-color: var(--mp-primary-dk) !important;
    font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--mp-primary-dk) !important;
    color: #0B0D10 !important;
}

/* ============================ CONTAINERS / CARDS ============================ */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid var(--mp-border) !important;
    border-radius: var(--mp-radius) !important;
    background: var(--mp-panel) !important;
    box-shadow: var(--mp-shadow-sm);
    padding: 4px;
}

/* ============================ EXPANDERS ============================ */
[data-testid="stExpander"] {
    border: 1px solid var(--mp-border) !important;
    border-radius: var(--mp-radius) !important;
    background: var(--mp-panel) !important;
    box-shadow: var(--mp-shadow-sm);
}
[data-testid="stExpander"] summary {
    font-weight: 500;
    color: var(--mp-text) !important;
    padding: 0.65rem 0.9rem !important;
}
[data-testid="stExpander"] summary:hover { color: var(--mp-primary) !important; }
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    padding: 0.4rem 0.9rem 0.9rem 0.9rem !important;
}

/* ============================ INPUTS ============================ */
input, textarea, select,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea,
[data-baseweb="select"] > div {
    background: var(--mp-panel) !important;
    border: 1px solid var(--mp-border) !important;
    color: var(--mp-text) !important;
    border-radius: var(--mp-radius-sm) !important;
    font-size: 0.92rem !important;
}
input:focus, textarea:focus, select:focus,
[data-baseweb="input"]:focus-within, [data-baseweb="select"]:focus-within {
    border-color: var(--mp-primary) !important;
    box-shadow: 0 0 0 3px var(--mp-primary-sft) !important;
    outline: none !important;
}

/* ============================ DATAFRAME / TABLES ============================ */
[data-testid="stDataFrame"] {
    border: 1px solid var(--mp-border);
    border-radius: var(--mp-radius);
    overflow: hidden;
}

/* ============================ CODE BLOCKS ============================ */
.stCode, [data-testid="stCodeBlock"] {
    border: 1px solid var(--mp-border) !important;
    border-radius: var(--mp-radius) !important;
    background: #07090C !important;
}
.stCode pre, [data-testid="stCodeBlock"] pre {
    color: var(--mp-text) !important;
    font-size: 0.85rem !important;
    line-height: 1.55 !important;
    padding: 0.9rem 1rem !important;
}

/* ============================ ALERTS ============================ */
[data-testid="stAlert"] {
    border-radius: var(--mp-radius) !important;
    border: 1px solid var(--mp-border) !important;
    border-left: 3px solid var(--mp-primary) !important;
    background: var(--mp-panel) !important;
    padding: 0.7rem 0.9rem !important;
    box-shadow: var(--mp-shadow-sm);
}
div[data-testid="stAlert"][class*="info"]    { border-left-color: var(--mp-info)  !important; }
div[data-testid="stAlert"][class*="success"] { border-left-color: var(--mp-ok)    !important; }
div[data-testid="stAlert"][class*="warning"] { border-left-color: var(--mp-warn)  !important; }
div[data-testid="stAlert"][class*="error"]   { border-left-color: var(--mp-alert) !important; }

/* ============================ METRICS ============================ */
[data-testid="stMetric"] {
    background: var(--mp-panel);
    border: 1px solid var(--mp-border);
    border-radius: var(--mp-radius);
    padding: 14px 18px;
    box-shadow: var(--mp-shadow-sm);
    transition: border-color 0.14s ease;
}
[data-testid="stMetric"]:hover { border-color: var(--mp-border-str); }
[data-testid="stMetricLabel"] {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--mp-text-mute) !important;
    font-size: 0.7rem !important;
    font-weight: 500 !important;
}
[data-testid="stMetricValue"] {
    color: var(--mp-text) !important;
    font-weight: 600 !important;
    font-size: 1.7rem !important;
    letter-spacing: -0.02em;
}
[data-testid="stMetricDelta"] {
    font-size: 0.82rem !important;
    color: var(--mp-text-dim) !important;
}

/* ============================ DIALOGS ============================ */
[role="dialog"] {
    background: var(--mp-panel) !important;
    border: 1px solid var(--mp-border-str) !important;
    border-radius: var(--mp-radius) !important;
    box-shadow: var(--mp-shadow-md);
}
[role="dialog"] h2,
[role="dialog"] h3 { color: var(--mp-text) !important; }

/* ============================ DIVIDERS ============================ */
hr {
    border: none !important;
    height: 1px !important;
    background: var(--mp-border) !important;
    margin: 1.4rem 0 !important;
}

/* ============================ TABS ============================ */
[data-testid="stTabs"] button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
    color: var(--mp-text-dim) !important;
    padding: 0.55rem 0.95rem !important;
}
[data-testid="stTabs"] button:hover { color: var(--mp-text) !important; }
[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--mp-text) !important;
    border-bottom: 2px solid var(--mp-primary) !important;
}
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid var(--mp-border) !important;
}

/* ============================ PROGRESS ============================ */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, var(--mp-primary-dk), var(--mp-primary)) !important;
    border-radius: 999px !important;
}
[data-testid="stProgressBar"] > div {
    background: var(--mp-panel-2) !important;
    border-radius: 999px !important;
    height: 8px !important;
}

/* ============================ LINKS ============================ */
a, a:visited {
    color: var(--mp-primary) !important;
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color 0.12s ease;
}
a:hover { border-bottom-color: var(--mp-primary); }

/* ============================ SCROLLBARS ============================ */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: var(--mp-border);
    border-radius: 999px;
    border: 2px solid var(--mp-bg);
}
::-webkit-scrollbar-thumb:hover { background: var(--mp-border-str); }

/* ============================ PAGE HEADER (componente) ============================ */
.mp-page-header {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 4px 0 18px 0;
    margin-bottom: 18px;
    border-bottom: 1px solid var(--mp-border);
}
.mp-page-header .mp-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    color: var(--mp-primary);
    font-weight: 600;
}
.mp-page-header .mp-eyebrow::before {
    content: "";
    display: inline-block;
    width: 14px;
    height: 1px;
    background: var(--mp-primary);
}
.mp-page-header h1 {
    margin: 0 !important;
    color: var(--mp-text);
    font-size: 2rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
}
.mp-page-header .mp-subtitle {
    color: var(--mp-text-dim);
    font-size: 1.02rem;
    margin: 0;
    line-height: 1.55;
    max-width: 78ch;
}

/* ============================ STAT CARD ============================ */
.mp-stat-card {
    background: var(--mp-panel);
    border: 1px solid var(--mp-border);
    border-radius: var(--mp-radius);
    padding: 14px 18px 16px 18px;
    box-shadow: var(--mp-shadow-sm);
    transition: border-color 0.14s ease, transform 0.14s ease;
    height: 100%;
}
.mp-stat-card:hover {
    border-color: var(--mp-border-str);
}
.mp-stat-card .mp-stat-label {
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--mp-text-mute);
    font-size: 0.7rem;
    font-weight: 500;
    margin: 0 0 6px 0;
}
.mp-stat-card .mp-stat-value {
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
    color: var(--mp-text);
    font-size: 1.8rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    line-height: 1.1;
}
.mp-stat-card .mp-stat-value.ok      { color: var(--mp-ok); }
.mp-stat-card .mp-stat-value.warn    { color: var(--mp-warn); }
.mp-stat-card .mp-stat-value.alert   { color: var(--mp-alert); }
.mp-stat-card .mp-stat-value.primary { color: var(--mp-primary); }
.mp-stat-card .mp-stat-hint {
    color: var(--mp-text-mute);
    font-size: 0.8rem;
    margin-top: 6px;
    line-height: 1.45;
}

/* ============================ STATUS PILL ============================ */
.mp-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 500;
    line-height: 1.4;
    border: 1px solid transparent;
    background: var(--mp-panel-2);
    color: var(--mp-text-dim);
}
.mp-pill::before {
    content: "";
    width: 6px; height: 6px; border-radius: 999px;
    background: currentColor;
    flex-shrink: 0;
}
.mp-pill.ok     { color: var(--mp-ok);      background: rgba(74,222,128,0.10); border-color: rgba(74,222,128,0.30); }
.mp-pill.warn   { color: var(--mp-warn);    background: rgba(245,158,11,0.10); border-color: rgba(245,158,11,0.30); }
.mp-pill.fail   { color: var(--mp-alert);   background: rgba(239,68,68,0.10);  border-color: rgba(239,68,68,0.30); }
.mp-pill.info   { color: var(--mp-info);    background: rgba(96,165,250,0.10); border-color: rgba(96,165,250,0.30); }
.mp-pill.primary{ color: var(--mp-primary); background: var(--mp-primary-sft);  border-color: rgba(242,197,61,0.30); }
.mp-pill.neutral{ color: var(--mp-text-dim); background: var(--mp-panel-2); border-color: var(--mp-border); }

/* ============================ SECTION HEADING ============================ */
.mp-section {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin: 1.8rem 0 1rem 0;
}
.mp-section .mp-section-title {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: var(--mp-text-mute);
    font-weight: 600;
}
.mp-section .mp-section-subtitle {
    color: var(--mp-text-dim);
    font-size: 0.92rem;
}

/* ============================ ROW (list item) ============================ */
.mp-row {
    display: grid;
    align-items: center;
    gap: 16px;
    padding: 14px 16px;
    border: 1px solid var(--mp-border);
    border-radius: var(--mp-radius);
    background: var(--mp-panel);
    box-shadow: var(--mp-shadow-sm);
    transition: border-color 0.14s ease, background 0.14s ease;
    margin-bottom: 8px;
}
.mp-row:hover { border-color: var(--mp-border-str); background: var(--mp-panel-2); }

/* ============================ EMPTY STATE ============================ */
.mp-empty {
    text-align: center;
    padding: 40px 20px;
    border: 1px dashed var(--mp-border);
    border-radius: var(--mp-radius);
    background: var(--mp-panel);
    color: var(--mp-text-dim);
}
.mp-empty .mp-empty-icon { font-size: 1.6rem; opacity: 0.6; margin-bottom: 8px; }
.mp-empty .mp-empty-title { font-weight: 600; color: var(--mp-text); margin-bottom: 4px; }
.mp-empty .mp-empty-hint { color: var(--mp-text-mute); font-size: 0.88rem; }

/* ============================ BREADCRUMBS ============================ */
.mp-crumbs {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    color: var(--mp-text-mute);
    margin: 0 0 12px 0;
    flex-wrap: wrap;
}
.mp-crumbs-sep { color: var(--mp-border-str); }
.mp-crumbs-link {
    color: var(--mp-text-dim);
}
.mp-crumbs-current {
    color: var(--mp-text);
    font-weight: 500;
}

/* ============================ CALLOUTS ============================ */
.mp-callout {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 14px;
    border-radius: var(--mp-radius);
    border: 1px solid var(--mp-border);
    background: var(--mp-panel);
    color: var(--mp-text-dim);
    font-size: 0.9rem;
    line-height: 1.5;
    margin: 8px 0;
}
.mp-callout .mp-callout-icon {
    flex-shrink: 0;
    font-size: 1rem;
    line-height: 1.45;
    color: var(--mp-text-mute);
}
.mp-callout-info    { border-left: 3px solid var(--mp-info);  }
.mp-callout-info    .mp-callout-icon { color: var(--mp-info); }
.mp-callout-tip     { border-left: 3px solid var(--mp-primary); }
.mp-callout-tip     .mp-callout-icon { color: var(--mp-primary); }
.mp-callout-warn    { border-left: 3px solid var(--mp-warn); }
.mp-callout-warn    .mp-callout-icon { color: var(--mp-warn); }
.mp-callout-success { border-left: 3px solid var(--mp-ok);   }
.mp-callout-success .mp-callout-icon { color: var(--mp-ok); }

/* ============================ ACTION BAR ============================ */
.mp-actionbar-title {
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-size: 0.74rem;
    color: var(--mp-text-mute);
    font-weight: 600;
    margin-bottom: 2px;
}

/* ============================ KEYBOARD HINT ============================ */
.mp-kbd-group { display: inline-flex; gap: 3px; align-items: center; }
.mp-kbd {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    padding: 1px 6px;
    border: 1px solid var(--mp-border);
    border-bottom-width: 2px;
    border-radius: var(--mp-radius-sm);
    background: var(--mp-panel-2);
    color: var(--mp-text-dim);
}

/* ============================ HELP DIALOG ============================ */
.mp-help-eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-size: 0.72rem;
    color: var(--mp-primary);
    font-weight: 600;
    margin-bottom: 4px;
}
.mp-help-title {
    color: var(--mp-text);
    font-size: 1.45rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    margin: 0 0 12px 0 !important;
}
.mp-help-summary {
    color: var(--mp-text-dim);
    line-height: 1.6;
    margin-bottom: 18px;
    font-size: 0.95rem;
    padding: 12px 14px;
    background: var(--mp-panel-2);
    border-left: 3px solid var(--mp-primary);
    border-radius: var(--mp-radius-sm);
}
.mp-help-section-title {
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-size: 0.72rem;
    color: var(--mp-text-mute);
    font-weight: 600;
    margin: 18px 0 6px 0;
    padding-bottom: 4px;
    border-bottom: 1px solid var(--mp-border);
}

/* ============================ TOAST / TOOLTIP / MISC ============================ */
[data-testid="stToast"] {
    background: var(--mp-panel-2) !important;
    border: 1px solid var(--mp-border-str) !important;
    border-radius: var(--mp-radius) !important;
}

/* Tighten Streamlit top header bar */
header[data-testid="stHeader"] {
    background: transparent !important;
    height: 0 !important;
}
</style>
"""


def inject_theme() -> None:
    """Inject the cockpit CSS into the current page.

    Call once per page, right after ``st.set_page_config()``. Idempotent —
    extra calls just add duplicate <style> tags (harmless).
    """
    import streamlit as st
    st.markdown(_CSS, unsafe_allow_html=True)


def render_logo() -> None:
    """Show the project logo in the sidebar (Streamlit ≥ 1.35)."""
    import streamlit as st

    from cockpit.core import paths

    logo_path = paths.logos_dir() / "logo sin fondo.png"
    if not logo_path.exists():
        for alt in ("logo metálico.png", "logo todo metalico.png", "logo fondo amarillo.png"):
            cand = paths.logos_dir() / alt
            if cand.exists():
                logo_path = cand
                break
        else:
            return

    try:
        st.logo(str(logo_path), size="large")
    except TypeError:
        try:
            st.logo(str(logo_path))
        except Exception:
            pass
    except Exception:
        pass
