from __future__ import annotations

from cockpit.connectors.base import Field_, PipelineConnector, register


@register
class EstadoProyecto(PipelineConnector):
    id = "estado_proyecto"
    label = "Estado del proyecto"
    icon = "📊"
    description = "Reporta progreso (PDFs → Guiones → Audio → Video) por módulo."
    script = "estado_proyecto.py"
    fields = [
        Field_("--codex", "Mostrar comandos pendientes para Codex", kind="bool"),
        Field_("--pendiente", "Filtrar incompletos", kind="bool"),
        Field_("--assets", "Verificar archivos multimedia", kind="bool"),
    ]
