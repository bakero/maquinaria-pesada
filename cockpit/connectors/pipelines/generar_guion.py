from __future__ import annotations

from cockpit.connectors.base import Field_, PipelineConnector, register


@register
class GenerarGuion(PipelineConnector):
    id = "generar_guion"
    label = "Generar guion"
    icon = "📝"
    description = "Genera un guion .txt desde un PDF fuente con OpenAI."
    script = "generar_guion.py"
    fields = [
        Field_("--pdf", "PDF fuente", kind="path", required=True,
               help="Ruta relativa al repo, p.ej. PDFs/RESUMEN_M3_Machine_Learning_Clasico.pdf"),
        Field_("--ep", "Código de episodio", required=True,
               placeholder="M3_T_ML_Clasico"),
        Field_("--modulo", "Módulo", placeholder="M3"),
        Field_("--tema", "Tema (título)"),
        Field_("--objetivo", "Objetivo del episodio"),
        Field_("--duracion-min", "Duración (min)", kind="int", default=15),
        Field_("--master-pdf", "PDF maestro (opcional)", kind="path"),
        Field_("--contexto-file", "Fichero de contexto adicional", kind="path"),
        Field_("--estudios", "Estudios/citas a incluir"),
        Field_("--aplicacion-empresarial", "Caso de aplicación empresarial"),
        Field_("--modelo", "Modelo OpenAI", default="gpt-4.1",
               kind="select", options=["gpt-4.1", "gpt-4.1-mini", "gpt-4o", "gpt-4o-mini"]),
        Field_("--modelo-review", "Modelo revisión", default="gpt-4.1-mini",
               kind="select", options=["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"]),
        Field_("--token-budget", "Token budget", kind="int"),
        Field_("--max-attempts", "Max intentos", kind="int", default=3),
    ]
