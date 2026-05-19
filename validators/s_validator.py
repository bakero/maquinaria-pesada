"""Validador específico de episodios S (Short) — spec v6.

S es diferente de M/T: una sola voz narradora (sin diálogo), texto neutro
sin atribución de speaker, 4 bloques internos opcionales (HOOK / DEFINICION /
EJEMPLO / APLICACION_GANCHO) que pueden ir como secciones `# X` o como un
único bloque de texto narrativo. Esta función acepta ambas formas.
"""
from __future__ import annotations

import re
from pathlib import Path

from validators.parser import count_words, parse_script
from validators.result import ValidationResult, fail, ok
from validators.shared import (
    blacklist,
    canonical_phrases,
    parity,
)

# Configuración v6
WORD_COUNT_MIN = 157
WORD_COUNT_MAX = 198

EXPECTED_INTERNAL_BLOCKS = (
    "HOOK", "DEFINICION", "EJEMPLO", "APLICACION_GANCHO",
)

# Plantillas de HOOK aceptables
HOOK_TEMPLATES = ("H1_contradiccion", "H2_numero", "H3_pregunta")

# Audio duration acceptable range (seconds)
AUDIO_DURATION_RANGE = (55.0, 95.0)


# Detecciones
DIALOGUE_RE = re.compile(r"^\s*(IAGO|MARIA|MARÍA)\s*:", re.MULTILINE)
TTS_TAG_RE = re.compile(r"\[[a-záéíóúñ_]+\]", re.IGNORECASE)
URL_RE = re.compile(r"https?://|www\.|punto\s+com", re.IGNORECASE)
PAPER_CITATION_RE = re.compile(
    r"[A-ZÁÉÍÓÚÑ][a-zñáéíóú]+\s+et\s+al\.?\s*,?\s*\d{4}"
    r"|[A-ZÁÉÍÓÚÑ][a-zñáéíóú]+\s+y\s+otros,?\s*\d{4}",
)


def _classify_hook(hook_text: str) -> str | None:
    """Devuelve la plantilla detectada (H1/H2/H3) o None."""
    t = hook_text.strip()
    if not t:
        return None
    if "¿" in t and "?" in t:
        return "H3_pregunta"
    # H2: contiene un número (porcentaje, año fuera de paper, o cifra)
    if re.search(r"\b\d+([.,]\d+)?\s*(%|por\s+ciento|millones|mil)?\b", t.lower()):
        return "H2_numero"
    # H1: contradicción → frase con marcador adversativo o de sorpresa.
    # Incluye modales que indican capacidad contraintuitiva ("puede inventar
    # con total seguridad"), concesivos ("aunque", "incluso", "a pesar de") y
    # los adversativos clásicos.
    h1_markers = (
        "pero", "sin embargo", "no es", "no son", "no lo", "no son",
        "aunque", "incluso", "a pesar de", "y eso", "y sin embargo",
        "y aún así", "y aun asi", "con total", "con absoluta",
        "puede inventar", "puede equivocarse", "no entienden",
        "nunca han", "jamás han", "jamas han",
    )
    low = t.lower()
    if any(a in low for a in h1_markers):
        return "H1_contradiccion"
    # H1 generalizado: arranque con "<sujeto> no <verbo>" o "no <verbo>".
    # Cubre "no inventan", "no aprenden", "no tienen", "no funcionan",
    # "no saben", "no recuerdan", etc., manteniendo la espontaneidad de
    # la afirmación contraintuitiva sin obligar a una lista cerrada.
    if re.match(r"^\s*(¡|¿)?[\wáéíóúñÁÉÍÓÚÑ\s,]{0,80}\bno\s+[a-záéíóúñ]+", low):
        return "H1_contradiccion"
    return None


def _extract_hook(text: str) -> str:
    """Si el guion S tiene `# HOOK`, devuelve esa sección; si no, la primera
    frase del texto narrativo (el HOOK del S dura 5-7s, ~12-18 palabras)."""
    parts = parse_script(text)
    hook = parts.section_text("HOOK")
    if hook:
        return hook
    sentences = re.split(r"(?<=[.!?…])\s+", text.strip())
    return sentences[0] if sentences else ""


def _strip_sections_headers(text: str) -> str:
    return re.sub(r"^#\s+[A-Z_]+\s*$", "", text, flags=re.MULTILINE)


def _full_narration(text: str) -> str:
    """Devuelve el texto narrado puro (sin tags ni cabeceras de sección)."""
    no_headers = _strip_sections_headers(text)
    return TTS_TAG_RE.sub("", no_headers).strip()


# ---- Reglas individuales ----------------------------------------------------


def check_word_count(text: str) -> ValidationResult:
    wc = count_words(_full_narration(text))
    if WORD_COUNT_MIN <= wc <= WORD_COUNT_MAX:
        return ok("s_word_count", "HARD",
                  f"Word count {wc} en [{WORD_COUNT_MIN}, {WORD_COUNT_MAX}]")
    return fail("s_word_count", "HARD",
                f"Word count {wc} fuera de [{WORD_COUNT_MIN}, {WORD_COUNT_MAX}]",
                count=wc)


def check_hook_template(text: str) -> ValidationResult:
    hook = _extract_hook(text)
    template = _classify_hook(hook)
    if template in HOOK_TEMPLATES:
        return ok("s_hook_template", "HARD",
                  f"HOOK encaja en plantilla {template}")
    return fail("s_hook_template", "HARD",
                "HOOK no encaja en ninguna plantilla H1/H2/H3 "
                "(contradicción, número o pregunta)")


def check_closing(text: str) -> ValidationResult:
    return canonical_phrases.check_s_closing(text)


def check_no_dialogue(text: str) -> ValidationResult:
    """Hard-fail si aparece formato de diálogo `IAGO:` o `MARIA:`."""
    if DIALOGUE_RE.search(text):
        return fail("s_no_dialogue", "HARD",
                    "El Short contiene formato de diálogo; debe ser narración única")
    return ok("s_no_dialogue", "HARD", "Sin diálogo: narración única correcta")


def check_no_tts_tags(text: str) -> ValidationResult:
    """Hard-fail si aparecen etiquetas TTS de tono `[tag]`."""
    body = _strip_sections_headers(text)
    if TTS_TAG_RE.search(body):
        return fail("s_no_tts_tags", "HARD",
                    "El Short contiene etiquetas TTS de tono (prohibidas)")
    return ok("s_no_tts_tags", "HARD", "Sin etiquetas TTS de tono")


def check_no_urls(text: str) -> ValidationResult:
    if URL_RE.search(text):
        return fail("s_no_urls_in_speech", "HARD",
                    "El Short contiene URLs en la narración")
    return ok("s_no_urls_in_speech", "HARD", "Sin URLs en la narración")


def check_no_paper_citations(text: str) -> ValidationResult:
    if PAPER_CITATION_RE.search(text):
        return fail("s_no_paper_citations_in_speech", "HARD",
                    "El Short cita un paper con autor y año en la narración")
    return ok("s_no_paper_citations_in_speech", "HARD",
              "Sin citas tipo paper en la narración")


def check_block_count(text: str) -> ValidationResult:
    """Hard-fail si hay más de 4 secciones internas con cabecera."""
    parts = parse_script(text)
    n = len(parts.section_order)
    if n <= 4:
        return ok("s_block_count", "HARD",
                  f"Secciones internas: {n} (≤4)")
    return fail("s_block_count", "HARD",
                f"El Short tiene {n} secciones internas (máximo 4)")


def check_filename(filename: str | None) -> ValidationResult:
    """Hard-fail si el nombre de archivo no encaja en `S{N}_nombre.mp3`."""
    if not filename:
        return ok("s_filename_format", "HARD",
                  "filename no proporcionado (skip)")
    name = Path(filename).name
    if re.match(r"^S\d+_[\w\-áéíóúñÁÉÍÓÚÑ]+\.mp3$", name):
        return ok("s_filename_format", "HARD",
                  f"filename '{name}' encaja en el patrón")
    return fail("s_filename_format", "HARD",
                f"filename '{name}' no encaja en S{{N}}_nombre.mp3",
                filename=name)


def check_voice_parity(s_number: int, voice: str) -> ValidationResult:
    """Hard-fail si la voz asignada no coincide con la paridad del número S."""
    expected = parity.opener_for(s_number)
    actual = (voice or "").upper()
    if actual == expected:
        return ok("s_voice_parity", "HARD",
                  f"S{s_number}: voz {expected} correcta por paridad")
    return fail("s_voice_parity", "HARD",
                f"S{s_number}: voz {actual or '?'} pero por paridad debe ser {expected}",
                expected=expected, actual=actual)


def check_blacklist_interjections(text: str) -> ValidationResult:
    """Hard-fail si el texto contiene una interjección de la lista negra."""
    return blacklist.check_interjections([text])


def check_brand_mention_only_in_closing(text: str) -> ValidationResult:
    """Soft-warn si 'MaquinarIA Pesada' aparece fuera del cierre."""
    matches = [m.start() for m in re.finditer(r"maquinaria\s+pesada", text,
                                              re.IGNORECASE)]
    if len(matches) <= 1:
        return ok("s_brand_only_in_closing", "SOFT",
                  "Marca mencionada como máximo una vez (en el cierre)")
    return fail("s_brand_only_in_closing", "SOFT",
                f"Marca aparece {len(matches)} veces; solo se permite en el cierre")


def check_internal_block_length(text: str,
                                 max_block_words: int = 60) -> ValidationResult:
    """Soft-warn si algún bloque interno supera el máximo de palabras."""
    parts = parse_script(text)
    if not parts.section_order:
        return ok("s_internal_block_length", "SOFT",
                  "Short sin secciones internas (texto narrativo único)")
    offenders = []
    for name in parts.section_order:
        wc = count_words(parts.section_text(name))
        if wc > max_block_words:
            offenders.append({"section": name, "words": wc})
    if offenders:
        return fail("s_internal_block_length", "SOFT",
                    f"{len(offenders)} bloque(s) interno(s) >60 palabras",
                    offenders=offenders)
    return ok("s_internal_block_length", "SOFT",
              "Bloques internos dentro del límite")


# ---- Validación post-TTS (delega en shared/tts_validator) -------------------


def validate_audio(audio_path) -> list[ValidationResult]:
    """Validaciones post-TTS específicas de S."""
    from validators.shared import tts_validator as tv
    return tv.check_all(
        audio_path,
        min_seconds=AUDIO_DURATION_RANGE[0],
        max_seconds=AUDIO_DURATION_RANGE[1],
        target_lufs=-14.0, lufs_tolerance=0.5,
        max_silence_s=2.0,
    )


# ---- Entrada principal ------------------------------------------------------


def validate(script_text: str, episode_id: str,
              s_number: int | None = None,
              voice: str | None = None,
              filename: str | None = None) -> list[ValidationResult]:
    """Aplica las 17 validaciones de guion del formato S (12 hard + 5 soft).

    Las 3 post-TTS y 3 de archivo (vídeo 9:16, captions, plantilla visual) se
    aplican aparte cuando hay MP3/MP4 disponible.
    """
    results: list[ValidationResult] = []

    # Hard de guion (12)
    results.append(check_word_count(script_text))
    results.append(check_hook_template(script_text))
    results.append(check_closing(script_text))
    results.append(check_no_dialogue(script_text))
    results.append(check_no_tts_tags(script_text))
    results.append(check_block_count(script_text))
    results.append(check_no_urls(script_text))
    results.append(check_no_paper_citations(script_text))
    # check_missing_glosario_source se valida en el generador (no aquí)
    results.append(check_blacklist_interjections(script_text))
    # voice_parity y filename_format solo si se pasan los datos
    if s_number is not None and voice is not None:
        results.append(check_voice_parity(s_number, voice))
    if filename is not None:
        results.append(check_filename(filename))

    # Soft de guion (5)
    results.append(check_brand_mention_only_in_closing(script_text))
    results.append(check_internal_block_length(script_text))
    # digits in speech (reutiliza audio_rules)
    from validators.shared import audio_rules
    results.append(audio_rules.check_digits_in_speech([script_text]))
    # apellidos inventados
    results.append(canonical_phrases.check_no_surnames(script_text))
    # Regla pedagogica SOFT: primera (y unica) mencion del termino expandida.
    # Critica en S porque el Short ES sobre ese termino.
    from validators.shared.pedagogy_check import check_first_mention_expansion
    results.append(check_first_mention_expansion(script_text))

    return results
