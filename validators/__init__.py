"""Validadores de guiones y audio de MaquinarIA Pesada (specs v6).

Arquitectura: validador base + 3 especialistas (M, T, S) por composición de los
módulos de `validators/shared/`. Salida estructurada en `ValidationResult`.

Reemplaza al `podcast_spec.py` legacy.
"""
from __future__ import annotations

from validators.result import ValidationResult, summarize

__all__ = ["ValidationResult", "summarize"]
