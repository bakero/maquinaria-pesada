"""Página Previsualizar: audio y vídeo desde la cockpit."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit.core import paths  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402
from cockpit.ui_components import page_header  # noqa: E402
from cockpit.ui_improve import render_improve_block  # noqa: E402

st.set_page_config(page_title="Previsualizar", page_icon="🎧", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()

page_header(
    "Previsualizar audio y vídeo",
    eyebrow="Contenido",
    subtitle="Player inline para audios y vídeos producidos. Útil para revisar antes de publicar.",
    help_page_id="previsualizar",
)

AUDIO_SUFFIXES = (".mp3", ".wav", ".m4a", ".ogg")
VIDEO_SUFFIXES = (".mp4", ".mov", ".mkv", ".webm")


def _collect(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        (p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in suffixes),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def _fmt_mtime(p: Path) -> str:
    import datetime as dt

    return dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")


tab_audio, tab_video = st.tabs(["🎧 Audio", "🎬 Vídeo"])

with tab_audio:
    audios = _collect(paths.episodios_dir(), AUDIO_SUFFIXES)
    st.caption(f"{len(audios)} ficheros en `{paths.episodios_dir()}`")
    if not audios:
        st.info("Sin audios todavía. Lanza `producir_episodio.py` desde *Generar Prompt*.")
    else:
        labels = {str(p.relative_to(paths.repo_root())): p for p in audios}
        sel = st.selectbox("Audio", list(labels.keys()), key="_audio_sel")
        path = labels[sel]
        size_mb = path.stat().st_size / 1_048_576
        st.caption(f"{size_mb:.1f} MB · modificado {_fmt_mtime(path)}")
        st.audio(str(path))

        render_improve_block(
            source=f"audio:{path.name}",
            context=(
                f"Audio MP3 generado por el pipeline. Fichero: {path.name}. "
                f"Tamaño: {size_mb:.1f} MB. La revisión es por descripción solo "
                "(no transcripción en este turno)."
            ),
            default_prompt=(
                "Asumiendo que es un episodio del podcast, sugiere 3 checks "
                "automáticos previos a publicar (loudness, silencios, intro/outro)."
            ),
            kind="improvement",
        )

with tab_video:
    videos = _collect(paths.videos_dir(), VIDEO_SUFFIXES)
    st.caption(f"{len(videos)} ficheros en `{paths.videos_dir()}`")
    if not videos:
        st.info("Sin vídeos todavía.")
    else:
        labels = {str(p.relative_to(paths.repo_root())): p for p in videos}
        sel = st.selectbox("Vídeo", list(labels.keys()), key="_video_sel")
        path = labels[sel]
        size_mb = path.stat().st_size / 1_048_576
        st.caption(f"{size_mb:.1f} MB · modificado {_fmt_mtime(path)}")
        st.video(str(path))

        render_improve_block(
            source=f"video:{path.name}",
            context=(
                f"Vídeo generado por el pipeline. Fichero: {path.name}. "
                f"Tamaño: {size_mb:.1f} MB."
            ),
            default_prompt=(
                "Sugiere 3 checks automáticos pre-publicación: bitrate mínimo, "
                "duración esperada vs guion, presencia de subtítulos."
            ),
            kind="improvement",
        )
