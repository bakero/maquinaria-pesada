"""
QA (Quality Assurance) policies para cada artefacto generado.

Filosofia: cada cosa que producimos pasa por una funcion check_X() que
devuelve {ok: bool, checks: {nombre: bool|valor}, errors: [...]}. Si
ok=False, NO se registra en la library / NO se considera entregado.

Cada funcion es pura: solo lee, no modifica. La integracion con el
pipeline es responsabilidad del caller.

Inventario de QAs:

  check_kling_clip(path)       Clip de video Kling (mp4, 16:9, ~20s)
  check_escaleta_md(path)      Escaleta markdown
  check_scene_track(path)      scene_track.json
  check_audio_structure(path)  audio_structure.json (sintonia detectada)
  check_video_final(path,
                    audio_dur) MP4 final del episodio
  check_library_integrity(lib) Library coherent (slugs <-> archivos)
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _ffprobe_duration(path: str | Path) -> float | None:
    if shutil.which("ffprobe") is None:
        return None
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ], text=True, timeout=30).strip()
        return float(out)
    except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired):
        return None


def _ffprobe_resolution(path: str | Path) -> tuple[int, int] | None:
    if shutil.which("ffprobe") is None:
        return None
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=s=x:p=0", str(path),
        ], text=True, timeout=30).strip()
        if "x" in out:
            w, h = out.split("x")
            return (int(w), int(h))
    except Exception:
        pass
    return None


def _result(ok: bool, checks: dict[str, Any], errors: list[str] | None = None) -> dict:
    return {"ok": ok, "checks": checks, "errors": errors or []}


# ── 1. Clip Kling ──────────────────────────────────────────────────

def check_kling_clip(path: str | Path,
                     expected_min_duration: float = 18.0,
                     expected_max_duration: float = 25.0,
                     expected_aspect: str = "16:9",
                     min_size_mb: float = 2.0) -> dict:
    """Valida un clip Kling descargado.

    Reglas:
      - Archivo existe
      - Tamanyo >= min_size_mb (defecto 2MB; 20s suelen pesar ~45MB)
      - ffprobe lee duracion -> integridad mp4 (moov atom OK)
      - duracion en [min, max] (para 20s clips: 18-25s)
      - aspect ratio 16:9 (1920x1080 o similar)
    """
    p = Path(path)
    checks: dict[str, Any] = {}
    errors: list[str] = []

    if not p.exists():
        return _result(False, {"exists": False}, ["archivo no existe"])
    checks["exists"] = True

    size_mb = p.stat().st_size / (1024 * 1024)
    checks["size_mb"] = round(size_mb, 2)
    if size_mb < min_size_mb:
        errors.append(f"tamano {size_mb:.1f}MB < min {min_size_mb}MB (truncado?)")

    dur = _ffprobe_duration(p)
    checks["duration"] = round(dur, 2) if dur is not None else None
    if dur is None:
        errors.append("ffprobe no pudo leer duracion (mp4 corrupto, moov missing)")
    else:
        if dur < expected_min_duration:
            errors.append(f"duracion {dur:.1f}s < min {expected_min_duration}s")
        elif dur > expected_max_duration:
            errors.append(f"duracion {dur:.1f}s > max {expected_max_duration}s")

    res = _ffprobe_resolution(p)
    checks["resolution"] = f"{res[0]}x{res[1]}" if res else None
    if res:
        ratio = res[0] / max(res[1], 1)
        if expected_aspect == "16:9":
            target = 16 / 9
            if abs(ratio - target) / target > 0.05:
                errors.append(f"aspect {ratio:.2f} != 16:9 (1.78)")
            checks["aspect_ratio"] = round(ratio, 3)

    return _result(len(errors) == 0, checks, errors)


# ── 2. Escaleta markdown ──────────────────────────────────────────

def check_escaleta_md(path: str | Path,
                      min_blocks: int = 8,
                      min_interventions: int = 20) -> dict:
    """Valida que la escaleta no este truncada y tenga marcas necesarias."""
    p = Path(path)
    checks: dict[str, Any] = {}
    errors: list[str] = []

    if not p.exists():
        return _result(False, {"exists": False}, ["escaleta no existe"])
    checks["exists"] = True

    text = p.read_text(encoding="utf-8")
    checks["lines"] = text.count("\n")
    checks["chars"] = len(text)

    n_blocks = len(re.findall(r"^##\s+[^\n]+", text, re.MULTILINE))
    n_ivs = len(re.findall(r"^###\s+[\d.]+", text, re.MULTILINE))
    checks["blocks"] = n_blocks
    checks["interventions"] = n_ivs
    if n_blocks < min_blocks:
        errors.append(f"bloques {n_blocks} < min {min_blocks}")
    if n_ivs < min_interventions:
        errors.append(f"intervenciones {n_ivs} < min {min_interventions}")

    # Detectar truncamiento: ultimo bloque debe cerrar limpiamente
    last500 = text[-500:].strip()
    if last500.endswith(("`", "|", "_")) or last500.count("\n") < 2:
        errors.append("posible truncamiento (cierre sospechoso)")
    checks["clean_close"] = len(errors) == 0 or "truncamiento" not in " ".join(errors)

    # Cobertura PIZARRA SI/NO
    pizarra_si = len(re.findall(r"\*\*PIZARRA:\*\*\s*S[IÍ]\b", text, re.IGNORECASE))
    pizarra_no = len(re.findall(r"\*\*PIZARRA:\*\*\s*NO\b", text, re.IGNORECASE))
    checks["pizarra_si"] = pizarra_si
    checks["pizarra_no"] = pizarra_no
    if pizarra_si + pizarra_no < n_ivs * 0.5:
        errors.append(f"solo {pizarra_si+pizarra_no}/{n_ivs} ivs marcan PIZARRA")

    return _result(len(errors) == 0, checks, errors)


# ── 3. scene_track.json ────────────────────────────────────────────

def check_scene_track(path: str | Path,
                      audio_duration: float | None = None,
                      max_drift_s: float = 1.0,
                      max_overlap_s: float = 0.05) -> dict:
    """Valida que el scene_track sea monotonico y que su ultimo end
    coincida con audio_duration (drift < max_drift_s)."""
    p = Path(path)
    checks: dict[str, Any] = {}
    errors: list[str] = []

    if not p.exists():
        return _result(False, {"exists": False}, ["scene_track no existe"])

    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return _result(False, {"format": "no es lista"}, ["scene_track no es lista"])

    checks["segments"] = len(data)
    if not data:
        errors.append("scene_track vacio")
        return _result(False, checks, errors)

    # Monotonia: cada seg.end <= next.start (con tolerancia max_overlap_s)
    overlaps = 0
    sum_dur = 0.0
    by_type: dict[str, int] = {}
    for i, seg in enumerate(data):
        s = float(seg.get("start", 0))
        e = float(seg.get("end", 0))
        sum_dur += max(0.0, e - s)
        by_type[seg.get("type", "?")] = by_type.get(seg.get("type", "?"), 0) + 1
        if i > 0:
            prev_e = float(data[i - 1].get("end", 0))
            if s < prev_e - max_overlap_s:
                overlaps += 1

    checks["overlaps"] = overlaps
    checks["sum_duration"] = round(sum_dur, 3)
    checks["last_end"] = round(float(data[-1].get("end", 0)), 3)
    checks["by_type"] = by_type

    if overlaps > 0:
        errors.append(f"{overlaps} solapamientos (track NO monotonico)")

    if audio_duration is not None:
        drift = abs(checks["last_end"] - audio_duration)
        checks["drift_vs_audio"] = round(drift, 3)
        if drift > max_drift_s:
            errors.append(f"drift {drift:.2f}s > {max_drift_s}s vs audio")

    return _result(len(errors) == 0, checks, errors)


# ── 4. audio_structure.json ────────────────────────────────────────

def check_audio_structure(path: str | Path,
                          min_audio_duration: float = 600.0,
                          max_audio_duration: float = 1100.0) -> dict:
    """Valida que sintonia este detectada y los hitos sean coherentes."""
    p = Path(path)
    checks: dict[str, Any] = {}
    errors: list[str] = []

    if not p.exists():
        return _result(False, {"exists": False}, ["audio_structure no existe"])

    data = json.loads(p.read_text(encoding="utf-8"))
    dur = float(data.get("audio_duration") or 0)
    checks["audio_duration"] = round(dur, 1)
    if dur < min_audio_duration:
        errors.append(f"audio_duration {dur:.0f}s < {min_audio_duration}s")
    if dur > max_audio_duration:
        errors.append(f"audio_duration {dur:.0f}s > {max_audio_duration}s")

    for k in ("hook_end", "sintonia_start", "sintonia_end", "content_start", "content_end"):
        v = data.get(k)
        checks[k] = v
        if v is None:
            errors.append(f"{k} no detectado")

    sintonia_dur = None
    if data.get("sintonia_start") is not None and data.get("sintonia_end") is not None:
        sintonia_dur = data["sintonia_end"] - data["sintonia_start"]
        checks["sintonia_duration"] = round(sintonia_dur, 2)
        if sintonia_dur < 8 or sintonia_dur > 12:
            errors.append(f"sintonia_dur {sintonia_dur:.1f}s fuera de [8,12]s")

    if data.get("content_start") is not None and data.get("content_end") is not None:
        if data["content_end"] <= data["content_start"]:
            errors.append("content_end <= content_start (incoherente)")

    return _result(len(errors) == 0, checks, errors)


# ── 5. Video final del episodio ────────────────────────────────────

def check_video_final(path: str | Path,
                      expected_audio_duration: float | None = None,
                      max_drift_s: float = 1.5,
                      min_size_mb: float = 30.0) -> dict:
    """Valida MP4 final."""
    p = Path(path)
    checks: dict[str, Any] = {}
    errors: list[str] = []

    if not p.exists():
        return _result(False, {"exists": False}, ["video final no existe"])
    checks["exists"] = True

    size_mb = p.stat().st_size / (1024 * 1024)
    checks["size_mb"] = round(size_mb, 1)
    if size_mb < min_size_mb:
        errors.append(f"tamano {size_mb:.0f}MB < {min_size_mb}MB (sospechoso)")

    dur = _ffprobe_duration(p)
    checks["duration"] = round(dur, 2) if dur is not None else None
    if dur is None:
        errors.append("ffprobe no lee duracion (mp4 corrupto)")
    elif expected_audio_duration is not None:
        drift = abs(dur - expected_audio_duration)
        checks["drift_vs_audio"] = round(drift, 3)
        if drift > max_drift_s:
            errors.append(f"drift video-audio {drift:.2f}s > {max_drift_s}s")

    res = _ffprobe_resolution(p)
    checks["resolution"] = f"{res[0]}x{res[1]}" if res else None
    if res and res != (1920, 1080):
        errors.append(f"resolucion {res} != 1920x1080")

    return _result(len(errors) == 0, checks, errors)


# ── 6. Library integrity ───────────────────────────────────────────

def check_library_integrity(library) -> dict:
    """Valida que cada slug del index tiene fichero fisico y QA OK."""
    checks: dict[str, Any] = {}
    errors: list[str] = []

    scenes = (library._index.get("scenes") if hasattr(library, "_index")
              else getattr(library, "scenes", {})) or {}
    checks["total_scenes"] = len(scenes)

    missing = []
    corrupt = []
    ok = []
    for slug, entry in scenes.items():
        path = Path(entry.get("path", ""))
        if not path.exists():
            missing.append(slug)
            continue
        # Quick check: size > 1MB and ffprobe OK
        if path.stat().st_size < 1_000_000:
            corrupt.append(f"{slug} (truncado)")
            continue
        if _ffprobe_duration(path) is None:
            corrupt.append(f"{slug} (moov)")
            continue
        ok.append(slug)

    checks["ok"] = len(ok)
    checks["missing"] = len(missing)
    checks["corrupt"] = len(corrupt)
    if missing:
        errors.append(f"missing files: {missing}")
    if corrupt:
        errors.append(f"corrupt clips: {corrupt}")

    return _result(len(errors) == 0, checks, errors)


# ── 6.bis Escaleta SEMANTIC: detectar texto del guion en pizarra ──

def _normalize_text(s: str) -> str:
    """Normaliza para comparacion fuzzy: lower, sin tildes, sin
    puntuacion, espacios colapsados."""
    import unicodedata
    s = s.lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _ngrams(text: str, n: int = 4) -> set:
    """Set de n-gramas de palabras."""
    words = _normalize_text(text).split()
    if len(words) < n:
        return set()
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def check_escaleta_semantic(escaleta_path: str | Path,
                             max_overlap_ratio: float = 0.4) -> dict:
    """Verifica que el LLM no haya copiado texto del guion en la
    pizarra (overlay labels). Para cada intervencion compara los
    4-gramas de su texto vs los de cada label de la tabla on-screen.
    Si el solapamiento > max_overlap_ratio -> fail.

    Tambien detecta el patron clasico de preguntas literales en
    highlight_quote / quote / concept_card.
    """
    from .escaleta_parser import parse_escaleta

    p = Path(escaleta_path)
    checks: dict[str, Any] = {}
    errors: list[str] = []

    if not p.exists():
        return _result(False, {"exists": False}, ["escaleta no existe"])

    parsed = parse_escaleta(p)
    total_overlays = 0
    overlap_ngrams = 0
    quote_with_question = 0
    bad_overlays: list[str] = []

    for block in parsed.get("blocks", []):
        for iv in block.get("interventions", []):
            iv_text = iv.get("text", "") or ""
            iv_ngrams = _ngrams(iv_text, n=4)
            for os_item in iv.get("on_screen", []) or []:
                total_overlays += 1
                label = os_item.get("label_text") or os_item.get("raw") or ""
                # Pattern 1: pregunta literal en highlight_quote / quote / concept
                elem = (os_item.get("element") or "").lower()
                if elem in ("highlight_quote", "quote", "concept_card",
                            "concept_card_image", "concept"):
                    if "?" in label or label.strip().startswith("¿"):
                        quote_with_question += 1
                        bad_overlays.append(f"  iv {iv.get('id')}: {elem} con '?' -> '{label[:60]}'")
                # Pattern 2: solapamiento alto con texto del guion
                if iv_ngrams:
                    label_ngrams = _ngrams(label, n=4)
                    if label_ngrams:
                        overlap = len(label_ngrams & iv_ngrams) / len(label_ngrams)
                        if overlap >= max_overlap_ratio:
                            overlap_ngrams += 1
                            bad_overlays.append(
                                f"  iv {iv.get('id')}: overlap {overlap:.0%} "
                                f"label={label[:50]!r}")

    checks["total_overlays"] = total_overlays
    checks["quote_with_question"] = quote_with_question
    checks["overlap_with_script"] = overlap_ngrams
    if quote_with_question > 0:
        errors.append(f"{quote_with_question} overlays son preguntas literales del guion")
    if overlap_ngrams > 0:
        errors.append(f"{overlap_ngrams} overlays solapan >40% con texto del guion")
    if bad_overlays:
        checks["examples"] = bad_overlays[:10]

    return _result(len(errors) == 0, checks, errors)


# ── 7. SRT subtitulos ──────────────────────────────────────────────

def check_srt(path: str | Path,
              min_chunks: int = 50,
              max_chunk_duration_s: float = 6.0) -> dict:
    """Valida SRT generado: numero de chunks, duraciones razonables."""
    p = Path(path)
    checks: dict[str, Any] = {}
    errors: list[str] = []

    if not p.exists():
        return _result(False, {"exists": False}, ["SRT no existe"])

    text = p.read_text(encoding="utf-8")
    chunk_idx = re.findall(r"^(\d+)\s*\n([\d:,]+)\s*-->\s*([\d:,]+)\s*\n",
                           text, re.MULTILINE)
    checks["chunks"] = len(chunk_idx)
    if len(chunk_idx) < min_chunks:
        errors.append(f"chunks {len(chunk_idx)} < min {min_chunks}")

    def _to_sec(ts: str) -> float:
        h, m, rest = ts.split(":")
        s, ms = rest.split(",")
        return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000

    too_long = 0
    for _, t_in, t_out in chunk_idx:
        dur = _to_sec(t_out) - _to_sec(t_in)
        if dur > max_chunk_duration_s:
            too_long += 1
    checks["chunks_over_max_dur"] = too_long
    if too_long > 0:
        errors.append(f"{too_long} chunks > {max_chunk_duration_s}s")

    return _result(len(errors) == 0, checks, errors)
