#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Validador de episodios - MaquinarIa Pesada

Uso:
  python validar_episodio.py --ep EP001_promo --guion "Guiones/EP001_guion_etiquetas (1).txt"

Checks:
  1) MP3 existe y > 1 MB
  2) Duracion entre 8 y 60 min
  3) Log existe y contiene "Produccion completada"
  4) Log no contiene errores criticos: ERROR / FAILED / Exception
  5) Todos los bloques del guion fueron procesados (count log vs guion)
  6) Audio reproducible (pydub lo carga sin excepcion)

Extras (10% creatividad):
  - Estimacion creditos ElevenLabs (chars del guion)
  - Barra de progreso ASCII de bloques procesados
  - Salida visual atractiva (stdlib + pydub)
"""

from __future__ import annotations

import argparse
import os
import re
import sys

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


def check_log_no_errors(log_text: Optional[str]) -> CheckResult:
    name = "Log sin errores criticos"
    if log_text is None:
        return CheckResult(name, "ERROR", "Log no disponible")
    hits = [l.strip() for l in iter_lines(log_text) if CRITICAL_RE.search(l)][:3]
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
    return p.parse_args()


def main() -> int:
    args = parse_args()

    out = Path("episodios")
    mp3_path   = Path(args.mp3)  if args.mp3  else out / f"{args.ep}.mp3"
    log_path   = Path(args.log)  if args.log  else out / f"{args.ep}_produccion.log"
    guion_path = Path(args.guion)

    print_header(args.ep, mp3_path, log_path, guion_path)

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

    verdict, severity = summarize(results)
    print_verdict(verdict, severity)
    return 0 if not verdict.startswith("RECHAZADO") else 1


if __name__ == "__main__":
    raise SystemExit(main())
