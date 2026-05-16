from __future__ import annotations

from cockpit.connectors.base import ServiceConnector, register


@register
class ElevenLabsService(ServiceConnector):
    id = "elevenlabs"
    label = "ElevenLabs"
    description = "Síntesis TTS de voces IAGO y MARIA (eleven_v3)."
    env_keys = ("ELEVENLABS_API_KEY",)
    # Voces (PODCAST_MASTER_SPEC.md):
    #   IAGO  CdAqYBLnsNjmTqYgD5Ha  · stability 0.65 · speed 1.20
    #   MARIA gD1IexrzCvsXPHUuT0s3  · stability 0.68 · speed 1.20
    # Modelo eleven_v3 · post_speed_multiplier 1.10
