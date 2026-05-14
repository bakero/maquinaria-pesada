"""Frases canónicas obligatorias y prohibición de apellidos.

Reglas A.5 y A.6 del cuadro consolidado v6.

- HOOK cierra con la frase de arranque.
- CIERRE_CONCEPTOS abre con la frase de conceptos (M y T).
- CIERRE_FINAL incluye la frase de cierre (M y T).
- S cierra con la plantilla `Más sobre [tema] en el episodio T de MaquinarIA Pesada.`
- Los presentadores se llaman solo Maria y Yago — sin apellidos inventados.
"""
from __future__ import annotations

import re
import unicodedata

from validators.result import ValidationResult, fail, ok

HOOK_CLOSING = "Esto es MaquinarIA Pesada. Arrancamos."
CONCEPTS_OPENING = (
    "No te puedes ir de este capitulo sin haber entendido estos conceptos"
)
FINAL_CLOSING = (
    "Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada. "
    "Siguenos para nuevos capitulos donde la I.A. crea contenido sobre I.A."
)
# Plantilla de cierre de S: [tema] es variable, el resto literal.
S_CLOSING_REGEX = re.compile(
    r"m[aá]s sobre .+ en el episodio t de maquinaria pesada", re.IGNORECASE
)

# Apellido inventado tras "Maria" o "Yago".
SURNAME_REGEX = re.compile(
    r"\b(Maria|Yago)\s+[A-ZÁÉÍÓÚÑ][a-zñáéíóú]+"
)


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower())
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", stripped).strip()


def _contains(haystack: str, needle: str) -> bool:
    return _normalize(needle) in _normalize(haystack)


def check_hook_closing(hook_text: str) -> ValidationResult:
    """Hard-fail si el HOOK no cierra con la frase canónica de arranque."""
    if _contains(hook_text, HOOK_CLOSING):
        return ok("canonical_hook_closing", "HARD", "HOOK cierra correctamente")
    return fail("canonical_hook_closing", "HARD",
                f"El HOOK no contiene la frase canónica: '{HOOK_CLOSING}'")


def check_concepts_opening(concepts_text: str) -> ValidationResult:
    """Hard-fail si CIERRE_CONCEPTOS no abre con la frase canónica (M y T)."""
    if _contains(concepts_text, CONCEPTS_OPENING):
        return ok("canonical_concepts_opening", "HARD",
                  "CIERRE_CONCEPTOS abre correctamente")
    return fail("canonical_concepts_opening", "HARD",
                f"CIERRE_CONCEPTOS no contiene la frase canónica: "
                f"'{CONCEPTS_OPENING}'")


def check_final_closing(final_text: str) -> ValidationResult:
    """Hard-fail si CIERRE_FINAL no incluye la frase canónica (M y T)."""
    if _contains(final_text, FINAL_CLOSING):
        return ok("canonical_final_closing", "HARD",
                  "CIERRE_FINAL cierra correctamente")
    return fail("canonical_final_closing", "HARD",
                "CIERRE_FINAL no contiene la frase canónica de cierre")


def check_s_closing(closing_text: str) -> ValidationResult:
    """Hard-fail si el cierre de un Short no encaja en la plantilla canónica."""
    if S_CLOSING_REGEX.search(closing_text or ""):
        return ok("canonical_s_closing", "HARD",
                  "El Short cierra con la plantilla canónica")
    return fail("canonical_s_closing", "HARD",
                "El Short no cierra con 'Más sobre [tema] en el episodio T "
                "de MaquinarIA Pesada.'")


def check_no_surnames(full_text: str) -> ValidationResult:
    """Hard-fail si aparecen apellidos inventados tras Maria o Yago."""
    full_matches = [m.group(0) for m in SURNAME_REGEX.finditer(full_text or "")]
    if full_matches:
        return fail(
            "no_invented_surnames", "HARD",
            f"Apellido(s) inventado(s) detectado(s): {', '.join(full_matches)}",
            matches=full_matches,
        )
    return ok("no_invented_surnames", "HARD", "Sin apellidos inventados")
