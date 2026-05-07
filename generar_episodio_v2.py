#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys
import time
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import glob as _glob
from dotenv import load_dotenv

from podcast_spec import (
    DEFAULT_SPEC_PATH,
    extract_leading_tag,
    load_master_spec,
    parse_script_blocks,
    validate_script_text,
)


load_dotenv(override=True)

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def setup_ffmpeg() -> None:
    import shutil

    winget_candidates = sorted(
        _glob.glob(
            r"C:\Users\Asus\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg-*\bin\ffmpeg.exe"
        ),
        reverse=True,
    )
    if winget_candidates:
        ffmpeg_dir = str(Path(winget_candidates[0]).parent)
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
        return
    if shutil.which("ffmpeg"):
        return
    capcut_candidates = sorted(
        _glob.glob(r"C:\Users\Asus\AppData\Local\CapCut\Apps\*\ffmpeg.exe"),
        reverse=True,
    )
    if capcut_candidates:
        ffmpeg_dir = str(Path(capcut_candidates[0]).parent)
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")


setup_ffmpeg()

try:
    import httpx
    from elevenlabs import VoiceSettings
    from elevenlabs.client import ElevenLabs
    from pydub import AudioSegment
except ImportError as exc:
    raise SystemExit(
        "Faltan dependencias. Ejecuta: pip install elevenlabs pydub httpx"
    ) from exc


@dataclass
class SubscriptionSnapshot:
    used: int | None
    limit: int | None

    @property
    def remaining(self) -> int | None:
        if self.used is None or self.limit is None:
            return None
        return self.limit - self.used


def load_runtime(spec_path: str | Path) -> tuple[dict, Path, Path, Path, Path | None, Path | None]:
    spec = load_master_spec(spec_path)
    output_dir = Path(spec["directories"]["output_dir"])
    temp_dir = Path(spec["directories"]["temp_dir"])
    music_path = output_dir / "background_music_raw.mp3"
    background_bed_path = Path(spec["audio_rules"].get("background_bed_path", "")) if spec["audio_rules"].get("background_bed_path") else None
    intro_theme_path = Path(spec["audio_rules"].get("intro_theme_path", "")) if spec["audio_rules"].get("intro_theme_path") else None
    output_dir.mkdir(exist_ok=True)
    temp_dir.mkdir(exist_ok=True)
    if background_bed_path and not background_bed_path.is_absolute():
        background_bed_path = Path.cwd() / background_bed_path
    if intro_theme_path and not intro_theme_path.is_absolute():
        intro_theme_path = Path.cwd() / intro_theme_path
    return spec, output_dir, temp_dir, music_path, background_bed_path, intro_theme_path


def get_voice_config(spec: dict, speaker: str) -> dict:
    return spec["audio_rules"]["voices"][speaker]


def speaker_display(spec: dict, speaker: str) -> str:
    return spec["speakers"][speaker]["display_name"]


def parsear_guion(ruta_guion: str, ep_code: str, spec: dict) -> list[dict]:
    text = Path(ruta_guion).read_text(encoding="utf-8")
    issues = validate_script_text(text, ep_code, spec)

    if issues:
        # Separar issues ESTRUCTURALES (fatales) de issues de CALIDAD (advertencias)
        HARD_KEYWORDS = (
            "falta la seccion",
            "fuera de orden",
            "no contiene bloques",
            "debe abrirlo",
            "menos de 4 bloques",
            "mas de 6 bloques",
            "falta la frase",
            "falta la instruccion",
            "falta la apertura",
        )
        hard_issues = [
            i for i in issues
            if any(kw in i.lower() for kw in HARD_KEYWORDS)
        ]
        soft_issues = [i for i in issues if i not in hard_issues]

        if hard_issues:
            issue_text = "\n".join(f"- {i}" for i in hard_issues)
            raise SystemExit(
                "La validacion obligatoria del guion ha fallado antes de sintetizar:\n"
                f"{issue_text}"
            )
        if soft_issues:
            print("[WARN] Problemas de calidad detectados en el guion (no fatales):")
            for i in soft_issues:
                print(f"  - {i}")

    blocks = parse_script_blocks(text, spec)
    for block in blocks:
        block["voice_id"] = get_voice_config(spec, block["speaker"])["voice_id"]
        block["speaker_label"] = speaker_display(spec, block["speaker"])
        block["tag"] = extract_leading_tag(block["text"])
    return blocks


def get_subscription_snapshot(api_key: str) -> SubscriptionSnapshot:
    try:
        response = httpx.get(
            "https://api.elevenlabs.io/v1/user/subscription",
            headers={"xi-api-key": api_key},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return SubscriptionSnapshot(
            used=data.get("character_count"),
            limit=data.get("character_limit"),
        )
    except Exception:
        return SubscriptionSnapshot(used=None, limit=None)


def print_credit_summary(prefix: str, snapshot: SubscriptionSnapshot) -> None:
    if snapshot.used is None or snapshot.limit is None:
        print(f"{prefix} creditos ElevenLabs restantes: desconocido (API no disponible)")
        return
    print(f"{prefix} creditos ElevenLabs usados: {snapshot.used}")
    print(f"{prefix} creditos ElevenLabs restantes: {snapshot.remaining}")


def generar_bloque(client: ElevenLabs, bloque: dict, ep: str, temp_dir: Path, spec: dict, reintentos: int = 3) -> Path | None:
    speaker = bloque["speaker"]
    texto = bloque["text"]
    indice = bloque["index"]
    config = get_voice_config(spec, speaker)
    nombre_archivo = temp_dir / f"{ep}_{indice:03d}_{speaker}.mp3"

    for intento in range(1, reintentos + 1):
        try:
            print(f"  [{indice:03d}] {speaker} - generando... (intento {intento})")
            audio_generator = client.text_to_speech.convert(
                voice_id=config["voice_id"],
                text=texto,
                model_id=spec["audio_rules"]["model"],
                voice_settings=VoiceSettings(
                    stability=config["stability"],
                    similarity_boost=config["similarity_boost"],
                    style=config["style"],
                    use_speaker_boost=config["use_speaker_boost"],
                    speed=config["speed"],
                ),
                output_format=spec["audio_rules"]["output_format"],
            )
            with open(nombre_archivo, "wb") as file_handle:
                for chunk in audio_generator:
                    if chunk:
                        file_handle.write(chunk)
            print(f"  [{indice:03d}] {speaker} - guardado: {nombre_archivo.name}")
            return nombre_archivo
        except Exception as exc:
            # Errores permanentes: abortar sin reintentar
            status = getattr(exc, "status_code", None)
            if status in (401, 403):
                raise SystemExit(
                    f"\nERROR FATAL: ElevenLabs rechazó la autenticación ({status}).\n"
                    "Comprueba que ELEVENLABS_API_KEY en el fichero .env es válida y está activa."
                ) from exc
            print(f"  [{indice:03d}] {speaker} - ERROR intento {intento}: {exc}")
            if intento < reintentos:
                wait_seconds = 5 * intento
                print(f"  Esperando {wait_seconds}s antes de reintentar...")
                time.sleep(wait_seconds)
            else:
                print(f"  [{indice:03d}] FALLO DEFINITIVO. Bloque omitido.")
                return None
    return None


def generar_musica(api_key: str, ruta_destino: Path, spec: dict) -> bool:
    print("\nGenerando musica de fondo via ElevenLabs...")
    try:
        response = httpx.post(
            "https://api.elevenlabs.io/v1/sound-generation",
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": spec["audio_rules"]["music_prompt"],
                "duration_seconds": spec["audio_rules"]["music_duration_seconds"],
                "prompt_influence": spec["audio_rules"]["music_prompt_influence"],
            },
            timeout=120.0,
        )
        response.raise_for_status()
        ruta_destino.write_bytes(response.content)
        print(f"  Musica guardada en: {ruta_destino}")
        return True
    except Exception as exc:
        print(f"  ERROR generando musica: {exc}")
        return False


def build_spoken_sequence(
    archivos: list[tuple[Path | None, dict]], spec: dict
) -> tuple[AudioSegment, list[tuple[int, dict]]]:
    """Devuelve (audio, [(offset_ms_relativo, bloque), ...])."""
    audio_rules = spec["audio_rules"]
    sequence = AudioSegment.silent(duration=0)
    previous_speaker = None
    timestamps: list[tuple[int, dict]] = []
    current_ms = 0
    for ruta, bloque in archivos:
        if ruta is None:
            continue
        speaker = bloque["speaker"]
        if previous_speaker is not None:
            pause_ms = (
                audio_rules["same_speaker_pause_ms"]
                if speaker == previous_speaker
                else audio_rules["different_speaker_pause_ms"]
            )
            sequence += AudioSegment.silent(duration=pause_ms)
            current_ms += pause_ms
        timestamps.append((current_ms, bloque))
        seg = AudioSegment.from_mp3(str(ruta))
        sequence += seg
        current_ms += len(seg)
        previous_speaker = speaker
    return sequence, timestamps


def loop_music_segment(source: AudioSegment, duration_ms: int) -> AudioSegment:
    if duration_ms <= 0:
        return AudioSegment.silent(duration=0)
    repetitions = (duration_ms // len(source)) + 2
    return (source * repetitions)[:duration_ms]


def montar_audio(
    archivos: list[tuple[Path | None, dict]],
    ruta_final: Path,
    spec: dict,
    ruta_musica: Path | None,
    ruta_sintonia: Path | None,
) -> tuple[float, list[dict]]:
    """Monta el episodio y devuelve (duracion_s, escaleta).

    La escaleta es una lista de dicts con claves:
      - time_ms: timestamp absoluto en el audio final (ya con post_speed aplicado)
      - event: 'INICIO' | 'SINTONIA_START' | 'SINTONIA_END' | 'BLOQUE'
      - speaker, section, index, tag  (solo para event='BLOQUE')
    """
    print("\nMontando audio final...")
    audio_rules = spec["audio_rules"]
    hook_archivos = [item for item in archivos if item[1].get("section") == "HOOK"]
    rest_archivos = [item for item in archivos if item[1].get("section") != "HOOK"]

    hook_audio, hook_ts = build_spoken_sequence(hook_archivos, spec)
    rest_audio, rest_ts = build_spoken_sequence(rest_archivos, spec)

    episode = AudioSegment.silent(duration=0)
    base_music = None
    theme_music = None
    escaleta: list[dict] = []
    current_ms = 0

    if ruta_musica and ruta_musica.exists():
        print("  Cargando base musical definitiva...")
        base_music = AudioSegment.from_mp3(str(ruta_musica)) + audio_rules["background_music_db"]
    if ruta_sintonia and ruta_sintonia.exists():
        print("  Cargando sintonia definitiva...")
        theme_music = AudioSegment.from_mp3(str(ruta_sintonia))

    escaleta.append({"time_ms": 0, "event": "INICIO"})

    # Pre-hook bed
    pre_hook_ms = audio_rules["pre_hook_bed_ms"]
    if base_music is not None:
        episode += loop_music_segment(base_music, pre_hook_ms)
    else:
        episode += AudioSegment.silent(duration=pre_hook_ms)
    current_ms += pre_hook_ms

    # Hook
    hook_start_ms = current_ms
    for rel_ms, bloque in hook_ts:
        escaleta.append({
            "time_ms": hook_start_ms + rel_ms,
            "event": "BLOQUE",
            "speaker": bloque["speaker"],
            "section": bloque.get("section", "HOOK"),
            "index": bloque["index"],
            "tag": bloque.get("tag", ""),
        })
    if base_music is not None:
        if len(hook_audio) > 0:
            hook_bed = loop_music_segment(base_music, len(hook_audio))
            episode += hook_bed.overlay(hook_audio)
    else:
        episode += hook_audio
    current_ms += len(hook_audio)

    # Post-hook bed
    post_hook_ms = audio_rules["post_hook_bed_ms"]
    if base_music is not None:
        post_hook = loop_music_segment(base_music, post_hook_ms).fade_out(
            audio_rules["post_hook_bed_fade_out_ms"]
        )
        episode += post_hook
    else:
        episode += AudioSegment.silent(duration=post_hook_ms)
    current_ms += post_hook_ms

    # Sintonía
    if theme_music is not None:
        escaleta.append({"time_ms": current_ms, "event": "SINTONIA_START"})
        episode += theme_music
        current_ms += len(theme_music)
        escaleta.append({"time_ms": current_ms, "event": "SINTONIA_END"})

    # Post-intro bed + voz principal
    post_intro_bed_ms = audio_rules["post_intro_bed_ms"]
    final_tail_ms = audio_rules["final_bed_tail_ms"]
    rest_start_ms = current_ms + post_intro_bed_ms
    for rel_ms, bloque in rest_ts:
        escaleta.append({
            "time_ms": rest_start_ms + rel_ms,
            "event": "BLOQUE",
            "speaker": bloque["speaker"],
            "section": bloque.get("section", ""),
            "index": bloque["index"],
            "tag": bloque.get("tag", ""),
        })

    if base_music is not None:
        bed_track = loop_music_segment(base_music, post_intro_bed_ms + len(rest_audio) + final_tail_ms)
        bed_track = bed_track.fade_out(audio_rules["final_bed_tail_fade_out_ms"])
        voice_track = AudioSegment.silent(duration=post_intro_bed_ms) + rest_audio + AudioSegment.silent(duration=final_tail_ms)
        episode += bed_track.overlay(voice_track)
    else:
        episode += AudioSegment.silent(duration=post_intro_bed_ms)
        episode += rest_audio
        episode += AudioSegment.silent(duration=final_tail_ms)

    episode = episode.normalize()
    episode = episode.apply_gain(audio_rules["normalization_target_dbfs"] - episode.dBFS)

    episode.export(
        str(ruta_final),
        format="mp3",
        bitrate=spec["audio_rules"]["export_bitrate"],
        tags={
            "title": spec["project_name"],
            "artist": spec["project_name"],
            "comment": "Generado automaticamente con IA",
        },
    )
    post_speed_multiplier = float(audio_rules.get("post_speed_multiplier", 1.0) or 1.0)
    if abs(post_speed_multiplier - 1.0) > 1e-6:
        ruta_tmp = ruta_final.with_name(ruta_final.stem + "_postspeed_tmp.mp3")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(ruta_final),
                "-filter:a",
                f"atempo={post_speed_multiplier:.3f}",
                "-b:a",
                spec["audio_rules"]["export_bitrate"],
                str(ruta_tmp),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ruta_tmp.replace(ruta_final)
        episode = AudioSegment.from_mp3(str(ruta_final))
        # Ajustar timestamps de escaleta al speed final
        for entry in escaleta:
            entry["time_ms"] = int(entry["time_ms"] / post_speed_multiplier)

    return len(episode) / 1000.0, escaleta


def verify_audio_output(ruta_final: Path, bloques: list[dict], generated_ok: int, spec: dict, require_full_duration: bool = True) -> list[str]:
    issues: list[str] = []
    if generated_ok != len(bloques):
        issues.append(f"Solo se generaron {generated_ok}/{len(bloques)} bloques.")
    if not ruta_final.exists():
        issues.append(f"No existe el archivo final {ruta_final}.")
        return issues
    try:
        audio = AudioSegment.from_mp3(str(ruta_final))
    except Exception as exc:
        issues.append(f"No se pudo abrir el MP3 final: {exc}")
        return issues

    duration_minutes = len(audio) / 60000.0
    if require_full_duration:
        minimum = spec["episode_defaults"]["minimum_audio_minutes"]
        maximum = spec["episode_defaults"]["maximum_audio_minutes"]
        if duration_minutes < minimum:
            issues.append(
                f"La duracion final es demasiado corta: {duration_minutes:.2f} min."
            )
        if duration_minutes > maximum:
            issues.append(
                f"La duracion final es demasiado larga: {duration_minutes:.2f} min."
            )
    return issues


def verify_production_assets(
    background_bed_path: Path | None,
    intro_theme_path: Path | None,
    bloques: list[dict],
) -> tuple[list[str], list[str]]:
    """Verifica musica de fondo, sintonia e identifica bloques con I.A. para revision auditiva."""
    from podcast_spec import remove_leading_tag
    issues: list[str] = []
    info_lines: list[str] = []

    # Verificar musica de fondo
    if background_bed_path is None:
        issues.append("MUSICA: No se ha configurado ruta de musica de fondo en el spec.")
    elif not background_bed_path.exists():
        issues.append(f"MUSICA: Archivo no encontrado: {background_bed_path}")
    else:
        try:
            bed = AudioSegment.from_mp3(str(background_bed_path))
            info_lines.append(
                f"MUSICA DE FONDO: {background_bed_path.name} ({len(bed) / 1000:.1f}s) - OK"
            )
        except Exception as exc:
            issues.append(f"MUSICA: Error al leer el archivo: {exc}")

    # Verificar sintonia
    if intro_theme_path is None:
        issues.append("SINTONIA: No se ha configurado ruta de sintonia en el spec.")
    elif not intro_theme_path.exists():
        issues.append(f"SINTONIA: Archivo no encontrado: {intro_theme_path}")
    else:
        try:
            theme = AudioSegment.from_mp3(str(intro_theme_path))
            info_lines.append(
                f"SINTONIA:       {intro_theme_path.name} ({len(theme) / 1000:.1f}s) - OK"
            )
        except Exception as exc:
            issues.append(f"SINTONIA: Error al leer el archivo: {exc}")

    # Listar bloques con menciones de I.A. para revision auditiva manual
    ia_blocks = []
    for block in bloques:
        text = remove_leading_tag(block["text"])
        if "I.A." in text:
            ia_blocks.append(block["index"])
    if ia_blocks:
        info_lines.append(
            f"BLOQUES CON I.A. (verificar pronunciacion en audio): {ia_blocks}"
        )
    else:
        info_lines.append("BLOQUES CON I.A.: ninguno detectado.")

    return issues, info_lines


def guardar_log(
    ep: str,
    bloques: list[dict],
    archivos_ok: int,
    archivos_fallidos: int,
    duracion_segundos: float,
    ruta_final: Path,
    tiempo_generacion: float,
    con_musica: bool,
    output_dir: Path,
    spec: dict,
    before_snapshot: SubscriptionSnapshot,
    after_snapshot: SubscriptionSnapshot,
    verification_issues: list[str],
    asset_issues: list[str] | None = None,
    asset_info: list[str] | None = None,
    escaleta: list[dict] | None = None,
) -> Path:
    total_chars = sum(len(block["text"]) for block in bloques)
    before_remaining = before_snapshot.remaining
    after_remaining = after_snapshot.remaining
    consumed_real = None
    if before_remaining is not None and after_remaining is not None:
        consumed_real = before_remaining - after_remaining

    log_lines = [
        "========================================",
        f"LOG DE PRODUCCION - {ep}",
        "========================================",
        f"Fecha:              {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Modelo audio:       {spec['audio_rules']['model']}",
        f"Voz IAGO:           {get_voice_config(spec, 'IAGO')['voice_id']}",
        f"  speed={get_voice_config(spec, 'IAGO')['speed']} stability={get_voice_config(spec, 'IAGO')['stability']}",
        f"Voz MARIA:          {get_voice_config(spec, 'MARIA')['voice_id']}",
        f"  speed={get_voice_config(spec, 'MARIA')['speed']} stability={get_voice_config(spec, 'MARIA')['stability']}",
        f"Musica de fondo:    {'si' if con_musica else 'no'}",
        f"Post speed final:   x{spec['audio_rules'].get('post_speed_multiplier', 1.0)}",
        "",
        "RESULTADOS",
        "----------",
        f"Bloques totales:    {len(bloques)}",
        f"Bloques generados:  {archivos_ok}",
        f"Bloques fallidos:   {archivos_fallidos}",
        f"Duracion total:     {duracion_segundos/60:.1f} minutos ({duracion_segundos:.0f}s)",
        f"Tiempo generacion:  {tiempo_generacion/60:.1f} minutos",
        f"Archivo final:      {ruta_final}",
        "",
        "CONSUMO",
        "-------",
        f"Tokens audio:       no aplica (ElevenLabs usa creditos/caracteres)",
        f"Caracteres totales: {total_chars}",
        f"Creditos estimados: {total_chars}",
    ]
    if consumed_real is not None:
        log_lines.append(f"Creditos consumidos reales: {consumed_real}")
    else:
        log_lines.append("Creditos consumidos reales: desconocido (API no disponible)")
    if after_remaining is not None:
        log_lines.append(f"Creditos restantes reales: {after_remaining}")
    else:
        log_lines.append("Creditos restantes reales: desconocido (API no disponible)")

    log_lines.extend(["", "VALIDACION FINAL", "----------------"])
    all_issues = list(verification_issues or []) + list(asset_issues or [])
    if all_issues:
        for issue in all_issues:
            log_lines.append(f"- {issue}")
    else:
        log_lines.append("- OK")

    if asset_info:
        log_lines.extend(["", "VERIFICACION DE ASSETS", "----------------------"])
        for line in asset_info:
            log_lines.append(f"  {line}")

    if escaleta:
        log_lines.extend(["", "ESCALETA", "--------"])
        for entry in escaleta:
            t = ms_to_mmss(entry["time_ms"])
            ev = entry["event"]
            if ev == "INICIO":
                log_lines.append(f"  {t}  [INICIO]")
            elif ev == "SINTONIA_START":
                log_lines.append(f"  {t}  [SINTONIA — inicio]")
            elif ev == "SINTONIA_END":
                log_lines.append(f"  {t}  [SINTONIA — fin]")
            elif ev == "BLOQUE":
                tag = f" [{entry['tag']}]" if entry.get("tag") else ""
                log_lines.append(
                    f"  {t}  {entry['section']:<24} {entry['speaker']} #{entry['index']:03d}{tag}"
                )

    log_lines.extend(["", "BLOQUES GENERADOS", "-----------------"])
    for block in bloques:
        preview = block["text"][:80] + "..." if len(block["text"]) > 80 else block["text"]
        log_lines.append(f"[{block['index']:03d}] {block['speaker']}: {preview}")

    log_lines.append("")
    log_lines.append("Produccion completada.")
    log_lines.append("")

    log_path = output_dir / log_name_from_ep(ep)
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print("\n".join(log_lines))
    print(f"Log guardado en: {log_path}")
    return log_path


def ms_to_mmss(ms: int) -> str:
    total_s = ms // 1000
    return f"{total_s // 60:02d}:{total_s % 60:02d}"


def log_name_from_ep(ep: str) -> str:
    """M0_E_Nombre → M0_produccion.log  |  M0_T1_E_Nombre → M0_T1_produccion.log"""
    m = re.match(r"^(M\d+(?:_T\d+)?)_E_", ep)
    return f"{m.group(1)}_produccion.log" if m else f"{ep}_produccion.log"


def canonical_speaker_arg(raw: str) -> str:
    clean = raw.strip().upper().replace("Á", "A")
    if clean == "MARIA":
        return "MARIA"
    if clean == "IAGO":
        return "IAGO"
    raise ValueError(f"Speaker no reconocido: {raw}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generador de episodios de MaquinarIA Pesada")
    parser.add_argument("--guion", required=True, help="Ruta al guion con etiquetas")
    parser.add_argument("--ep", required=True, help="Codigo del episodio, por ejemplo EP001")
    parser.add_argument("--spec", default=str(DEFAULT_SPEC_PATH), help="Ruta a la especificacion maestra")
    parser.add_argument("--solo-bloque", type=int, default=None, help="Generar y montar solo el bloque N")
    parser.add_argument("--solo-speaker", type=str, default=None, help="Regenerar solo IAGO o MARIA")
    parser.add_argument("--solo-montar", action="store_true", help="Montar desde archivos existentes")
    parser.add_argument("--generar-musica", action="store_true", help="Generar nueva musica de fondo")
    args = parser.parse_args()

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise SystemExit("Falta ELEVENLABS_API_KEY en el entorno.")

    spec, output_dir, temp_dir, generated_music_path, background_bed_path, intro_theme_path = load_runtime(args.spec)

    print(f"\nLeyendo guion: {args.guion}")
    bloques = parsear_guion(args.guion, args.ep, spec)
    print(f"   {len(bloques)} bloques encontrados")
    print("   Tokens audio: no aplica (ElevenLabs usa creditos/caracteres)")

    before_snapshot = get_subscription_snapshot(api_key)
    print_credit_summary("Antes de generar", before_snapshot)

    if args.generar_musica:
        generar_musica(api_key, generated_music_path, spec)

    active_background_path = background_bed_path if background_bed_path and background_bed_path.exists() else (
        generated_music_path if generated_music_path.exists() else None
    )

    if args.solo_montar:
        print("\nModo solo-montar: usando archivos existentes en output/temp/")
        archivos: list[tuple[Path | None, dict]] = []
        faltantes = 0
        for block in bloques:
            ruta = temp_dir / f"{args.ep}_{block['index']:03d}_{block['speaker']}.mp3"
            if ruta.exists():
                archivos.append((ruta, block))
            else:
                archivos.append((None, block))
                faltantes += 1
        ruta_final = output_dir / f"{args.ep}.mp3"
        duracion, escaleta = montar_audio(archivos, ruta_final, spec, active_background_path, intro_theme_path)
        verification_issues = verify_audio_output(ruta_final, bloques, len(bloques) - faltantes, spec)
        asset_issues, asset_info = verify_production_assets(active_background_path, intro_theme_path, bloques)
        after_snapshot = get_subscription_snapshot(api_key)
        guardar_log(
            ep=args.ep,
            bloques=bloques,
            archivos_ok=len(bloques) - faltantes,
            archivos_fallidos=faltantes,
            duracion_segundos=duracion,
            ruta_final=ruta_final,
            tiempo_generacion=0.0,
            con_musica=bool(active_background_path and active_background_path.exists()),
            output_dir=output_dir,
            spec=spec,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            verification_issues=verification_issues,
            asset_issues=asset_issues,
            asset_info=asset_info,
            escaleta=escaleta,
        )
        print_credit_summary("Despues de montar", after_snapshot)
        if verification_issues or asset_issues:
            raise SystemExit("La validacion final del audio ha fallado. Revisa el log.")
        return

    if args.solo_bloque is not None:
        index = args.solo_bloque - 1
        if not 0 <= index < len(bloques):
            raise SystemExit(f"Bloque {args.solo_bloque} no existe.")
        bloques_a_generar = [bloques[index]]
        print(f"   Modo prueba: solo bloque {args.solo_bloque}")
    elif args.solo_speaker is not None:
        speaker = canonical_speaker_arg(args.solo_speaker)
        bloques_a_generar = [block for block in bloques if block["speaker"] == speaker]
        if not bloques_a_generar:
            raise SystemExit(f"No hay bloques de {speaker} en el guion.")
        print(f"   Modo solo-speaker: {len(bloques_a_generar)} bloques de {speaker}")
    else:
        bloques_a_generar = bloques

    client = ElevenLabs(api_key=api_key)
    print(f"\nGenerando audio con ElevenLabs {spec['audio_rules']['model']}...")
    start_time = time.time()

    archivos_generados: dict[int, tuple[Path | None, dict]] = {}
    archivos_ok = 0
    archivos_fallidos = 0

    for position, bloque in enumerate(bloques_a_generar):
        ruta = generar_bloque(client, bloque, args.ep, temp_dir, spec)
        archivos_generados[bloque["index"]] = (ruta, bloque)
        if ruta:
            archivos_ok += 1
        else:
            archivos_fallidos += 1
        if position < len(bloques_a_generar) - 1:
            time.sleep(0.5)

    elapsed = time.time() - start_time

    if args.solo_speaker is not None:
        after_snapshot = get_subscription_snapshot(api_key)
        print_credit_summary("Despues de regenerar", after_snapshot)
        print(f"\n{archivos_ok} bloques regenerados ({archivos_fallidos} fallidos).")
        print("Ejecuta sin filtros o con --solo-montar para montar el episodio completo.")
        return

    if archivos_ok == 0:
        raise SystemExit("No se genero ningun bloque. Revisa la API key y la conexion.")

    if args.solo_bloque is not None:
        archivos_montar = [(ruta, bloque) for _, (ruta, bloque) in sorted(archivos_generados.items())]
    else:
        archivos_montar = []
        for bloque in bloques:
            if bloque["index"] in archivos_generados:
                ruta, block_meta = archivos_generados[bloque["index"]]
            else:
                ruta_candidate = temp_dir / f"{args.ep}_{bloque['index']:03d}_{bloque['speaker']}.mp3"
                ruta = ruta_candidate if ruta_candidate.exists() else None
                block_meta = bloque
            archivos_montar.append((ruta, block_meta))

    ruta_final = output_dir / f"{args.ep}.mp3"
    duracion, escaleta = montar_audio(archivos_montar, ruta_final, spec, active_background_path, intro_theme_path)
    after_snapshot = get_subscription_snapshot(api_key)
    print_credit_summary("Despues de generar", after_snapshot)

    verification_issues = verify_audio_output(
        ruta_final,
        bloques_a_generar if args.solo_bloque else bloques,
        archivos_ok,
        spec,
        require_full_duration=args.solo_bloque is None,
    )
    asset_issues, asset_info = verify_production_assets(active_background_path, intro_theme_path, bloques)
    guardar_log(
        ep=args.ep,
        bloques=bloques_a_generar if args.solo_bloque else bloques,
        archivos_ok=archivos_ok,
        archivos_fallidos=archivos_fallidos,
        duracion_segundos=duracion,
        ruta_final=ruta_final,
        tiempo_generacion=elapsed,
        con_musica=bool(active_background_path and active_background_path.exists()),
        output_dir=output_dir,
        spec=spec,
        before_snapshot=before_snapshot,
        after_snapshot=after_snapshot,
        verification_issues=verification_issues,
        asset_issues=asset_issues,
        asset_info=asset_info,
        escaleta=escaleta,
    )

    if verification_issues or asset_issues:
        raise SystemExit("La validacion final del audio ha fallado. Revisa el log.")

    print(f"\nAudio final: {ruta_final}")
    print(f"   Duracion: {duracion / 60:.1f} minutos")

    from estado_proyecto import print_estado_resumen
    print_estado_resumen()


if __name__ == "__main__":
    main()
