from __future__ import annotations

from cockpit.connectors.base import PipelineConnector, register


@register
class ProducePending(PipelineConnector):
    id = "produce_pending"
    label = "Producir pendientes (batch)"
    icon = "⚙️"
    description = (
        "Fan-out de generación: detecta TODOS los episodios con guion "
        "pero sin audio y los produce uno a uno con generar_episodio_v2. "
        "Útil para arrancar un módulo entero o recuperar tras un fallo "
        "masivo. Sin flags — escanea Guiones/ y produce lo que falte."
    )
    script = "produce_pending.py"
    fields = []
