from __future__ import annotations

import shutil

from cockpit.connectors.base import ServiceConnector, Status, register


@register
class CodexService(ServiceConnector):
    id = "codex"
    label = "OpenAI Codex CLI"
    description = "Ejecutor automático de pipelines (recibe los prompts generados)."
    env_keys = ("OPENAI_API_KEY",)

    def status(self) -> Status:
        path = shutil.which("codex") or shutil.which("codex.exe")
        if not path:
            return Status(ok=False, detail="binario `codex` no encontrado en PATH")
        return Status(ok=True, detail=path)
