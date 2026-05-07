"""
Paso 01 - Transcripcion con timestamps por palabra (Whisper).
Cachea el resultado en JSON para no repetir el trabajo en re-runs.
"""

import json
from pathlib import Path

from .logger import get_logger


def transcribe_episode(audio_path: str | Path,
                       output_folder: str | Path,
                       model_size: str = "large-v3",
                       language: str = "es",
                       force: bool = False) -> dict:
    """
    Usa Whisper para obtener timestamps por PALABRA individual.
    Cachea resultado en JSON.

    Args:
        audio_path: Ruta al archivo de audio (mp3/wav).
        output_folder: Carpeta donde se guarda transcription_raw.json.
        model_size: tiny, base, small, medium, large-v3.
        language: idioma del audio.
        force: si True, ignora cache y re-transcribe.

    Returns dict con: audio_file, duration_seconds, language, words, full_text.
    """
    log = get_logger("01_transcriber")
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    cache = output_folder / "transcription_raw.json"

    if cache.exists() and not force:
        log.info(f"Transcripcion cacheada encontrada: {cache.name}")
        return json.loads(cache.read_text(encoding="utf-8"))

    audio_path = str(Path(audio_path).resolve())
    log.info(f"Cargando modelo Whisper: {model_size}")

    try:
        import whisper  # openai-whisper
    except ImportError as exc:
        raise RuntimeError(
            "Falta el paquete 'openai-whisper'. Instalalo con: "
            "pip install openai-whisper"
        ) from exc

    model = whisper.load_model(model_size)

    log.info(f"Transcribiendo: {audio_path}")
    result = model.transcribe(
        audio_path,
        word_timestamps=True,
        language=language,
        task="transcribe",
        verbose=False,
    )

    words = []
    for seg in result.get("segments", []):
        for w in seg.get("words", []) or []:
            text = (w.get("word") or "").strip()
            if not text:
                continue
            words.append({
                "word":  text,
                "start": round(float(w.get("start", 0.0)), 3),
                "end":   round(float(w.get("end", 0.0)), 3),
            })

    duration = (
        float(result["segments"][-1]["end"]) if result.get("segments") else 0.0
    )

    output = {
        "audio_file":       audio_path,
        "duration_seconds": round(duration, 3),
        "language":         language,
        "model":            model_size,
        "words":            words,
        "segments":         [
            {
                "id":    s.get("id"),
                "start": round(float(s.get("start", 0)), 3),
                "end":   round(float(s.get("end", 0)), 3),
                "text":  s.get("text", "").strip(),
            }
            for s in result.get("segments", [])
        ],
        "full_text":        result.get("text", "").strip(),
    }

    cache.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"Transcripcion guardada: {len(words)} palabras, {duration:.1f}s")
    return output


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("audio")
    parser.add_argument("--out", default="./outputs")
    parser.add_argument("--model", default="large-v3")
    parser.add_argument("--lang", default="es")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    transcribe_episode(args.audio, args.out, args.model, args.lang, args.force)
