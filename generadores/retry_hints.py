"""Hints de acción para retry feedback.

Cada entrada explica al modelo qué cambiar concretamente cuando una regla
de validación falla.

Filosofía v7:
- HARD: acción específica + ejemplo cuando ayuda a desambiguar.
- SOFT: sugerencia general dejando margen estilístico.
- 12 entradas consolidadas (antes 28). Variantes equivalentes fusionadas
  en una sola para mantener el feedback breve y accionable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Severity = Literal["HARD", "SOFT"]


@dataclass(frozen=True)
class RetryHint:
    rule_name: str
    severity: Severity
    action: str
    example: str | None = None

    def format(self) -> str:
        out = f"  ACCIÓN ({self.severity}): {self.action}"
        if self.example:
            out += f"\n  EJEMPLO: {self.example}"
        return out


HINTS: tuple[RetryHint, ...] = (
    RetryHint(
        rule_name="word_count",
        severity="HARD",
        action=(
            "Amplía bloques de desarrollo (BLOQUE_PANORAMA, BLOQUE_DESTACADO, "
            "BLOQUE_COMO, BLOQUE_CASOS o APLICACION_PRACTICA según el formato). "
            "Añade sub-mecanismos o casos completos; NO recortes nada existente. "
            "Apunta al medio del rango. Para Shorts: si <157 añade dos frases "
            "concretas antes del cierre canónico; si >198 recorta el ejemplo."
        ),
    ),
    RetryHint(
        rule_name="parity_opener",
        severity="HARD",
        action=(
            "Cambia el HOOK para que lo abra el speaker correcto por paridad. "
            "El opener pronuncia HOOK + aviso de IA (los dos juntos)."
        ),
    ),
    RetryHint(
        rule_name="canonical_phrases",
        severity="HARD",
        action=(
            "Las frases canónicas son literales (sin tildes en 'capitulo', "
            "sin signos extra). HOOK cierra con 'Esto es MaquinarIA Pesada. "
            "Arrancamos.'; CIERRE_CONCEPTOS abre con 'No te puedes ir de este "
            "capitulo sin haber entendido estos conceptos'; CIERRE_FINAL "
            "termina con la frase canónica completa. Shorts: 'Más sobre "
            "[tema] en el episodio T de MaquinarIA Pesada.'"
        ),
    ),
    RetryHint(
        rule_name="m_fuentes_count",
        severity="HARD",
        action=(
            "Cuenta los AÑOS DISTINTOS en BLOQUE_FUENTES: deben ser 3 o 4 "
            "(M) / exactamente 3 (T). Si te faltan, añade fuente con año "
            "nuevo. Si te sobran, elimina o reescribe años laterales como "
            "'hoy' / 'actualmente' (sin cifra de año)."
        ),
        example=(
            "Vaswani y otros, dos mil diecisiete. Lewis y otros, dos mil "
            "veinte. Stanford, dos mil veintitrés."
        ),
    ),
    RetryHint(
        rule_name="t_fuentes_count_exact_3",
        severity="HARD",
        action=(
            "BLOQUE_FUENTES debe tener EXACTAMENTE 3 fuentes con 3 AÑOS "
            "DISTINTOS. Cuenta los años antes de cerrar el bloque."
        ),
        example=(
            "Vaswani, dos mil diecisiete; Lewis, dos mil veinte; NIST AI RMF, "
            "dos mil veintitrés."
        ),
    ),
    RetryHint(
        rule_name="speaker_balance",
        severity="HARD",
        action=(
            "Recalcula palabras por speaker en el bloque señalado. Lider del "
            "bloque debe estar en el rango previsto (PANORAMA y LIMITES → "
            "Yago ≥65/55%; CASOS → Maria ≥60%; DESTACADO y COMO → 40-60%; "
            "APLICACION_PRACTICA → Maria 30-40%, Yago 60-70%). Sube al "
            "minoritario añadiendo un turno largo (80-120 palabras) o baja "
            "al mayoritario acortando uno largo suyo."
        ),
    ),
    RetryHint(
        rule_name="m_concepts_count",
        severity="HARD",
        action=(
            "CIERRE_CONCEPTOS debe tener 3-5 intervenciones totales (M) o "
            "EXACTAMENTE 3 (T). La PRIMERA combina la frase canónica de "
            "apertura con el primer concepto en UN ÚNICO bloque del opener "
            "— nunca la apertura sola en su propio bloque."
        ),
    ),
    RetryHint(
        rule_name="t_casos_company_count",
        severity="HARD",
        action=(
            "BLOQUE_CASOS necesita ≥2 empresas con nombre propio reconocible. "
            "Lista canónica: Harvey AI, Morgan Stanley, JPMorgan, IBM, "
            "Microsoft, Google, OpenAI, Anthropic, Meta, Lemonade, Zara, "
            "Nordea, BBVA, Santander, Telefonica, Netflix, Spotify, "
            "Salesforce, McKinsey, Gartner, Stanford, MIT."
        ),
    ),
    RetryHint(
        rule_name="saludo_format",
        severity="HARD",
        action=(
            "SALUDO_Y_PRESENTACION son 3 intervenciones SEPARADAS, una por "
            "línea: opener saluda → otro saluda → opener da el aviso de IA. "
            "El aviso contiene LITERALMENTE 'sistema automatico' y 'puede "
            "contener errores'."
        ),
    ),
    RetryHint(
        rule_name="s_hook_template",
        severity="HARD",
        action=(
            "El HOOK del Short debe encajar en UNA plantilla: H1 contradicción "
            "(empieza con 'no es / no son / aunque / incluso / a pesar de / "
            "puede inventar / nunca'), H2 número (cifra en palabras como "
            "primera frase), o H3 pregunta ('¿...?')."
        ),
    ),
    RetryHint(
        rule_name="pingpong",
        severity="SOFT",
        action=(
            "Anti-pingpong: en el bloque señalado el speaker de APOYO tiene "
            "demasiada presencia. Su ratio palabras-apoyo / palabras-líder "
            "debe quedar ≤ 0.33. Convierte sus turnos de desarrollo en "
            "reacciones breves de 5-12 palabras (pregunta corta específica "
            "al tema, no 'exactamente' / 'claro') o fusiona dos turnos suyos "
            "en uno corto."
        ),
    ),
    RetryHint(
        rule_name="tts_invariants",
        severity="SOFT",
        action=(
            "Reglas TTS: ninguna frase >32 palabras (pártelas con puntos); "
            "no más de 3 frases <12 palabras seguidas en un mismo turno "
            "(fusiónalas con 'y'/'porque' a medianas de 15-25 palabras); "
            "reacciones de la voz de apoyo ≤15 palabras; tag TTS de la "
            "lista cerrada: didactico, analitico, reflexivo, claro, "
            "explicativo, curioso, escéptico, enfático."
        ),
    ),
)


# Diccionario para lookup directo por nombre exacto (compat con base_generator).
HINTS_BY_NAME: dict[str, RetryHint] = {h.rule_name: h for h in HINTS}


def get_hint(rule_name: str) -> str | None:
    """Devuelve el texto formateado del hint o None si la regla no tiene hint
    específico. Mapeo de aliases (variantes equivalentes consolidadas):
    """
    # Aliases minimalistas: SOLO los grupos cuyas reglas no se beneficiaban
    # de hints específicos. Los `*_leader_*` y `s_word_count` se DEJAN sin
    # alias para que caigan al fallback granular en
    # base_generator._RULE_ACTION_HINTS (los granulares dan al modelo
    # cifras concretas — la consolidación regresionaba el feedback).
    aliases = {
        # Parity / IA warning siguen consolidados.
        "ia_warning": "parity_opener",
        # Canonical phrases variants — fraseo común sirve para los 4.
        "canonical_hook_closing": "canonical_phrases",
        "canonical_concepts_opening": "canonical_phrases",
        "canonical_final_closing": "canonical_phrases",
        "canonical_s_closing": "canonical_phrases",
        # TTS invariants — son reglas de pulido (SOFT), un hint común vale.
        "tts_invariant_long_sentences": "tts_invariants",
        "tts_invariant_consecutive_short_sentences": "tts_invariants",
        "tts_tags_allowed": "tts_invariants",
        "audio_rule_reaction_length": "tts_invariants",
        "audio_rule_intervention_over_max": "tts_invariants",
        "blacklist_interjection": "tts_invariants",
        "no_invented_surnames": "tts_invariants",
    }
    canonical = aliases.get(rule_name, rule_name)
    hint = HINTS_BY_NAME.get(canonical)
    return hint.format() if hint else None
