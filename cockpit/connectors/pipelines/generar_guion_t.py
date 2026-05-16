from __future__ import annotations

from cockpit.connectors.base import Field_, PipelineConnector, register


@register
class GenerarGuionT(PipelineConnector):
    id = "generar_guion_t"
    label = "Generar guion T"
    icon = "📑"
    description = (
        "Genera un guion .txt de episodio T (tema) con Anthropic Claude. "
        "El PDF de entrada debe vivir en PDFs/temas/ con el patrón "
        "Mₙ_Tₖ_slug.pdf. Ver GENERACION.md."
    )
    script = "generar_guion_t.py"
    fields = [
        Field_(
            "--pdf",
            "PDF del tema",
            kind="path",
            required=True,
            placeholder="PDFs/temas/M1_T11_limitaciones_llms.pdf",
            help=(
                "Ruta al PDF de un sub-tema. El nombre debe ser "
                "Mₙ_Tₖ_slug.pdf — esa convención determina el ID del "
                "episodio resultante (M1_T11)."
            ),
        ),
        Field_(
            "--spec",
            "Spec T",
            default="PODCAST_T_SPEC.md",
            help="Spec con las reglas estructurales del formato T.",
        ),
        Field_(
            "--max-intentos",
            "Max intentos",
            kind="int",
            default=3,
            help="Reintentos si Claude devuelve un guion no-conforme.",
        ),
    ]
