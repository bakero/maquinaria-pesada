#!/usr/bin/env python3
# ruff: noqa
"""
Validador de episodios - MaquinarIa Pesada

🚫 SCRIPT LEGACY — RETIRADO 2026-05-19.
   El validador vigente es `validar_episodio_v6.py` que ejecuta los 54+
   checks de `validators/{base,m,t,s}_validator.py` más la capa editorial
   v6.1. Ver `GENERACION.md`.
"""
from __future__ import annotations

import sys

if __name__ == "__main__":
    sys.stderr.write(
        "\n❌ validar_episodio.py está retirado (era v5).\n"
        "   Usa el validador canónico:\n"
        "       python validar_episodio_v6.py --kind M --ep M3 --guion Guiones/M3_v6.md\n"
        "   Ver GENERACION.md para el mapa completo.\n\n"
    )
    raise SystemExit(2)

# ---- Código histórico inaccesible ----------------------------------------
# Se elimina entero en un PR de limpieza dedicado.
# --------------------------------------------------------------------------

import argparse
import os
import re

# Forzar UTF-8 en consola Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Tuple, List

from dotenv import load_dotenv
load_dotenv(override=True)

from pydub import AudioSegment

sys.path.insert(0, str(Path(__file__).parent))
from podcast_spec import (  # noqa: E402
    compute_glossary_coverage,
    episode_number,
    glossary_concepts_for_sources,
    parse_glossary,
    source_code_from_pdf_path,
)

# ----------------------------
# Utilidades de consola
# ----------------------------

RESET   = "\x1b[0m"
BOLD    = "\x1b[1m"

FG_GREEN  = "\x1b[32m"
FG_YELLOW = "\x1b[33m"
FG_RED    = "\x1b[31m"
FG_CYAN   = "\x1b[36m"
FG_GRAY   = "\x1b[90m"


def supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


USE_COLOR = supports_color()


def c(text: str, color: str) -> str:
    if not USE_COLOR:
        return text
    return f"{color}{text}{RESET}"


def badge(status: str) -> str:
    s = status.upper()
    if s == "OK":
        return c("[ OK ]", FG_GREEN)
    if s == "WARN":
        return c("[WARN]", FG_YELLOW)
    if s == "ERROR":
        return c("[ERR ]", FG_RED)
    return s


def fmt_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    x = float(n)
    for u in units:
        if x < 1024.0 or u == units[-1]:
            return f"{x:.2f} {u}" if u != "B" else f"{int(x)} {u}"
        x /= 1024.0
    return f"{n} B"


def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def progress_bar(done: int, total: int, width: int = 30) -> str:
    if total <= 0:
        total = 1
    done = clamp(done, 0, total)
    filled = clamp(int(round((done / total) * width)), 0, width)
    bar = "█" * filled + "░" * (width - filled)
    pct = int(round((done / total) * 100))
    return f"[{bar}] {done}/{total}  ({pct}%)"


# ----------------------------
# Modelo de resultado
# ----------------------------

@dataclass
class CheckResult:
    name:   str
    status: str   # OK | WARN | ERROR
    detail: str


# ----------------------------
# I/O helpers
# ----------------------------

def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="strict")
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            raise
    return path.read_text(encoding="latin-1", errors="replace")


def iter_lines(text: str) -> Iterable[str]:
    for line in text.splitlines():
        yield line.rstrip("\n")


# ----------------------------
# Parseo de bloques
# ----------------------------

# El log de generar_episodio_v2.py usa el formato: "  [001] IAGO — generando..."
LOG_BLOCK_RE = re.compile(r"^\s*\[(\d+)\]")

# El guion usa líneas que empiezan con IAGO: o MARIA:
GUION_LINE_RE = re.compile(r"^(IAGO|MAR[IÍ]A)\s*:", re.IGNORECASE)


def count_speaker_lines_in_guion(guion_text: str) -> int:
    """Cuenta bloques reales del guion (líneas IAGO:/MARÍA:)."""
    return sum(1 for line in iter_lines(guion_text) if GUION_LINE_RE.match(line))


def max_block_index_in_log(log_text: str) -> int:
    """Devuelve el índice máximo de bloque procesado visto en el log."""
    max_idx = 0
    for line in iter_lines(log_text):
        m = LOG_BLOCK_RE.match(line)
        if m:
            max_idx = max(max_idx, int(m.group(1)))
    return max_idx


# ----------------------------
# Checks individuales
# ----------------------------

CRITICAL_RE = re.compile(r"\b(ERROR|FAILED|EXCEPTION)\b", re.IGNORECASE)


def check_mp3_exists_and_size(mp3_path: Path) -> CheckResult:
    name = "MP3 existe y tamaño > 1 MB"
    if not mp3_path.exists():
        return CheckResult(name, "ERROR", f"No existe: {mp3_path}")
    size = mp3_path.stat().st_size
    if size <= 1_048_576:
        return CheckResult(name, "ERROR", f"Demasiado pequeño: {fmt_bytes(size)}")
    return CheckResult(name, "OK", fmt_bytes(size))


def check_audio_load(mp3_path: Path) -> Tuple[CheckResult, Optional[float]]:
    name = "Audio reproducible (pydub)"
    try:
        audio = AudioSegment.from_file(mp3_path, format="mp3")
        duration_min = len(audio) / 60_000.0
        return CheckResult(name, "OK", "Carga correcta"), duration_min
    except Exception as e:
        return CheckResult(name, "ERROR", f"{type(e).__name__}: {e}"), None


def check_duration(duration_min: Optional[float], lo: float, hi: float) -> CheckResult:
    name = f"Duracion entre {lo:.0f} y {hi:.0f} min"
    if duration_min is None:
        return CheckResult(name, "ERROR", "No disponible (fallo carga)")
    if not (lo <= duration_min <= hi):
        return CheckResult(name, "ERROR", f"{duration_min:.2f} min fuera de rango")
    return CheckResult(name, "OK", f"{duration_min:.2f} min")


def check_log_completion(log_path: Path) -> Tuple[CheckResult, Optional[str]]:
    name = "Log existe y contiene 'Produccion completada'"
    if not log_path.exists():
        return CheckResult(name, "ERROR", f"No existe: {log_path}"), None
    try:
        text = read_text(log_path)
    except Exception as e:
        return CheckResult(name, "ERROR", str(e)), None
    if "produccion completada" not in text.lower():
        return CheckResult(name, "ERROR", "Frase no encontrada en log"), text
    return CheckResult(name, "OK", "OK"), text


BLOCK_LINE_RE = re.compile(r"^\s*\[\d{3,}\]\s+(IAGO|MARIA)\s*:")


def check_log_no_errors(log_text: Optional[str]) -> CheckResult:
    name = "Log sin errores criticos"
    if log_text is None:
        return CheckResult(name, "ERROR", "Log no disponible")
    # Excluir lineas que son citas de contenido del guion ([NNN] SPEAKER: ...)
    # — esas pueden contener "error" o "falla" como parte del texto hablado, no
    # como error real del pipeline.
    hits = [
        l.strip()
        for l in iter_lines(log_text)
        if CRITICAL_RE.search(l) and not BLOCK_LINE_RE.match(l)
    ][:3]
    if hits:
        return CheckResult(name, "ERROR", " | ".join(hits))
    return CheckResult(name, "OK", "Sin ERROR/FAILED/Exception")


def check_blocks(log_text: Optional[str], guion_text: Optional[str]) -> Tuple[CheckResult, str]:
    name = "Bloques procesados (log vs guion)"
    if log_text is None or guion_text is None:
        return CheckResult(name, "WARN", "No disponible"), "n/a"

    expected = count_speaker_lines_in_guion(guion_text)
    processed = max_block_index_in_log(log_text)

    bar = progress_bar(processed, expected) if expected > 0 else "n/a"

    if expected == 0:
        return CheckResult(name, "WARN", "No se detectaron bloques en el guion"), bar
    if processed == 0:
        return CheckResult(name, "WARN", "No se detectaron indices en el log"), bar
    if processed < expected:
        return CheckResult(name, "ERROR", f"Incompleto: {processed}/{expected}"), bar
    return CheckResult(name, "OK", f"{processed}/{expected} bloques"), bar


# ----------------------------
# Cobertura de conceptos del glosario
# ----------------------------

GLOSSARY_DEFAULT_PATH = Path(__file__).parent / "PDFs" / "auxiliares" / "glosario_unificado.md"


def extract_spoken_text(guion_text: str) -> str:
    """Texto hablado del guion: solo líneas IAGO:/MARÍA:, sin el prefijo del speaker.

    Excluye la sección # VERIFICACIONES y los encabezados de sección, de modo que
    la cobertura mida el diálogo real y no los nombres de conceptos listados al final.
    """
    spoken: list[str] = []
    for line in iter_lines(guion_text):
        if GUION_LINE_RE.match(line):
            spoken.append(re.sub(r"^(IAGO|MAR[IÍ]A)\s*:\s*", "", line, flags=re.IGNORECASE))
    return "\n".join(spoken)


def resolve_glossary_sources(ep: str, guion_path: Path, pdf_fuente: str | None) -> list[str]:
    """Determina los códigos de fuente del glosario (MX_TY / MX_RESUMEN) a evaluar.

    Si se pasa --pdf-fuente se deriva de su nombre; si no, se infiere el número de
    módulo desde el ep o el nombre del guion y se usa el RESUMEN del módulo, que es
    el PDF que `generar_guion.py` usa como fuente.
    """
    if pdf_fuente:
        code = source_code_from_pdf_path(pdf_fuente)
        return [code] if code else []
    for candidate in (ep, guion_path.stem):
        try:
            n = episode_number(candidate)
            return [f"M{n}_RESUMEN"]
        except ValueError:
            continue
    return []


def check_glossary_coverage(
    guion_text: str | None,
    ep: str,
    guion_path: Path,
    pdf_fuente: str | None,
    glosario_path: Path,
) -> tuple[CheckResult, str]:
    """Mide qué % de conceptos del glosario asociados al PDF fuente aparecen en el guion."""
    name = "Cobertura de conceptos del glosario en el guion"
    if guion_text is None:
        return CheckResult(name, "WARN", "Guion no disponible"), "n/a"
    glossary = parse_glossary(glosario_path)
    if not glossary:
        return CheckResult(name, "WARN", f"Glosario no encontrado: {glosario_path}"), "n/a"
    sources = resolve_glossary_sources(ep, guion_path, pdf_fuente)
    if not sources:
        return CheckResult(name, "WARN", "No se pudo inferir el PDF fuente (usa --pdf-fuente)"), "n/a"
    concepts = glossary_concepts_for_sources(sources, glossary=glossary)
    # Fallback: si el RESUMEN no tiene conceptos etiquetados, usar todos los del módulo.
    if not concepts and sources[0].endswith("_RESUMEN"):
        mod = sources[0].split("_")[0]
        concepts = [
            t for t, codes in glossary.items()
            if any(c == mod or c.startswith(mod + "_") for c in codes)
        ]
    if not concepts:
        return CheckResult(name, "WARN", f"Sin conceptos de glosario para {', '.join(sources)}"), "n/a"
    cov = compute_glossary_coverage(extract_spoken_text(guion_text), concepts)
    bar = progress_bar(len(cov["covered"]), cov["total"])
    detail = (
        f"{cov['coverage_pct']}% — {len(cov['covered'])}/{cov['total']} conceptos "
        f"de {', '.join(sources)}"
    )
    if cov["missing"]:
        detail += f" | sin mencionar: {', '.join(cov['missing'][:6])}"
    status = "OK" if cov["coverage_pct"] >= 75 else "WARN"
    return CheckResult(name, status, detail), bar


# ----------------------------
# Estimacion de creditos
# ----------------------------

def estimate_credits(guion_text: str) -> Tuple[int, int]:
    """Devuelve (chars_totales_en_bloques, chars_compactos)."""
    chars = 0
    for line in iter_lines(guion_text):
        if GUION_LINE_RE.match(line):
            # quitar el prefijo "IAGO: " / "MARÍA: "
            texto = re.sub(r"^(IAGO|MAR[IÍ]A)\s*:\s*", "", line, flags=re.IGNORECASE)
            chars += len(texto)
    compact = len(re.sub(r"\s+", " ", guion_text).strip())
    return chars, compact


# ----------------------------
# Presentacion
# ----------------------------

def print_header(ep: str, mp3: Path, log: Path, guion: Path) -> None:
    title = f"VALIDADOR DE EPISODIO  —  {ep}"
    sep = "═" * (len(title) + 4)
    print(c(sep, FG_CYAN))
    print(c(f"  {title}", BOLD + FG_CYAN if USE_COLOR else FG_CYAN))
    print(c(sep, FG_CYAN))
    print(f"  {c('MP3  ', FG_GRAY)}: {mp3}")
    print(f"  {c('LOG  ', FG_GRAY)}: {log}")
    print(f"  {c('GUION', FG_GRAY)}: {guion}")
    print()


def print_check(i: int, total: int, res: CheckResult) -> None:
    num = c(f"{i}/{total}", FG_GRAY)
    name = (BOLD + res.name + RESET) if USE_COLOR else res.name
    print(f"  {num}  {badge(res.status)}  {name}")
    if res.detail:
        print(f"         {c('↳', FG_GRAY)} {res.detail}")


def print_verdict(verdict: str, severity: str) -> None:
    sep = "─" * 40
    print(c(sep, FG_CYAN))
    if severity == "OK":
        v = c("✔  APROBADO", FG_GREEN)
    elif severity == "WARN":
        v = c("⚠  APROBADO (con advertencias)", FG_YELLOW)
    else:
        v = c("✖  RECHAZADO", FG_RED)
    print(f"  Veredicto: {v}")
    print(c(sep, FG_CYAN))
    print(f"\nRESULTADO_FINAL={verdict}")


def summarize(results: List[CheckResult]) -> Tuple[str, str]:
    if any(r.status == "ERROR" for r in results):
        return "RECHAZADO", "ERROR"
    if any(r.status == "WARN" for r in results):
        return "APROBADO (con WARN)", "WARN"
    return "APROBADO", "OK"


# ----------------------------
# Main
# ----------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validador de episodios - MaquinarIa Pesada")
    p.add_argument("--ep",    required=True, help="Prefijo del episodio, ej: EP001_promo")
    p.add_argument("--guion", required=True, help="Ruta al guion .txt")
    p.add_argument("--mp3",   default=None,  help="Ruta MP3 (opcional, se infiere de --ep)")
    p.add_argument("--log",   default=None,  help="Ruta log (opcional, se infiere de --ep)")
    p.add_argument("--min",   dest="min_min", type=float, default=8.0,  help="Duracion minima en minutos")
    p.add_argument("--max",   dest="max_min", type=float, default=60.0, help="Duracion maxima en minutos")
    p.add_argument(
        "--pdf-fuente", default=None,
        help="Ruta al PDF fuente del guion (para medir cobertura de conceptos del glosario). "
             "Si se omite, se infiere el RESUMEN del modulo desde el ep/guion.",
    )
    p.add_argument(
        "--glosario", default=None,
        help="Ruta al glosario unificado (por defecto PDFs/auxiliares/glosario_unificado.md)",
    )
    return p.parse_args()


def main() -> int:
    from cockpit.core.log_helpers import get_run_logger
    log = get_run_logger("validar_episodio")

    args = parse_args()

    out = Path("episodios")
    mp3_path   = Path(args.mp3)  if args.mp3  else out / f"{args.ep}.mp3"
    log_path   = Path(args.log)  if args.log  else out / f"{args.ep}_produccion.log"
    guion_path = Path(args.guion)

    print_header(args.ep, mp3_path, log_path, guion_path)
    log.step("load_script", ep=args.ep, guion=str(guion_path), mp3=str(mp3_path))

    # Leer guion
    guion_text: Optional[str] = None
    try:
        guion_text = read_text(guion_path)
    except Exception:
        pass

    # Estimacion creditos
    if guion_text:
        chars_bloques, chars_compact = estimate_credits(guion_text)
        print(f"  {c('Creditos ElevenLabs (est.)', FG_GRAY)}: ~{chars_bloques:,} chars en dialogos  "
              f"| compact total: {chars_compact:,} chars")
    else:
        print(f"  {badge('WARN')} No se pudo leer el guion para estimar creditos")
    print()

    # Ejecutar checks
    log.step("validate", ep=args.ep)
    results: List[CheckResult] = []

    r_size = check_mp3_exists_and_size(mp3_path)
    results.append(r_size)

    if r_size.status != "ERROR":
        r_audio, duration_min = check_audio_load(mp3_path)
    else:
        r_audio  = CheckResult("Audio reproducible (pydub)", "ERROR", "No se valida (MP3 no encontrado)")
        duration_min = None
    results.append(r_audio)

    results.append(check_duration(duration_min, args.min_min, args.max_min))

    r_log, log_text = check_log_completion(log_path)
    results.append(r_log)
    results.append(check_log_no_errors(log_text))

    r_blocks, bar = check_blocks(log_text, guion_text)
    results.append(r_blocks)

    glosario_path = Path(args.glosario) if args.glosario else GLOSSARY_DEFAULT_PATH
    r_glossary, gloss_bar = check_glossary_coverage(
        guion_text, args.ep, guion_path, args.pdf_fuente, glosario_path
    )
    results.append(r_glossary)

    # Imprimir checklist
    print(c("  CHECKLIST", FG_CYAN))
    print(c("  " + "─" * 38, FG_CYAN))
    for i, res in enumerate(results, 1):
        print_check(i, len(results), res)
    print()

    # Barra de progreso
    if bar != "n/a":
        print(f"  {c('Progreso bloques', FG_GRAY)}: {bar}")
        print()
    if gloss_bar != "n/a":
        print(f"  {c('Cobertura glosario', FG_GRAY)}: {gloss_bar}")
        print()

    verdict, severity = summarize(results)
    print_verdict(verdict, severity)
    n_ok = sum(1 for r in results if r.status == "OK")
    n_warn = sum(1 for r in results if r.status == "WARN")
    n_err = sum(1 for r in results if r.status == "ERROR")
    if verdict.startswith("RECHAZADO"):
        log.error("episodio rechazado", ep=args.ep, verdict=verdict,
                  ok=n_ok, warn=n_warn, error=n_err)
    else:
        log.ok("episodio aceptado", ep=args.ep, verdict=verdict,
               ok=n_ok, warn=n_warn, error=n_err)
    return 0 if not verdict.startswith("RECHAZADO") else 1


# El bloque `if __name__ == "__main__"` original se ha movido al inicio del
# archivo (ver guard arriba). No se ejecutará por debajo del SystemExit.
if False:  # pragma: no cover - histórico inaccesible
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="validar_episodio.py", params=sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        raise SystemExit(main())
