from __future__ import annotations

from cockpit.connectors.base import Field_, PipelineConnector, register


@register
class NormalizarGuiones(PipelineConnector):
    id = "normalizar_guiones"
    label = "Normalizar guiones (legacy)"
    icon = "🧹"
    description = (
        "⚠️ Utilidad LEGACY: convierte guiones del formato B (pre-v5) al "
        "formato A. NO ejecutar sobre guiones ya en formato v5 — el "
        "resultado sería rechazado por el validador. Solo úsalo para "
        "recuperar guiones de codex antiguo. Ver GENERACION.md."
    )
    script = "normalizar_guiones.py"
    fields = [
        Field_(
            "--file",
            "Archivo concreto (.txt)",
            help="Ruta relativa a Guiones/. Si se omite, procesa todos.",
            placeholder="M3_T_ML_Clasico.txt",
        ),
        Field_(
            "--dry-run",
            "Dry run (no escribir)",
            kind="bool",
            default=False,
            help="Muestra los cambios sin tocar nada.",
        ),
        Field_(
            "--all",
            "Procesar todos",
            kind="bool",
            default=False,
            help="Procesa todos los guiones de Guiones/.",
        ),
    ]
