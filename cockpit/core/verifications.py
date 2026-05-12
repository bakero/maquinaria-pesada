"""Verificaciones por episodio y tipo de contenido.

Cada check devuelve un `CheckResult` con (id, label, status, detail).
Status ∈ {"ok", "fail", "warn", "na"}.

Sin red, sin keys: todas las comprobaciones son sobre filesystem.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .episodes import Episode


@dataclass
class CheckResult:
    id: str
    label: str
    status: str        # ok | fail | warn | na
    detail: str = ""

    @property
    def icon(self) -> str:
        return {"ok": "✅", "fail": "❌", "warn": "⚠️", "na": "⚪"}[self.status]


def _file_check(label: str, path: Path | None, min_bytes: int = 0) -> CheckResult:
    if path is None:
        return CheckResult(label.lower().replace(" ", "_"), label, "fail", "Falta el archivo")
    if not path.exists():
        return CheckResult(label.lower().replace(" ", "_"), label, "fail", f"No existe: {path.name}")
    sz = path.stat().st_size
    if sz < min_bytes:
        return CheckResult(
            label.lower().replace(" ", "_"),
            label,
            "warn",
            f"{path.name} pesa {sz} B (mínimo esperado {min_bytes})",
        )
    return CheckResult(
        label.lower().replace(" ", "_"),
        label,
        "ok",
        f"{path.name} · {sz:,} B",
    )


def _guion_content_checks(path: Path) -> list[CheckResult]:
    """Análisis ligero del texto del guion."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return [CheckResult("guion_read", "Lectura del guion", "fail", str(e))]
    out: list[CheckResult] = []
    n_words = len(text.split())
    out.append(
        CheckResult(
            "guion_min_words",
            "Guion ≥ 500 palabras",
            "ok" if n_words >= 500 else "warn",
            f"{n_words} palabras",
        )
    )
    has_iago = "iago" in text.lower()
    has_maria = "maría" in text.lower() or "maria" in text.lower()
    out.append(
        CheckResult(
            "guion_speakers",
            "Ambos speakers presentes",
            "ok" if has_iago and has_maria else "fail",
            f"iago={has_iago}, maria={has_maria}",
        )
    )
    return out


def _audio_size_check(path: Path) -> CheckResult:
    sz = path.stat().st_size
    # Heurística: > 200 KB ya es audio real, no un stub
    if sz < 200_000:
        return CheckResult(
            "audio_size", "Audio pesa más que un stub", "warn", f"{sz:,} B (esperado >200 KB)"
        )
    return CheckResult("audio_size", "Audio pesa más que un stub", "ok", f"{sz:,} B")


def _logs_error_check(logs: list[Path]) -> CheckResult:
    if not logs:
        return CheckResult("log_errors", "Logs sin errores", "na", "No hay logs")
    errors = 0
    for lp in logs:
        try:
            text = lp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            up = line.upper()
            if "ERROR" in up or "TRACEBACK" in up or "❌" in line:
                errors += 1
    if errors == 0:
        return CheckResult("log_errors", "Logs sin errores", "ok", "0 marcas de error")
    return CheckResult(
        "log_errors",
        "Logs sin errores",
        "fail",
        f"{errors} línea(s) con ERROR/TRACEBACK/❌",
    )


def run_all(ep: Episode) -> dict[str, list[CheckResult]]:
    """Ejecuta todas las verificaciones agrupadas por contenido."""
    results: dict[str, list[CheckResult]] = {}

    # PDF
    pdf_checks = [_file_check("PDF fuente", ep.pdf, min_bytes=10_000)]
    results["pdf"] = pdf_checks

    # Guion
    guion_checks = [_file_check("Guion", ep.guion, min_bytes=1_000)]
    if ep.guion and ep.guion.exists():
        guion_checks.extend(_guion_content_checks(ep.guion))
    results["guion"] = guion_checks

    # Escaleta
    results["escaleta"] = [_file_check("Escaleta", ep.escaleta, min_bytes=200)]

    # Audio
    audio_checks = [_file_check("Audio MP3", ep.audio, min_bytes=200_000)]
    if ep.audio and ep.audio.exists():
        audio_checks.append(_audio_size_check(ep.audio))
    results["audio"] = audio_checks

    # Logs
    results["logs"] = [
        CheckResult(
            "logs_present",
            "Hay logs de producción",
            "ok" if ep.logs else "warn",
            f"{len(ep.logs)} log(s)",
        ),
        _logs_error_check(ep.logs),
    ]
    return results


def episode_has_errors(ep: Episode) -> bool:
    """True si alguna verificación devuelve fail."""
    for group in run_all(ep).values():
        if any(c.status == "fail" for c in group):
            return True
    return False
