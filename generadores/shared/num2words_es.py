"""Conversión de números a palabras en español.

Audio-Regla 1 v6: a 1.32×, "3.7%" o "$3M" son ininteligibles. El generador
convierte cualquier cifra del texto a palabras antes de enviar a TTS.

Usa `num2words` cuando está disponible; si no, cae a una implementación nativa
para 0-999 (suficiente para evitar dígitos sueltos en el guion).
"""
from __future__ import annotations

import re

try:  # pragma: no cover — selección de implementación
    from num2words import num2words as _num2words
    _HAS_NUM2WORDS = True
except ImportError:  # pragma: no cover
    _HAS_NUM2WORDS = False


_UNITS = ("cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete",
          "ocho", "nueve")
_TEENS = {10: "diez", 11: "once", 12: "doce", 13: "trece", 14: "catorce",
          15: "quince", 16: "dieciséis", 17: "diecisiete", 18: "dieciocho",
          19: "diecinueve"}
_TENS = {20: "veinte", 30: "treinta", 40: "cuarenta", 50: "cincuenta",
         60: "sesenta", 70: "setenta", 80: "ochenta", 90: "noventa"}
_HUNDREDS = {100: "cien", 200: "doscientos", 300: "trescientos",
             400: "cuatrocientos", 500: "quinientos", 600: "seiscientos",
             700: "setecientos", 800: "ochocientos", 900: "novecientos"}


def _spell_native(n: int) -> str:
    """Fallback nativo para 0-999 (sin acentos perfectos, suficiente para TTS)."""
    if n < 0:
        return "menos " + _spell_native(-n)
    if n < 10:
        return _UNITS[n]
    if n < 20:
        return _TEENS[n]
    if n < 100:
        tens = (n // 10) * 10
        unit = n % 10
        if tens == 20 and unit:
            mapping = {21: "veintiuno", 22: "veintidós", 23: "veintitrés",
                       24: "veinticuatro", 25: "veinticinco", 26: "veintiséis",
                       27: "veintisiete", 28: "veintiocho", 29: "veintinueve"}
            return mapping[n]
        if unit == 0:
            return _TENS[tens]
        return f"{_TENS[tens]} y {_UNITS[unit]}"
    if n == 100:
        return "cien"
    if n < 1000:
        h = (n // 100) * 100
        rest = n % 100
        prefix = _HUNDREDS[h] if h != 100 else "ciento"
        if rest == 0:
            return prefix
        return f"{prefix} {_spell_native(rest)}"
    # Para 1000+, delega en num2words si está; si no, devolvemos cadena bruta.
    return str(n)


def spell_integer(n: int) -> str:
    """Convierte un entero a palabras en español."""
    if _HAS_NUM2WORDS:
        return _num2words(n, lang="es")
    return _spell_native(n)


def spell_decimal(value: str) -> str:
    """Convierte una cifra con decimales (3.7, 3,7) a palabras."""
    sep = "." if "." in value else ","
    int_part, dec_part = value.split(sep, 1)
    int_text = spell_integer(int(int_part))
    dec_text = " ".join(spell_integer(int(d)) for d in dec_part)
    return f"{int_text} punto {dec_text}"


_NUMBER_RE = re.compile(r"(?<!\w)\d+(?:[.,]\d+)?(?!\d)")


def replace_numbers_in_text(text: str) -> str:
    """Sustituye cada cifra del texto por su forma en palabras.

    Mantiene la separación con `%` y `$`: "3.7%" se convierte a
    "tres punto siete por ciento", "$3M" a "tres millones de dólares".
    """
    def _rep(match: re.Match) -> str:
        raw = match.group(0)
        before = text[max(0, match.start() - 1):match.start()]
        after = text[match.end():match.end() + 2]
        if "." in raw or "," in raw:
            spelled = spell_decimal(raw)
        else:
            spelled = spell_integer(int(raw))
        # Sufijos comunes en cifras del corpus.
        if after.startswith("%"):
            return f"{spelled} por ciento"
        if after.startswith("M") and not after[1:].lstrip().startswith(tuple("abcdefghijklmnopqrstuvwxyz")):
            return f"{spelled} millones"
        if before == "$":
            return f"{spelled} dólares"
        return spelled

    out = _NUMBER_RE.sub(_rep, text)
    # Quitamos los símbolos % $ M sueltos que quedaron tras la sustitución.
    out = re.sub(r"\s*%", "", out)
    out = re.sub(r"\$\s*", "", out)
    # "M" suelto que era sufijo de millones — solo limpiar cuando sigue a "millones".
    out = re.sub(r"(millones)\s*M\b", r"\1", out)
    return out
