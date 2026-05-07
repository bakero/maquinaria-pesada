from __future__ import annotations

from cockpit.connectors.base import ServiceConnector, register


@register
class ElevenLabsService(ServiceConnector):
    id = "elevenlabs"
    label = "ElevenLabs"
    icon = "🎙️"
    description = "Síntesis TTS de voces IAGO y MARIA (eleven_v3)."
    env_keys = ("ELEVENLABS_API_KEY",)

    def render_config(self) -> None:
        import streamlit as st
        super().render_config()
        st.divider()
        st.write("**Voces configuradas (PODCAST_MASTER_SPEC.md):**")
        st.write("- IAGO: `CdAqYBLnsNjmTqYgD5Ha` — stability 0.65, speed 1.20")
        st.write("- MARIA: `gD1IexrzCvsXPHUuT0s3` — stability 0.68, speed 1.20")
        st.caption("Modelo: eleven_v3 · post_speed_multiplier 1.10")
