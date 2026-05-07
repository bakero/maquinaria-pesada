from __future__ import annotations

import shutil

from cockpit.connectors.base import ServiceConnector, Status, register


@register
class FfmpegService(ServiceConnector):
    id = "ffmpeg"
    label = "ffmpeg"
    icon = "🎞️"
    description = "Post-procesado de audio (ajuste de velocidad, montaje)."
    env_keys = ()

    def status(self) -> Status:
        path = shutil.which("ffmpeg")
        if path:
            return Status(ok=True, detail=path)
        return Status(ok=False, detail="ffmpeg no encontrado en PATH")

    def render_config(self) -> None:
        import streamlit as st
        s = self.status()
        if s.ok:
            st.success(f"`ffmpeg` disponible en: `{s.detail}`")
        else:
            st.error(s.detail)
            st.caption("Instalar con: `winget install Gyan.FFmpeg`")
