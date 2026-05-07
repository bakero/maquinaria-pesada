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
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .logger import get_logger
from .brand import RESOLUTIONS


def derive_video_basename(audio_path: str | Path | None,
                          episode_id: str) -> str:
    """
    Deduce el nombre base del video siguiendo la nomenclatura del proyecto.

    Si el audio se llama  MX_E_<Tema>.mp3  -> devuelve  MX_V_<Tema>
    En cualquier otro caso devuelve  <episode_id>_MaquinarIaPesada_videopodcast
    """
    if audio_path:
        stem = Path(audio_path).stem  # sin extension
        m = re.match(r"^(M\d+)_E_(.+)$", stem)
        if m:
            return f"{m.group(1)}_V_{m.group(2)}"
    return f"{episode_id}_MaquinarIaPesada_videopodcast"


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
                  preview: bool = False,
                  audio_structure: dict | None = None,
                  scene_track: list[dict] | None = None) -> str:
    """
    Devuelve la ruta del MP4 final.

    Estructura del video resultante (sincronizado con el audio del episodio,
    que YA contiene hook + sintonia + contenido):
       [0 ─── lead silence ─── HOOK ─── sintonia (intro_video overlay) ─── CONTENIDO ──]
    Los frames generados (con overlays/stickers) se muestran encima del
    cuerpo, pero durante la sintonia se muestra el intro_video.
    """
    log = get_logger("06_video_compositor")
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    videos_folder_cfg = config.get("assets", {}).get("videos_folder")
    final_dir = Path(videos_folder_cfg) if videos_folder_cfg else output_folder
    final_dir.mkdir(parents=True, exist_ok=True)
    suffix = "_preview" if preview else ""
    base_name = derive_video_basename(audio_path, episode_id)
    final_path = final_dir / f"{base_name}{suffix}.mp4"

    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg no esta en el PATH.")

    # La resolucion del config manda; el modo preview ya no la baja a 720p.
    res_str = config.get("episode_defaults", {}).get("resolution", "1920x1080")
    w, h = RESOLUTIONS.get(res_str, (1920, 1080))

    intro_video = config["assets"].get("intro_video")
    frames = frames_index.get("frames", [])
    if not frames:
        raise RuntimeError("No hay frames en frames_index.")

    workdir = output_folder / "_compose_tmp"
    workdir.mkdir(parents=True, exist_ok=True)
    body_video = workdir / f"body{suffix}.mp4"

    # 1) Construir el body alternando PIZARRA / ESTUDIO / BLANK si tenemos
    #    scene_track. Si no, fallback al modo legacy (todo pizarra).
    if scene_track:
        _build_body_from_track(
            scene_track, frames, workdir, body_video, w, h,
            preview=preview, log=log,
        )
    else:
        concat_list = workdir / "frames_concat.txt"
        _build_concat_list(frames, concat_list)
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

    # 2) Si tenemos audio_structure con sintonia detectada y un intro_video,
    #    creamos un video de sintonia normalizado y lo overlay-amos sobre body
    #    en ese rango exacto.
    sintonia_start = (audio_structure or {}).get("sintonia_start")
    sintonia_end = (audio_structure or {}).get("sintonia_end")
    sintonia_dur = None
    if sintonia_start is not None and sintonia_end is not None:
        sintonia_dur = max(0.0, float(sintonia_end) - float(sintonia_start))

    intro_overlay_video = None
    if (intro_video and Path(intro_video).exists()
            and sintonia_dur and sintonia_dur > 0.5):
        intro_overlay_video = workdir / "intro_overlay.mp4"
        # Recortar/extender intro_video a la duracion exacta de la sintonia
        # (sin audio: el audio del episodio ya lo lleva)
        cmd_intro = [
            "ffmpeg", "-y",
            "-i", str(intro_video),
            "-an",
            "-vf",
            f"scale={w}:{h}:flags=lanczos,format=yuv420p,fps=30,"
            f"tpad=stop_mode=clone:stop_duration={max(0, sintonia_dur - _intro_dur(intro_video)):.3f}",
            "-t", f"{sintonia_dur:.3f}",
            "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
            str(intro_overlay_video),
        ]
        _run(cmd_intro, log)

    # 3) Filter complex final: body + audio + intro overlay sobre sintonia + subs.
    inputs = ["-i", str(body_video), "-i", str(audio_path)]
    filter_parts = []

    if intro_overlay_video:
        inputs += ["-i", str(intro_overlay_video)]
        # Hacemos que el intro_overlay aparezca solo entre sintonia_start y sintonia_end.
        # 1) Retrasar el intro_overlay con setpts para que su t=0 coincida con sintonia_start.
        # 2) Componer encima del body con enable.
        filter_parts.append(
            f"[2:v]setpts=PTS+{float(sintonia_start):.3f}/TB[introv]"
        )
        filter_parts.append(
            f"[0:v][introv]overlay=x=0:y=0:enable='between(t,{float(sintonia_start):.3f},{float(sintonia_end):.3f})'[v0]"
        )
        v_in = "[v0]"
    else:
        v_in = "[0:v]"

    # Subtitulos quemados al final del filtro de video
    if srt_path and Path(srt_path).exists():
        esc = _escape_srt_for_ffmpeg(Path(srt_path))
        # Subtitulos a la franja inferior de la pantalla:
        # MarginV en pixeles desde abajo. ~30 los pega bien al borde.
        # Fontsize 32 a 1080p (escala desde el ratio del video).
        font_size = 32 if h >= 1080 else 22
        srt_chain = (
            f"subtitles='{esc}':force_style="
            f"'FontName=Arial,Fontsize={font_size},PrimaryColour=&H00E8E8E8,"
            f"OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=0,"
            f"MarginV=30,Alignment=2'"
        )
        filter_parts.append(f"{v_in}{srt_chain}[v]")
    else:
        filter_parts.append(f"{v_in}null[v]")

    filter_complex = ";".join(filter_parts)

    cmd_final = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "veryfast" if preview else "slow",
        "-crf", "23" if preview else "18",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-shortest",
        "-movflags", "+faststart",
        str(final_path),
    ]
    _run(cmd_final, log)

    log.info(f"Video final generado: {final_path}")
    if sintonia_start is not None:
        log.info(f"  intro_video overlay aplicado en [{sintonia_start:.2f}s, {sintonia_end:.2f}s]")
    return str(final_path)


def _build_body_from_track(scene_track: list[dict],
                            pizarra_frames: list[dict],
                            workdir: Path,
                            body_out: Path,
                            w: int, h: int,
                            preview: bool = False,
                            log=None) -> None:
    """
    Construye body_video alternando segmentos pizarra / estudio / blank.
    Cada segmento se materializa como un MP4 normalizado a (w,h,30fps).
    Despues los concatena con concat demuxer.
    """
    log = log or get_logger("06_video_compositor")
    workdir.mkdir(parents=True, exist_ok=True)
    seg_clips = []

    # Filtro vf comun: scale + format + fps. NOTA: 'format' es un filtro
    # independiente, separado del scale por COMA (no por dos puntos).
    vf_common = f"scale={w}:{h}:flags=lanczos,format=yuv420p,fps=30"
    vf_blank = f"scale={w}:{h},format=yuv420p,fps=30"  # sin lanczos para PNG simple

    for i, seg in enumerate(scene_track):
        seg_dur = max(0.05, float(seg.get("end", 0)) - float(seg.get("start", 0)))
        seg_clip = workdir / f"seg_{i:03d}_{seg['type']}.mp4"

        if seg["type"] == "blank":
            # Frame neutro (rejilla industrial) para silencios y rango sintonia.
            blank = workdir / f"seg_{i:03d}_blank.png"
            try:
                import sys as _sys
                _root = Path(__file__).parent.parent
                if str(_root) not in _sys.path:
                    _sys.path.insert(0, str(_root))
                from templates.background_generators import get_background  # type: ignore
                bg = get_background("industrial_grid", w, h)
                bg.save(blank, "PNG")
            except Exception:
                from PIL import Image as _Image
                _Image.new("RGB", (w, h), (13, 13, 13)).save(blank, "PNG")
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-t", f"{seg_dur:.3f}", "-i", str(blank),
                "-vf", vf_blank,
                "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "23", "-pix_fmt", "yuv420p", "-r", "30",
                "-an", str(seg_clip),
            ]
            _run(cmd, log)
        elif seg["type"] == "estudio" and seg.get("source"):
            src_dur = _intro_dur(seg["source"]) or seg_dur
            loops = max(0, int(seg_dur // max(src_dur, 0.1)))
            cmd = [
                "ffmpeg", "-y",
                "-stream_loop", str(loops), "-i", str(seg["source"]),
                "-t", f"{seg_dur:.3f}",
                "-an",
                "-vf", vf_common,
                "-c:v", "libx264", "-preset", "veryfast" if preview else "medium",
                "-crf", "23" if preview else "20",
                "-pix_fmt", "yuv420p", "-r", "30",
                str(seg_clip),
            ]
            _run(cmd, log)
        else:
            # PIZARRA: frames PNG que solapan el segmento
            local_frames = [
                f for f in pizarra_frames
                if f["end"] > seg["start"] and f["start"] < seg["end"]
            ]
            if not local_frames:
                # Fallback a blank
                blank = workdir / f"seg_{i:03d}_fallback.png"
                from PIL import Image as _Image
                _Image.new("RGB", (w, h), (13, 13, 13)).save(blank, "PNG")
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1", "-t", f"{seg_dur:.3f}", "-i", str(blank),
                    "-vf", vf_blank,
                    "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "23", "-pix_fmt", "yuv420p", "-r", "30",
                    "-an", str(seg_clip),
                ]
                _run(cmd, log)
            else:
                concat = workdir / f"seg_{i:03d}_pizarra_concat.txt"
                lines = []
                for f in local_frames:
                    f_start = max(float(f["start"]), float(seg["start"]))
                    f_end = min(float(f["end"]), float(seg["end"]))
                    f_dur = max(0.05, f_end - f_start)
                    p = Path(f["path"]).resolve().as_posix()
                    lines.append(f"file '{p}'")
                    lines.append(f"duration {f_dur:.3f}")
                last = Path(local_frames[-1]["path"]).resolve().as_posix()
                lines.append(f"file '{last}'")
                concat.write_text("\n".join(lines), encoding="utf-8")
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "concat", "-safe", "0",
                    "-i", str(concat),
                    "-t", f"{seg_dur:.3f}",
                    "-vf", vf_common,
                    "-c:v", "libx264", "-preset", "veryfast" if preview else "medium",
                    "-crf", "23" if preview else "20",
                    "-pix_fmt", "yuv420p", "-r", "30",
                    "-an", str(seg_clip),
                ]
                _run(cmd, log)
        seg_clips.append(seg_clip)

    # Concatenar todos los clips (mismo formato/fps/res)
    final_concat = workdir / "body_concat.txt"
    final_concat.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in seg_clips),
        encoding="utf-8",
    )
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(final_concat),
        "-c", "copy",
        str(body_out),
    ]
    _run(cmd, log)
    log.info(f"  body_video construido desde track: {len(seg_clips)} segmentos")


def _intro_dur(path: str | Path) -> float:
    """Duracion del intro_video.mp4 (para tpad)."""
    if shutil.which("ffprobe") is None:
        return 0.0
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ], text=True).strip()
        return float(out)
    except Exception:
        return 0.0
