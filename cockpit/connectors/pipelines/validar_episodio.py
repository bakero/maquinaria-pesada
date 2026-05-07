from __future__ import annotations

from cockpit.connectors.base import Field_, PipelineConnector, register


@register
class ValidarEpisodio(PipelineConnector):
    id = "validar_episodio"
    label = "Validar episodio"
    icon = "✅"
    description = "Comprueba MP3, duración, log, errores, bloques y reproducibilidad."
    script = "validar_episodio.py"
    fields = [
        Field_("--ep", "Código de episodio", required=True),
        Field_("--guion", "Guion (.txt)", kind="path", required=True),
        Field_("--mp3", "MP3 final (opcional)", kind="path"),
        Field_("--log", "Log de producción (opcional)", kind="path"),
        Field_("--min", "Duración mínima (min)", kind="int", default=14),
        Field_("--max", "Duración máxima (min)", kind="int", default=17),
    ]
