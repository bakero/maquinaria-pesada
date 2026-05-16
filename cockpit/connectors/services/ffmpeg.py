from __future__ import annotations

import shutil

from cockpit.connectors.base import ServiceConnector, Status, register


@register
class FfmpegService(ServiceConnector):
    id = "ffmpeg"
    label = "ffmpeg"
    description = "Post-procesado de audio (ajuste de velocidad, montaje)."
    env_keys = ()

    def status(self) -> Status:
        path = shutil.which("ffmpeg")
        if path:
            return Status(ok=True, detail=path)
        return Status(ok=False, detail="ffmpeg no encontrado en PATH")
