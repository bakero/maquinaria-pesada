from __future__ import annotations

from cockpit.connectors.base import ServiceConnector, register


@register
class OpenAIService(ServiceConnector):
    id = "openai"
    label = "OpenAI"
    icon = "🤖"
    description = "Generación de guiones y revisión (gpt-4.1, gpt-4.1-mini)."
    env_keys = ("OPENAI_API_KEY",)
