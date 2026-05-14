"""
Paso 05 - Generacion de subtitulos SRT.

NUEVO COMPORTAMIENTO (v2):
- Texto: tomado DEL GUION (limpio: sin SPEAKER:, sin [tono], sin <silence>).
  El guion es la verdad; Whisper se usa solo como fuente de timing.
- Timing: alineamos cada intervencion del guion con los segments de Whisper
  por matching de primeras palabras, y subdividimos cada intervencion en
  bloques de ~7 palabras con timing proporcional.
- Resaltado: keywords y cifras en amarillo CAT.
- El subtitulo NO aparece durante hook/sintonia (lead + sintonia silenciados
  segun audio_structure si esta disponible).
"""

import re
import unicodedata
from pathlib import Path

from .logger import get_logger

# ─── Helpers de texto/normalizacion ───────────────────────────────────────


def _normalize(s: str) -> str:
    s = s.lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _format_timestamp(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms >= 1000:
        ms = 0
        s += 1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _highlight(text: str, keywords: list[str], color: str = "#F5C400") -> str:
    """Sin highlights: el usuario quiere subtitulos 100% blancos.
    Conservamos la firma para compatibilidad con el resto del pipeline."""
    return text


# ─── Alineacion guion <-> Whisper ─────────────────────────────────────────


def _flatten_interventions(content: dict) -> list[dict]:
    """De content_data extrae lista plana de intervenciones limpias."""
    flat = []
    for sec in content.get("sections", []):
        for iv in sec.get("interventions", []):
            text = (iv.get("text") or "").strip()
            if not text:
                continue
            flat.append({
                "section": sec["name"],
                "speaker": iv.get("speaker", ""),
                "text":    text,
            })
    return flat


def _distribute_proportional(interventions: list[dict],
                              t_start: float, t_end: float) -> None:
    """Reparte intervenciones en [t_start, t_end] proporcional al numero de palabras."""
    if t_end <= t_start or not interventions:
        return
    total_words = sum(max(len((iv.get("text") or "").split()), 1)
                      for iv in interventions) or 1
    cursor = float(t_start)
    span = float(t_end - t_start)
    for iv in interventions:
        share = max(len((iv.get("text") or "").split()), 1) / total_words
        dur = span * share
        iv["start"] = round(cursor, 3)
        iv["end"] = round(min(cursor + dur, t_end), 3)
        cursor += dur


def _refine_with_whisper(interventions: list[dict],
                         whisper_words: list[dict],
                         t_start: float, t_end: float) -> int:
    """
    Para cada intervencion intenta afinar `start` buscando sus primeras 4-6
    palabras en Whisper dentro de su ventana asignada (con margen ±15s).
    Si encuentra match, ajusta `start` (y desplaza `end` proporcionalmente).
    Devuelve cuantos matches consiguio.
    """
    matches = 0
    if not whisper_words:
        return 0
    win_words = [(i, w) for i, w in enumerate(whisper_words)
                 if t_start - 5 <= w["start"] <= t_end + 5]
    if not win_words:
        return 0
    norm = [_normalize(w["word"]) for _, w in win_words]
    joined = " ".join(norm)

    for iv in interventions:
        text_norm = _normalize(iv.get("text", ""))
        first_words = text_norm.split()[:6]
        if not first_words:
            continue
        match_pos_word = None
        for n_try in (6, 5, 4, 3):
            needle = " ".join(first_words[:n_try])
            if not needle:
                continue
            # Buscar match cerca del start asignado por proporcionalidad
            pos = joined.find(needle)
            if pos != -1:
                match_pos_word = joined[:pos].count(" ")
                break
        if match_pos_word is None:
            continue
        try:
            new_start = win_words[match_pos_word][1]["start"]
        except IndexError:
            continue
        # Solo aceptar si esta dentro de la ventana razonable (no muy lejos del proporcional)
        if abs(new_start - iv.get("start", 0)) <= 30:
            old_dur = iv["end"] - iv["start"]
            iv["start"] = round(float(new_start), 3)
            iv["end"] = round(float(new_start + old_dur), 3)
            matches += 1
    return matches


def _align_interventions_with_whisper(interventions: list[dict],
                                       whisper_words: list[dict],
                                       content_start: float = 0.0,
                                       content_end: float | None = None,
                                       audio_structure: dict | None = None) -> list[dict]:
    """
    Estrategia v2:
      1. Separar intervenciones por seccion (HOOK vs CONTENIDO).
      2. Distribuir proporcionalmente cada grupo en su rango temporal:
         - HOOK: [hook_start, hook_end]
         - CONTENIDO: [content_start, content_end]
      3. Refinar con matching de palabras Whisper cuando se pueda.

    Asi siempre hay timing aceptable, incluso si Whisper-tiny falla.
    """
    log = get_logger("05_subtitle_generator")
    if not interventions:
        return []

    audio_structure = audio_structure or {}
    hook_start = audio_structure.get("hook_start") or 0.0
    hook_end = audio_structure.get("hook_end")
    if hook_end is None and audio_structure.get("sintonia_start") is not None:
        hook_end = audio_structure["sintonia_start"]
    if hook_end is None:
        hook_end = max(hook_start, 30.0)

    if content_end is None:
        content_end = whisper_words[-1]["end"] if whisper_words else 0.0
    if content_start <= 0:
        content_start = audio_structure.get("content_start") or 0.0

    # Particionar
    SKIP_SECTIONS = {"INTRO_SONIDO", "SINTONIA", "VERIFICACIONES"}
    hook_ivs = []
    content_ivs = []
    for iv in interventions:
        sec = (iv.get("section") or "").upper()
        if sec in SKIP_SECTIONS:
            continue
        if sec == "HOOK":
            hook_ivs.append(dict(iv))
        else:
            content_ivs.append(dict(iv))

    # Distribuir proporcionalmente cada grupo en su rango.
    _distribute_proportional(hook_ivs, hook_start, hook_end)
    _distribute_proportional(content_ivs, content_start, content_end)

    # Refinar con Whisper donde se pueda.
    n1 = _refine_with_whisper(hook_ivs, whisper_words, hook_start, hook_end)
    n2 = _refine_with_whisper(content_ivs, whisper_words, content_start, content_end)
    aligned = hook_ivs + content_ivs

    # Reasegurar orden temporal
    aligned.sort(key=lambda x: x.get("start", 0))
    log.info(f"  Alineamiento: hook={len(hook_ivs)} content={len(content_ivs)} "
             f"matches_whisper={n1+n2}/{len(aligned)}")
    return aligned


def _split_intervention_into_chunks(text: str, start: float, end: float,
                                     max_words: int = 7,
                                     max_dur: float = 3.0) -> list[dict]:
    """Subdivide la intervencion en chunks de subtitulos (~7 palabras / 3s)."""
    words = text.split()
    if not words:
        return []
    total_words = len(words)
    duration = max(end - start, 0.1)
    sec_per_word = duration / total_words

    chunks = []
    cursor_word = 0
    cursor_t = start
    while cursor_word < total_words:
        # tomar hasta max_words o hasta encontrar puntuacion final
        take = 0
        while (take < max_words
               and cursor_word + take < total_words
               and (cursor_word + take + 1) * sec_per_word - cursor_word * sec_per_word < max_dur):
            take += 1
            w = words[cursor_word + take - 1]
            if w.endswith((".", "?", "!", ";")):
                break
        if take == 0:
            take = 1
        chunk_words = words[cursor_word:cursor_word + take]
        chunk_text = " ".join(chunk_words)
        chunk_start = cursor_t
        chunk_end = min(cursor_t + take * sec_per_word, end)
        chunks.append({"text": chunk_text, "start": chunk_start, "end": chunk_end})
        cursor_word += take
        cursor_t = chunk_end
    return chunks


# ─── Funcion publica ──────────────────────────────────────────────────────


def generate_srt(transcription: dict, content: dict,
                 output_folder: str | Path,
                 episode_id: str,
                 max_words: int = 7,
                 max_duration: float = 3.0,
                 force: bool = False,
                 videos_folder: str | Path | None = None,
                 base_name: str | None = None,
                 audio_structure: dict | None = None) -> str:
    """
    Genera el SRT a partir del GUION LIMPIO (no de Whisper).
    Whisper aporta solo los timestamps.
    """
    log = get_logger("05_subtitle_generator")
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    srt_dir = Path(videos_folder) if videos_folder else output_folder
    srt_dir.mkdir(parents=True, exist_ok=True)
    name = base_name or f"{episode_id}_MaquinarIaPesada_videopodcast"
    srt_path = srt_dir / f"{name}.srt"

    if srt_path.exists() and not force:
        log.info(f"SRT cacheado: {srt_path.name}")
        return str(srt_path)

    keywords = content.get("keywords", [])

    # NUEVO ENFOQUE (sincronizacion exacta):
    # Usar directamente las palabras de Whisper (con sus timestamps reales)
    # agrupadas en chunks de ~7 palabras o ~3s, omitiendo el rango de la
    # sintonia para evitar superpoponer subtitulos sobre el intro_video.
    words = transcription.get("words", [])
    if not words:
        log.warning("Whisper sin palabras; SRT vacio.")
        srt_path.write_text("", encoding="utf-8")
        return str(srt_path)

    sintonia_start = (audio_structure or {}).get("sintonia_start")
    sintonia_end = (audio_structure or {}).get("sintonia_end")

    def _in_sintonia(t: float) -> bool:
        return (sintonia_start is not None and sintonia_end is not None
                and sintonia_start <= t <= sintonia_end)

    chunks = []
    current = []
    chunk_start = None
    for w in words:
        # Skip palabras que caen dentro de la sintonia (el intro_video manda)
        if _in_sintonia((w["start"] + w["end"]) / 2):
            if current:
                chunks.append({
                    "start": chunk_start, "end": current[-1]["end"],
                    "text": " ".join(c["word"].strip() for c in current),
                })
                current = []
                chunk_start = None
            continue

        if chunk_start is None:
            chunk_start = w["start"]
        current.append(w)

        # Cierre de chunk si:
        #  a) llegamos al limite de palabras
        #  b) el chunk dura mas de max_duration
        #  c) la palabra termina en . ? !
        text_w = w["word"].strip()
        chunk_dur = w["end"] - chunk_start
        ends_punct = text_w.endswith((".", "?", "!"))
        if (len(current) >= max_words
                or chunk_dur >= max_duration
                or ends_punct):
            chunks.append({
                "start": chunk_start, "end": w["end"],
                "text": " ".join(c["word"].strip() for c in current),
            })
            current = []
            chunk_start = None

    if current:
        chunks.append({
            "start": chunk_start, "end": current[-1]["end"],
            "text": " ".join(c["word"].strip() for c in current),
        })

    # Escribir SRT
    lines = []
    for idx, ck in enumerate(chunks, start=1):
        text_clean = ck["text"].strip()
        if not text_clean:
            continue
        lines.append(str(idx))
        lines.append(f"{_format_timestamp(ck['start'])} --> {_format_timestamp(ck['end'])}")
        lines.append(_highlight(text_clean, keywords))
        lines.append("")

    srt_path.write_text("\n".join(lines), encoding="utf-8")
    log.info(f"SRT generado: {len(chunks)} chunks desde Whisper word-level -> {srt_path.name}")
    return str(srt_path)
