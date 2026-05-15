"""Reglas de producción de audio comprobables sobre el texto del guion.

Reglas A.7 (Audio-Reglas) y el invariante de calidad TTS sintética (§2B de los
specs v6). Las comprobaciones que necesitan el MP3 final (duración, LUFS) viven
en `tts_validator.py`.

Cubre:
- Audio-Regla 1: números en palabras (dígitos en diálogo → soft-warn).
- Audio-Regla 2: longitud de intervención (reacción >15 palabras → hard-fail;
  intervención >200 palabras → soft-warn).
- Invariante TTS: frases largas (>32 palabras → soft-warn), demasiadas frases
  cortas seguidas (soft-warn), tecnicismos sin aterrizaje.
"""
from __future__ import annotations

import re

from validators.result import ValidationResult, fail, ok

# Marcadores que legitiman un número (años de papers/informes).
_PUBLICATION_MARKERS = (
    "paper", "informe", "estudio", "reporte", "publicacion", "publicación",
    "encuesta", "segun", "según", "lanzamiento", "mckinsey", "hugging face",
    "anthropic", "openai", "google", "meta", "gartner", "ibm", "idc",
    "lucid", "forrester", "stanford", "mit",
)


def _strip_tag(text: str) -> str:
    """Quita la etiqueta [tag] inicial de una intervención."""
    return re.sub(r"^\s*\[[^\]]+\]\s*", "", text).strip()


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])\s+", text.strip())
    return [p for p in parts if p.strip()]


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\wáéíóúñÁÉÍÓÚÑ]+\b", text))


def check_digits_in_speech(interventions: list[str]) -> ValidationResult:
    """Soft-warn si aparecen dígitos en el diálogo (Audio-Regla 1).

    Excepción: un dígito acompañado de un marcador de publicación en las 6
    palabras previas (el año de un paper puede ir en cifra).
    """
    offenders: list[dict] = []
    for idx, raw in enumerate(interventions):
        body = _strip_tag(raw)
        for m in re.finditer(r"\d+([.,]\d+)?", body):
            prev = body[max(0, m.start() - 60):m.start()].lower()
            prev_words = prev.split()[-6:]
            if any(any(mk in w for mk in _PUBLICATION_MARKERS)
                   for w in prev_words):
                continue
            if any(mk in prev for mk in _PUBLICATION_MARKERS):
                continue
            offenders.append({"index": idx, "match": m.group(0),
                              "text": body[:80]})
    if offenders:
        return fail(
            "audio_rule_digits_in_speech", "SOFT",
            f"{len(offenders)} número(s) en cifra en el diálogo "
            "(Audio-Regla 1: usar palabras)",
            offenders=offenders[:20],
        )
    return ok("audio_rule_digits_in_speech", "SOFT",
              "Sin dígitos sueltos en el diálogo")


def _looks_like_reaction(body: str) -> bool:
    """Heurística: la intervención parece una reacción-pregunta.

    Solo se consideran reacciones las intervenciones de ≤2 frases que son
    preguntas (empiezan con `¿` o terminan en `?`) o son una interjección
    explícita (empiezan con muletilla típica). Una afirmación normal de una
    sola frase larga es un statement, no una reacción.
    """
    stripped = body.strip()
    if not stripped:
        return False
    sentences = _split_sentences(stripped)
    if len(sentences) > 2:
        return False
    if stripped.startswith("¿") or "?" in stripped:
        return True
    interjection_starts = (
        "pues ", "pero ", "vale", "vaya", "uf", "ah,", "oh,", "eh,",
    )
    return stripped.lower().startswith(interjection_starts)


def check_reaction_length(interventions: list[str],
                          reaction_word_limit: int = 15) -> ValidationResult:
    """Hard-fail si una intervención que parece reacción/pregunta supera el
    límite de palabras.

    "Parece reacción" implica: ≤2 frases Y (es pregunta O empieza con
    muletilla típica). Una afirmación normal de 1 frase larga no se cuenta
    como reacción.
    """
    offenders: list[dict] = []
    for idx, raw in enumerate(interventions):
        body = _strip_tag(raw)
        if not _looks_like_reaction(body):
            continue
        wc = _word_count(body)
        if wc > reaction_word_limit:
            offenders.append({"index": idx, "words": wc, "text": body[:80]})
    if offenders:
        return fail(
            "audio_rule_reaction_length", "HARD",
            f"{len(offenders)} reacción/pregunta superan "
            f"{reaction_word_limit} palabras",
            offenders=offenders,
        )
    return ok("audio_rule_reaction_length", "HARD",
              "Reacciones dentro del límite de palabras")


def check_intervention_max_words(interventions: list[str],
                                 max_words: int = 200) -> ValidationResult:
    """Soft-warn si una intervención supera el máximo absoluto de palabras."""
    offenders: list[dict] = []
    for idx, raw in enumerate(interventions):
        wc = _word_count(_strip_tag(raw))
        if wc > max_words:
            offenders.append({"index": idx, "words": wc})
    if offenders:
        return fail(
            "audio_rule_intervention_over_max", "SOFT",
            f"{len(offenders)} intervención(es) superan {max_words} palabras",
            offenders=offenders,
        )
    return ok("audio_rule_intervention_over_max", "SOFT",
              f"Ninguna intervención supera {max_words} palabras")


def check_long_sentences(interventions: list[str],
                         max_words_per_sentence: int = 32) -> ValidationResult:
    """Soft-warn si hay frases más largas que el límite del invariante TTS."""
    offenders: list[dict] = []
    for idx, raw in enumerate(interventions):
        for sent in _split_sentences(_strip_tag(raw)):
            wc = _word_count(sent)
            if wc > max_words_per_sentence:
                offenders.append({"index": idx, "words": wc,
                                  "text": sent[:90]})
    if offenders:
        return fail(
            "tts_invariant_long_sentences", "SOFT",
            f"{len(offenders)} frase(s) superan {max_words_per_sentence} "
            "palabras (invariante TTS)",
            offenders=offenders[:20],
        )
    return ok("tts_invariant_long_sentences", "SOFT",
              f"Sin frases de más de {max_words_per_sentence} palabras")


def check_consecutive_short_sentences(
    interventions: list[str], max_consecutive: int = 3,
    short_threshold: int = 12,
) -> ValidationResult:
    """Soft-warn si hay demasiadas frases cortas seguidas (ping-pong mecánico)."""
    offenders: list[dict] = []
    for idx, raw in enumerate(interventions):
        run = 0
        for sent in _split_sentences(_strip_tag(raw)):
            if _word_count(sent) < short_threshold:
                run += 1
                if run > max_consecutive:
                    offenders.append({"index": idx, "run": run})
                    break
            else:
                run = 0
    if offenders:
        return fail(
            "tts_invariant_consecutive_short_sentences", "SOFT",
            f"{len(offenders)} intervención(es) con más de {max_consecutive} "
            "frases cortas seguidas (invariante TTS)",
            offenders=offenders,
        )
    return ok("tts_invariant_consecutive_short_sentences", "SOFT",
              "Sin rachas de frases cortas excesivas")


def check_all(interventions: list[str], *,
              reaction_word_limit: int = 15,
              max_words: int = 200,
              max_words_per_sentence: int = 32,
              max_consecutive_short: int = 3) -> list[ValidationResult]:
    """Aplica todas las reglas de audio comprobables sobre texto."""
    return [
        check_digits_in_speech(interventions),
        check_reaction_length(interventions, reaction_word_limit),
        check_intervention_max_words(interventions, max_words),
        check_long_sentences(interventions, max_words_per_sentence),
        check_consecutive_short_sentences(interventions, max_consecutive_short),
    ]
