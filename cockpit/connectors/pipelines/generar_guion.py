from __future__ import annotations

from cockpit.connectors.base import Field_, PipelineConnector, register


@register
class GenerarGuion(PipelineConnector):
    id = "generar_guion"
    label = "Generar guion M"
    icon = "📝"
    description = (
        "Genera un guion .txt de episodio M (módulo) con Anthropic Claude "
        "(Sonnet 4.5). Episodios T → generar_guion_t.py. Ver GENERACION.md."
    )
    script = "generar_guion.py"
    # Flags alineados con el argparse real de generar_guion.py.
    fields = [
        Field_("--modulo", "Módulo (0-14)", kind="int", required=True,
               placeholder="6"),
        Field_("--pdf", "PDF RESUMEN del módulo", kind="path", required=True,
               help="Ruta relativa al repo, p.ej. PDFs/resumenes/RESUMEN_M6_Ingenieria_Prompts.pdf"),
        Field_("--nombre", "Nombre del módulo (archivo)",
               placeholder="Ingenieria_de_Prompts",
               help="Opcional. Si se omite se infiere del nombre del PDF."),
        Field_("--spec", "Ruta al spec M", default="PODCAST_M_SPEC.md"),
        Field_("--max-intentos", "Max intentos", kind="int", default=3),
    ]
