"""Página Rendimiento: métricas de Spotify / iVoox / LinkedIn."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit.connectors.analytics import Unavailable  # noqa: E402
from cockpit.connectors.analytics.ivoox import IvooxAnalytics  # noqa: E402
from cockpit.connectors.analytics.linkedin import LinkedInAnalytics  # noqa: E402
from cockpit.connectors.analytics.spotify import SpotifyAnalytics  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402
from cockpit.ui_components import page_header  # noqa: E402

st.set_page_config(page_title="Rendimiento", page_icon="📊", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()

page_header(
    "Rendimiento · métricas de publicaciones",
    eyebrow="Difusión",
    subtitle=(
        "Conectores a Spotify, iVoox y LinkedIn. Las credenciales viven en `.env`. "
        "Datos cacheados en `logs/analytics/<source>.json`."
    ),
    help_page_id="rendimiento",
)

sp = SpotifyAnalytics()
iv = IvooxAnalytics()
li = LinkedInAnalytics()

# ---- Estado conectores ---------------------------------------------------

st.subheader("Estado")
c1, c2, c3 = st.columns(3)
for col, conn in zip([c1, c2, c3], [sp, iv, li], strict=True):
    with col:
        ok = conn.is_configured()
        badge = "🟢" if ok else "🔴"
        st.markdown(f"### {badge} {conn.icon} {conn.label}")
        st.caption(conn.status_detail())

st.divider()

# ---- Spotify -------------------------------------------------------------

st.subheader("🎧 Spotify for Creators")
if not sp.is_configured():
    st.info(
        "Configura en `.env`: `SPOTIFY_SP_DC`, `SPOTIFY_SP_KEY`, `SPOTIFY_PODCAST_ID`. "
        "Ver `docs/integraciones/analytics.md` para obtener las cookies."
    )
else:
    win = st.slider("Ventana (días)", 7, 90, 30, key="sp_win")
    if st.button("Refrescar Spotify", key="sp_refresh"):
        try:
            show = sp.fetch_show(window_days=win)
            episodes = sp.fetch_episodes(window_days=win)
        except Unavailable as e:
            st.error(str(e))
        except Exception as e:  # noqa: BLE001
            st.error(f"Error: {type(e).__name__}: {e}")
        else:
            if show:
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Seguidores", f"{show.followers:,}")
                mc2.metric("Nuevos", f"+{show.new_followers:,}")
                mc3.metric(f"Streams ({win}d)", f"{show.total_streams_window:,}")
            if episodes:
                import pandas as pd
                df = pd.DataFrame([{
                    "Episodio": e.title,
                    "Fecha": e.publish_date,
                    "Streams": e.streams,
                    "Listeners": e.listeners,
                    "Completion": f"{(e.completion_rate or 0):.0%}",
                } for e in episodes])
                st.dataframe(df, use_container_width=True)

st.divider()

# ---- iVoox ---------------------------------------------------------------

st.subheader("🟧 iVoox (RSS + CSV)")
if not iv.is_configured():
    st.info(
        "Define `IVOOX_RSS_URL` en `.env` con la URL del feed RSS de tu podcast. "
        "Para métricas reales (escuchas, retención), sube el CSV exportado desde la Zona de Creadores."
    )
else:
    if st.button("Refrescar feed iVoox", key="iv_refresh"):
        try:
            info = iv.fetch_feed_info()
            episodes = iv.fetch_episodes(window_days=365)
        except Unavailable as e:
            st.error(str(e))
        except Exception as e:  # noqa: BLE001
            st.error(f"Error parseando RSS: {type(e).__name__}: {e}")
        else:
            st.caption(f"**{info.title}** — {info.author} ({info.language})")
            if episodes:
                import pandas as pd
                df = pd.DataFrame([{
                    "Episodio": e.title,
                    "Publicado": e.publish_date,
                    "Duración (s)": e.duration_seconds or 0,
                    "URL": e.url,
                } for e in episodes])
                st.dataframe(df, use_container_width=True)

st.markdown("**Importar CSV de iVoox Podcasters** (escuchas, retención, demografía)")
csv_file = st.file_uploader("Sube `estadisticas.csv`", type=["csv"], key="iv_csv")
if csv_file is not None:
    try:
        df = IvooxAnalytics.load_stats_csv(csv_file)
        st.dataframe(df, use_container_width=True)
        st.caption(f"{len(df)} filas · {len(df.columns)} columnas")
    except Unavailable as e:
        st.error(str(e))
    except Exception as e:  # noqa: BLE001
        st.error(f"No se pudo parsear el CSV: {e}")

st.divider()

# ---- LinkedIn ------------------------------------------------------------

st.subheader("💼 LinkedIn")
if not all(li._env.get(k) for k in li.ENV_KEYS):
    st.info(
        "Configura en `.env`: `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, "
        "`LINKEDIN_ORG_URN` (`urn:li:organization:<id>`). Luego completa el flujo OAuth."
    )
else:
    redirect = st.text_input(
        "Redirect URI (debe coincidir con la app en developer.linkedin.com)",
        value="http://localhost:8501/oauth/callback",
        key="li_redirect",
    )
    scopes = ["r_organization_social", "rw_organization_admin", "r_organization_admin"]
    auth_url = li.authorization_url(redirect, scopes, state="mp-cockpit")
    st.markdown(f"**1.** [Autorizar app en LinkedIn]({auth_url})")
    code = st.text_input("**2.** Pega aquí el `code` del callback", key="li_code")
    if st.button("**3.** Intercambiar code → token", key="li_exchange") and code:
        try:
            li.exchange_code(code.strip(), redirect)
            st.success("Token guardado en `logs/analytics/linkedin_tokens.json`")
        except Exception as e:  # noqa: BLE001
            st.error(f"Falló el intercambio: {type(e).__name__}: {e}")

    if li.is_configured() and st.button("Refrescar métricas LinkedIn", key="li_refresh"):
        try:
            shares = li.fetch_share_statistics()
            followers = li.fetch_follower_statistics()
            posts = li.fetch_posts(window_days=90)
        except Unavailable as e:
            st.error(str(e))
        except Exception as e:  # noqa: BLE001
            st.error(f"Error API: {type(e).__name__}: {e}")
        else:
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Impresiones", f"{shares.get('impressionCount', 0):,}")
            mc2.metric("Clicks", f"{shares.get('clickCount', 0):,}")
            mc3.metric("Likes", f"{shares.get('likeCount', 0):,}")
            mc4.metric("Engagement", f"{(shares.get('engagement') or 0):.2%}")
            if posts:
                import pandas as pd
                df = pd.DataFrame([{
                    "Publicado": p.published_at,
                    "Texto": p.text_preview,
                    "Impresiones": p.impressions,
                    "Clicks": p.clicks,
                    "Likes": p.likes,
                    "Comentarios": p.comments,
                    "Compartidos": p.shares,
                } for p in posts])
                st.dataframe(df, use_container_width=True)
            with st.expander("Followers (raw)"):
                st.json(followers)
