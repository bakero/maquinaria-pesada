"""
Reconstruye la escaleta de tiempos del episodio a partir de los chunks
individuales de audio en `episodios/temp/` y la `audio_structure`.

Asuncion del flujo de produccion (generar_episodio_v2.py):
  1. Silencio inicial (~2s)
  2. Chunks del HOOK concatenados consecutivamente
  3. Silencio post-hook (~2s)
  4. Sintonia (intro_video) inyectada
  5. Silencio post-sintonia (~2s)
  6. Chunks del CONTENIDO concatenados consecutivamente
  7. Silencio final (~3s)

Si conocemos:
  - Duracion exacta de cada chunk (ffprobe)
  - audio_structure con hook_start, hook_end, sintonia_*, content_start
podemos calcular timestamps EXACTOS para cada intervencion sin depender
de Whisper ni del matching aproximado.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

from .logger import get_logger

CHUNK_NAME_RE = re.compile(
    r"^(?P<prefix>EP-MOD\d+|M\d+_E_[\w]+|EP\d+(?:_test|_promo)?)_(?P<num>\d{3,4})_(?P<speaker>[A-ZÑÁÉÍÓÚ]+)\.mp3$",
    re.IGNORECASE,
)


def _ffprobe_duration(path: Path) -> float:
    if shutil.which("ffprobe") is None:
        return 0.0
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of",
            "default=noprint_wrappers=1:nokey=1", str(path),
        ], text=True).strip()
        return float(out)
    except Exception:
        return 0.0


def list_chunks(temp_folder: str | Path,
                episode_prefix: str | None = None) -> list[dict]:
    """
    Devuelve lista ordenada de chunks: [{"path","num","speaker","duration"}, ...]
    Filtra por prefijo si se da (ej. "EP-MOD000").
    """
    folder = Path(temp_folder)
    if not folder.exists():
        return []
    chunks = []
    for f in sorted(folder.glob("*.mp3")):
        m = CHUNK_NAME_RE.match(f.name)
        if not m:
            continue
        prefix = m.group("prefix")
        if episode_prefix and prefix.upper() != episode_prefix.upper():
            continue
        num = int(m.group("num"))
        speaker = m.group("speaker").upper().replace("Á", "A").replace("Í", "I")
        chunks.append({
            "path":    str(f),
            "num":     num,
            "speaker": speaker,
            "duration": _ffprobe_duration(f),
            "filename": f.name,
        })
    chunks.sort(key=lambda x: x["num"])
    return chunks


def reconstruct_timeline(chunks: list[dict],
                         interventions: list[dict],
                         audio_structure: dict) -> list[dict]:
    """
    Asocia cada chunk con la intervencion correspondiente del guion (por orden)
    y calcula timestamps absolutos.

    Reglas:
      - El primer chunk empieza en hook_start (final del lead silence).
      - Los chunks pertenecientes al HOOK se distribuyen entre [hook_start, hook_end].
      - Los chunks del CONTENIDO se distribuyen entre [content_start, content_end].

    Para saber cuales son del HOOK y cuales del CONTENIDO, miramos la seccion
    de la intervencion del guion (que viene en orden).
    """
    log = get_logger("production_log_parser")
    if not chunks or not interventions:
        return []

    # Particionar intervenciones por seccion
    SKIP_SECTIONS = {"INTRO_SONIDO", "SINTONIA", "VERIFICACIONES"}
    spoken_ivs = [iv for iv in interventions
                  if (iv.get("section") or "").upper() not in SKIP_SECTIONS]

    if len(spoken_ivs) != len(chunks):
        log.warning(f"  Discrepancia: {len(chunks)} chunks vs {len(spoken_ivs)} "
                    f"intervenciones en guion. Usando el menor.")
    n = min(len(chunks), len(spoken_ivs))
    spoken_ivs = spoken_ivs[:n]
    chunks_used = chunks[:n]

    hook_start = float(audio_structure.get("hook_start") or 0.0)
    hook_end = float(audio_structure.get("hook_end") or hook_start)
    content_start = float(audio_structure.get("content_start") or hook_end)
    content_end = float(audio_structure.get("content_end") or
                         (content_start + 600))

    # Separar chunks segun seccion de su intervencion correspondiente
    hook_chunks = []
    content_chunks = []
    for ch, iv in zip(chunks_used, spoken_ivs, strict=False):
        if (iv.get("section") or "").upper() == "HOOK":
            hook_chunks.append((ch, iv))
        else:
            content_chunks.append((ch, iv))

    aligned = []

    def _layout(group: list, t_start: float, t_end: float) -> None:
        """Coloca chunks en [t_start, t_end] usando duraciones reales,
        repartiendo el sobrante (silencios entre intervenciones)
        proporcionalmente entre los gaps."""
        if not group:
            return
        sum_dur = sum(ch["duration"] for ch, _ in group) or 0.001
        total_window = max(t_end - t_start, sum_dur)
        slack = max(0.0, total_window - sum_dur)
        gap_count = max(len(group) - 1, 0)
        gap_dur = (slack / gap_count) if gap_count else 0.0

        cursor = t_start
        for j, (ch, iv) in enumerate(group):
            iv_start = cursor
            iv_end = iv_start + ch["duration"]
            aligned.append({
                **iv,
                "start":         round(iv_start, 3),
                "end":           round(iv_end, 3),
                "chunk_num":     ch["num"],
                "chunk_speaker": ch["speaker"],
                "chunk_dur":     round(ch["duration"], 3),
            })
            cursor = iv_end + (gap_dur if j < len(group) - 1 else 0)

    _layout(hook_chunks, hook_start, hook_end)
    _layout(content_chunks, content_start, content_end)

    aligned.sort(key=lambda x: x.get("start", 0))
    log.info(f"  Reconstruidas {len(aligned)} intervenciones desde chunks "
             f"(hook={len(hook_chunks)}, contenido={len(content_chunks)})")
    return aligned


def derive_alignment_from_production(temp_folder: str | Path,
                                      episode_audio_path: str | Path,
                                      interventions: list[dict],
                                      audio_structure: dict,
                                      output_path: str | Path | None = None) -> list[dict]:
    """
    Funcion publica: detecta los chunks de la episode_audio_path en temp_folder
    y los alinea con las intervenciones.
    """
    log = get_logger("production_log_parser")
    audio = Path(episode_audio_path)
    # Inferir prefijo del nombre del audio del episodio
    stem = audio.stem
    # Prefijo posible: EP-MOD000  o  M0_E_Tema (en cuyo caso, el prefijo de
    # los chunks es EP-MOD<algo>; veamos primero si existen).
    candidates = []
    if stem.upper().startswith("EP-MOD") or stem.upper().startswith("EP"):
        candidates.append(stem)
    # Tambien probar EP-MOD000 si nombre del archivo es M0_E_*
    m = re.match(r"^M(\d+)_E_(.+)$", stem)
    if m:
        candidates.append(f"EP-MOD{int(m.group(1)):03d}")

    chunks = []
    for prefix in candidates:
        chunks = list_chunks(temp_folder, episode_prefix=prefix)
        if chunks:
            log.info(f"  Encontrados {len(chunks)} chunks con prefijo {prefix!r}")
            break

    if not chunks:
        log.warning(f"  No se encontraron chunks en {temp_folder} para {audio.name}")
        return []

    aligned = reconstruct_timeline(chunks, interventions, audio_structure)
    if output_path and aligned:
        Path(output_path).write_text(
            json.dumps(aligned, indent=2, ensure_ascii=False),
            encoding="utf-8")
        log.info(f"  Aligned guardado en {output_path}")
    return aligned
