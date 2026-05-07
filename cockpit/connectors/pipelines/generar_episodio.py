from __future__ import annotations

from cockpit.connectors.base import Field_, PipelineConnector, register


@register
class GenerarEpisodio(PipelineConnector):
    id = "generar_episodio"
    label = "Generar episodio (audio)"
    icon = "🎧"
    description = "Sintetiza el audio del episodio con ElevenLabs y monta el MP3 final."
    script = "generar_episodio_v2.py"
    fields = [
        Field_("--guion", "Guion (.txt)", kind="path", required=True,
               placeholder="Guiones/M3_T_ML_Clasico.txt"),
        Field_("--ep", "Código de episodio", required=True,
               placeholder="M3_E_ML_Clasico"),
        Field_("--spec", "Spec maestro (opcional)", kind="path",
               default="PODCAST_MASTER_SPEC.md"),
        Field_("--solo-bloque", "Regenerar solo bloque N", kind="int"),
        Field_("--solo-speaker", "Regenerar solo speaker",
               kind="select", options=["", "IAGO", "MARIA"]),
        Field_("--solo-montar", "Solo montar (no resintetizar)", kind="bool"),
        Field_("--generar-musica", "Generar música de fondo", kind="bool"),
    ]
