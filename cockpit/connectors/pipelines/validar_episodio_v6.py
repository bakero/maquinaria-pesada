from __future__ import annotations

from cockpit.connectors.base import Field_, PipelineConnector, register


@register
class ValidarEpisodioV6(PipelineConnector):
    id = "validar_episodio_v6"
    label = "Validar episodio (v6 — M/T/S)"
    icon = "🧪"
    description = (
        "Validador estructural unificado para episodios M / T / S. "
        "Comprueba el guion contra el spec correspondiente, voz, "
        "longitud y nomenclatura. Complemento de validar_episodio.py "
        "(que valida el MP3 + duración + reproducibilidad)."
    )
    script = "validar_episodio_v6.py"
    fields = [
        Field_(
            "--kind",
            "Tipo",
            kind="select",
            options=["M", "T", "S"],
            required=True,
            help="M = módulo · T = sub-tema · S = especial.",
        ),
        Field_(
            "--ep",
            "ID episodio",
            required=True,
            placeholder="M3 · M3_T2 · S1_RAG",
        ),
        Field_(
            "--guion",
            "Guion (.txt)",
            kind="path",
            required=True,
            placeholder="Guiones/M3_T2_atencion.txt",
        ),
        Field_(
            "--repo-root",
            "Repo root",
            default=".",
            help="Por defecto el cwd del cockpit.",
        ),
        Field_(
            "--s-number",
            "Número S (solo S)",
            kind="int",
            help="Solo aplica si --kind=S.",
        ),
        Field_(
            "--voice",
            "Voz (solo S)",
            kind="select",
            options=["", "IAGO", "MARIA"],
            help="Voz dominante si es un especial S.",
        ),
        Field_(
            "--filename",
            "Nombre fichero (solo S)",
            help="Override del nombre esperado para S.",
        ),
    ]
