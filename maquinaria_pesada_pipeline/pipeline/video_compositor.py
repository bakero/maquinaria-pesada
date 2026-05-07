"""
Paso 06 - Composicion final con ffmpeg.

Estructura:
1. intro_video (asset configurado)
2. cuerpo del episodio: secuencia de frames PNG con su duracion + audio
   con subtitulos quemados.
Concatenamos ambos en MP4 final con libx264 + aac.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .logger import get_logger
from .brand import RESOLUTIONS


def _run(cmd: list[str], log) -> None:
    log.debug("FFMPEG: " + " ".join(str(c) for c in cmd))
    try:
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if proc.stderr:
            log.debug(proc.stderr[-2000:])
    except subprocess.CalledProcessError as exc:
        log.error("ffmpeg fallo: " + (exc.stderr or "")[-3000:])
        raise


def _build_concat_list(frames: list[dict], list_path: Path) -> None:
    lines = []
    for f in frames:
        path = Path(f["path"]).resolve().as_posix()
        lines.append(f"file '{path}'")
        lines.append(f"duration {max(f['duration'], 0.05):.3f}")
    # ffmpeg concat exige duplicar el ultimo file sin duration
    if frames:
        last = Path(frames[-1]["path"]).resolve().as_posix()
        lines.append(f"file '{last}'")
    list_path.write_text("\n".join(lines), encoding="utf-8")


def _escape_srt_for_ffmpeg(srt_path: Path) -> str:
    p = srt_path.resolve().as_posix()
    if os.name == "nt":
        p = p.replace(":", "\\:")
    return p.replace("'", "\\'")


def compose_video(config: dict,
                  frames_index: dict,
                  audio_path: str | Path,
                  srt_path: str | Path,
                  output_folder: str | Path,
                  episode_id: str,
                  preview: bool = False) -> str:
    """Devuelve la ruta del MP4 final."""
    log = get_logger("06_video_compositor")
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    suffix = "_preview" if preview else ""
    final_path = output_folder / f"{episode_id}{suffix}_videopodcast.mp4"

    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg no esta en el PATH. Instalalo antes de continuar.")

    res_str = config.get("episode_defaults", {}).get("resolution", "1920x1080")
    if preview:
        res_str = "1280x720"
    w, h = RESOLUTIONS.get(res_str, (1920, 1080))

    intro_video = config["assets"].get("intro_video")
    logo = config["assets"].get("logo_watermark")
    frames = frames_index.get("frames", [])

    if not frames:
        raise RuntimeError("No hay frames en frames_index.")

    workdir = output_folder / "_compose_tmp"
    workdir.mkdir(parents=True, exist_ok=True)
    concat_list = workdir / "frames_concat.txt"
    _build_concat_list(frames, concat_list)

    body_video = workdir / f"body{suffix}.mp4"
    body_with_audio = workdir / f"body_audio{suffix}.mp4"

    # 1) Crear video de frames con duraciones (sin audio).
    cmd_body = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-vf", f"scale={w}:{h}:flags=lanczos,format=yuv420p,fps=30",
        "-c:v", "libx264", "-preset", "veryfast" if preview else "slow",
        "-crf", "23" if preview else "18",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        str(body_video),
    ]
    _run(cmd_body, log)

    # 2) Mezclar con audio + subtitulos quemados.
    duration_audio = float(frames_index.get("duration", 0)) or sum(f["duration"] for f in frames)

    srt_filter = ""
    if srt_path and Path(srt_path).exists():
        esc = _escape_srt_for_ffmpeg(Path(srt_path))
        srt_filter = (
            f",subtitles='{esc}':force_style="
            f"'FontName=Arial,Fontsize=22,PrimaryColour=&H00E8E8E8,"
            f"OutlineColour=&H00000000,BorderStyle=1,Outline=2,"
            f"Shadow=0,MarginV=60,Alignment=2'"
        )

    cmd_mix = [
        "ffmpeg", "-y",
        "-i", str(body_video),
        "-i", str(audio_path),
        "-filter_complex",
        f"[0:v]format=yuv420p{srt_filter}[v]",
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast" if preview else "slow",
        "-crf", "23" if preview else "18",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(body_with_audio),
    ]
    _run(cmd_mix, log)

    # 3) Concatenar intro + cuerpo si hay intro
    if intro_video and Path(intro_video).exists():
        intro_norm = workdir / "intro_norm.mp4"
        cmd_intro = [
            "ffmpeg", "-y",
            "-i", str(intro_video),
            "-vf", f"scale={w}:{h}:flags=lanczos,format=yuv420p,fps=30",
            "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
            "-c:a", "aac", "-b:a", "192k",
            "-ar", "48000", "-ac", "2",
            str(intro_norm),
        ]
        _run(cmd_intro, log)

        # Asegurar que body_with_audio tambien usa 48k stereo
        body_norm = workdir / f"body_norm{suffix}.mp4"
        cmd_norm = [
            "ffmpeg", "-y",
            "-i", str(body_with_audio),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            str(body_norm),
        ]
        _run(cmd_norm, log)

        concat_final = workdir / "concat_final.txt"
        concat_final.write_text(
            f"file '{intro_norm.resolve().as_posix()}'\n"
            f"file '{body_norm.resolve().as_posix()}'\n",
            encoding="utf-8",
        )
        cmd_final = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_final),
            "-c", "copy", "-movflags", "+faststart",
            str(final_path),
        ]
        _run(cmd_final, log)
    else:
        shutil.copyfile(body_with_audio, final_path)

    log.info(f"Video final generado: {final_path}")
    return str(final_path)
