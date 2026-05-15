from __future__ import annotations

from cockpit.connectors.base import PipelineConnector, register


@register
class DualDebate(PipelineConnector):
    id = "dual_debate"
    label = "Dual debate (Claude ↔ GPT)"
    icon = "💬"
    description = (
        "Debate colaborativo Claude (rondas 1 y 3) + GPT (rondas 2 y 4) "
        "sobre la estrategia del podcast. Requiere ANTHROPIC_API_KEY y "
        "OPENAI_API_KEY. Sin flags — pregunta hard-codeada en el script."
    )
    script = "dual_debate_maquinaria.py"
    fields = []
