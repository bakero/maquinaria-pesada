#!/usr/bin/env python3
"""
MaquinarIa Pesada — Script de generación automática de episodios v2.0

Uso:
    python generar_episodio_v2.py --guion EP001_guion_etiquetas_v2.txt --ep EP001
    python generar_episodio_v2.py --guion EP001_guion_etiquetas_v2.txt --ep EP001 --generar-musica --solo-bloque 1
    python generar_episodio_v2.py --guion EP001_guion_etiquetas_v2.txt --ep EP001 --solo-speaker MARÍA
    python generar_episodio_v2.py --guion EP001_guion_etiquetas_v2.txt --ep EP001 --solo-montar

Requisitos:
    pip install elevenlabs pydub

Variables de entorno:
    ELEVENLABS_API_KEY=tu_api_key_aqui
"""

import os
import sys
import argparse
import time
from dotenv import load_dotenv
load_dotenv()
import glob as _glob
from pathlib import Path
from datetime import datetime

# Forzar UTF-8 en consola Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Añadir ffmpeg oficial (WinGet) al PATH antes de importar pydub
def _setup_ffmpeg():
    import shutil
    winget_candidates = sorted(
        _glob.glob(r"C:\Users\Asus\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg-*\bin\ffmpeg.exe"),
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

_setup_ffmpeg()

# ============================================================
# CONFIGURACIÓN
# ============================================================

API_KEY = os.environ.get("ELEVENLABS_API_KEY", "TU_API_KEY_AQUI")

VOCES = {
    "IAGO":  "851ejYcv2BoNPjrkw93G",   # Tony
    "MARÍA": "gJlzF5JxsCvM5hQAoRyD",   # voz española (v4)
}

MODELO = "eleven_v3"

CONFIGURACION_VOCES = {
    "IAGO": {
        "stability":         0.50,
        "similarity_boost":  0.65,
        "style":             0.00,
        "use_speaker_boost": False,
        "speed":             1.15,
    },
    "MARÍA": {
        "stability":         0.70,
        "similarity_boost":  0.55,
        "style":             0.00,
        "use_speaker_boost": False,
        "speed":             1.25,   # v4: acento España, velocidad ajustada
    },
}

OUTPUT_DIR = Path("output")
TEMP_DIR   = Path("output/temp")
MUSICA_RAW = OUTPUT_DIR / "background_music_raw.mp3"

SILENCIO_INICIO_MS           = 2000   # 2s al inicio (Cambio 1)
SILENCIO_MISMO_SPEAKER_MS    = 250
SILENCIO_DISTINTO_SPEAKER_MS = 500

# ============================================================
# IMPORTS
# ============================================================

try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings
except ImportError:
    print("ERROR: Instala la librería de ElevenLabs:")
    print("  pip install elevenlabs")
    sys.exit(1)

try:
    from pydub import AudioSegment
except ImportError:
    print("ERROR: Instala pydub para el montaje de audio:")
    print("  pip install pydub")
    sys.exit(1)

# ============================================================
# PARSER DEL GUIÓN
# ============================================================

def parsear_guion(ruta_guion: str) -> list[dict]:
    """
    Lee el guión y devuelve bloques con índice original preservado.
    Cada bloque: {speaker, voice_id, text, linea, indice}
    """
    bloques = []
    with open(ruta_guion, "r", encoding="utf-8") as f:
        for num_linea, linea in enumerate(f, 1):
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            if linea.startswith("IAGO:"):
                bloques.append({
                    "speaker":  "IAGO",
                    "voice_id": VOCES["IAGO"],
                    "text":     linea[5:].strip(),
                    "linea":    num_linea,
                })
            elif linea.startswith("MARÍA:"):
                bloques.append({
                    "speaker":  "MARÍA",
                    "voice_id": VOCES["MARÍA"],
                    "text":     linea[6:].strip(),
                    "linea":    num_linea,
                })

    for i, b in enumerate(bloques, 1):
        b["indice"] = i

    return bloques

# ============================================================
# GENERACIÓN DE AUDIO — BLOQUE
# ============================================================

def generar_bloque(
    client:     ElevenLabs,
    bloque:     dict,
    ep:         str,
    reintentos: int = 3,
) -> Path | None:
    speaker  = bloque["speaker"]
    voice_id = bloque["voice_id"]
    texto    = bloque["text"]
    indice   = bloque["indice"]
    config   = CONFIGURACION_VOCES[speaker]

    nombre_archivo = TEMP_DIR / f"{ep}_{indice:03d}_{speaker}.mp3"

    for intento in range(1, reintentos + 1):
        try:
            print(f"  [{indice:03d}] {speaker} — generando... (intento {intento})")

            audio_generator = client.text_to_speech.convert(
                voice_id=voice_id,
                text=texto,
                model_id=MODELO,
                voice_settings=VoiceSettings(
                    stability=config["stability"],
                    similarity_boost=config["similarity_boost"],
                    style=config["style"],
                    use_speaker_boost=config["use_speaker_boost"],
                    speed=config["speed"],
                ),
                output_format="mp3_44100_128",
            )

            with open(nombre_archivo, "wb") as f:
                for chunk in audio_generator:
                    if chunk:
                        f.write(chunk)

            print(f"  [{indice:03d}] {speaker} — guardado: {nombre_archivo.name}")
            return nombre_archivo

        except Exception as e:
            print(f"  [{indice:03d}] {speaker} — ERROR intento {intento}: {e}")
            if intento < reintentos:
                espera = 5 * intento
                print(f"  Esperando {espera}s antes de reintentar...")
                time.sleep(espera)
            else:
                print(f"  [{indice:03d}] FALLO DEFINITIVO. Bloque omitido.")
                return None

# ============================================================
# GENERACIÓN DE MÚSICA DE FONDO (Cambio 4)
# ============================================================

def generar_musica(api_key: str, ruta_destino: Path) -> bool:
    """Genera track instrumental via ElevenLabs sound-generation y lo guarda."""
    try:
        import httpx
    except ImportError:
        print("ERROR: httpx no disponible. Ejecuta: pip install httpx")
        return False

    print("\nGenerando música de fondo via ElevenLabs sound-generation...")
    try:
        resp = httpx.post(
            "https://api.elevenlabs.io/v1/sound-generation",
            headers={
                "xi-api-key":   api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": (
                    "Lo-fi instrumental background music for a technology podcast. "
                    "Slow repetitive beats, no vocals, no dominant melody, ambient electronic, "
                    "deep focus mood, seamlessly loopable, subtle and unobtrusive"
                ),
                "duration_seconds": 30,
                "prompt_influence": 0.3,
            },
            timeout=120.0,
        )

        if resp.status_code == 200:
            ruta_destino.write_bytes(resp.content)
            print(f"  Música guardada: {ruta_destino}")
            return True
        else:
            print(f"  ERROR {resp.status_code}: {resp.text[:300]}")
            return False

    except Exception as e:
        print(f"  ERROR generando música: {e}")
        return False

# ============================================================
# MONTAJE DE AUDIO (Cambios 1 y 4)
# ============================================================

def montar_audio(
    archivos:    list[tuple[Path | None, str]],
    ruta_final:  Path,
    ruta_musica: Path | None = None,
) -> float:
    """
    Monta todos los bloques en un único MP3.
    Aplica silencio inicial, normalización y mezcla de música de fondo.
    Devuelve la duración total en segundos.
    """
    print("\nMontando audio final...")

    # Silencio inicial de 2 segundos (Cambio 1)
    episodio = AudioSegment.silent(duration=SILENCIO_INICIO_MS)
    speaker_anterior = None

    for ruta, speaker in archivos:
        if ruta is None:
            continue

        if speaker_anterior is not None:
            ms = (
                SILENCIO_MISMO_SPEAKER_MS
                if speaker == speaker_anterior
                else SILENCIO_DISTINTO_SPEAKER_MS
            )
            episodio += AudioSegment.silent(duration=ms)

        try:
            episodio += AudioSegment.from_mp3(str(ruta))
            speaker_anterior = speaker
        except Exception as e:
            print(f"  ERROR montando {ruta.name}: {e}")

    # Normalizar voces a -16 LUFS (aproximación)
    episodio = episodio.normalize()
    episodio = episodio.apply_gain(-16 - episodio.dBFS)

    # Mezclar música de fondo (Cambio 4)
    if ruta_musica and Path(ruta_musica).exists():
        print("  Mezclando música de fondo...")
        musica = AudioSegment.from_mp3(str(ruta_musica))

        # Loop hasta cubrir el episodio + 5s de margen
        duracion_objetivo_ms = len(episodio) + 5000
        repeticiones = (duracion_objetivo_ms // len(musica)) + 2
        musica_loop = (musica * repeticiones)[:duracion_objetivo_ms]

        # Fade in 3s, fade out 5s
        musica_loop = musica_loop.fade_in(3000).fade_out(5000)

        # Bajar -20 dB respecto a las voces normalizadas
        musica_loop = musica_loop - 20

        # Mezclar sobre el audio de voces
        episodio = episodio.overlay(musica_loop)
    else:
        if ruta_musica:
            print("  Música de fondo no encontrada — montando sin música.")

    episodio.export(
        str(ruta_final),
        format="mp3",
        bitrate="192k",
        tags={
            "title":   "MaquinarIa Pesada",
            "artist":  "MaquinarIa Pesada",
            "comment": "Generado automáticamente con IA",
        },
    )

    return len(episodio) / 1000

# ============================================================
# LOG DE PRODUCCIÓN
# ============================================================

def guardar_log(
    ep:                str,
    bloques:           list[dict],
    archivos_ok:       int,
    archivos_fallidos: int,
    duracion_segundos: float,
    ruta_final:        Path,
    tiempo_generacion: float,
    con_musica:        bool,
):
    total_chars = sum(len(b["text"]) for b in bloques)

    log = f"""
========================================
LOG DE PRODUCCIÓN — {ep}
========================================
Fecha:              {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Modelo:             {MODELO}
Voz IAGO:           Tony ({VOCES["IAGO"]})
  stability={CONFIGURACION_VOCES["IAGO"]["stability"]}  similarity={CONFIGURACION_VOCES["IAGO"]["similarity_boost"]}
Voz MARÍA:          Sheila ({VOCES["MARÍA"]})
  stability={CONFIGURACION_VOCES["MARÍA"]["stability"]}  similarity={CONFIGURACION_VOCES["MARÍA"]["similarity_boost"]}
Música de fondo:    {"sí" if con_musica else "no"}

RESULTADOS
----------
Bloques totales:    {len(bloques)}
Bloques generados:  {archivos_ok}
Bloques fallidos:   {archivos_fallidos}
Duración total:     {duracion_segundos/60:.1f} minutos ({duracion_segundos:.0f}s)
Tiempo generación:  {tiempo_generacion/60:.1f} minutos
Archivo final:      {ruta_final}

CRÉDITOS
--------
Caracteres totales: {total_chars}
Créditos estimados: {total_chars}

BLOQUES GENERADOS
-----------------
"""
    for b in bloques:
        texto_preview = b["text"][:60] + "..." if len(b["text"]) > 60 else b["text"]
        log += f"  [{b['indice']:03d}] {b['speaker']}: {texto_preview}\n"

    ruta_log = OUTPUT_DIR / f"{ep}_produccion.log"
    with open(ruta_log, "w", encoding="utf-8") as f:
        f.write(log)

    print(log)
    print(f"Log guardado en: {ruta_log}")

# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generador automático de episodios de MaquinarIa Pesada v2"
    )
    parser.add_argument("--guion",          required=True,  help="Ruta al guión con etiquetas")
    parser.add_argument("--ep",             required=True,  help="Código del episodio (ej: EP001)")
    parser.add_argument("--solo-bloque",    type=int, default=None, help="Generar y montar solo el bloque N")
    parser.add_argument("--solo-speaker",   type=str, default=None, help="Regenerar solo los bloques de IAGO o MARÍA")
    parser.add_argument("--solo-montar",    action="store_true",    help="Montar desde archivos existentes sin regenerar")
    parser.add_argument("--generar-musica", action="store_true",    help="Generar música de fondo (consume créditos)")
    args = parser.parse_args()

    if API_KEY == "TU_API_KEY_AQUI":
        print("ERROR: Configura tu API key de ElevenLabs.")
        print("  export ELEVENLABS_API_KEY=tu_key")
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)

    # Parsear guión
    print(f"\nLeyendo guion: {args.guion}")
    bloques = parsear_guion(args.guion)
    print(f"   {len(bloques)} bloques encontrados")

    # Generar música si se solicita (Cambio 5)
    if args.generar_musica:
        generar_musica(API_KEY, MUSICA_RAW)

    # ---- Modo solo-montar: monta desde archivos en disco ----
    if args.solo_montar:
        print("\nModo solo-montar: usando archivos existentes en output/temp/")
        archivos = []
        faltantes = 0
        for b in bloques:
            ruta = TEMP_DIR / f"{args.ep}_{b['indice']:03d}_{b['speaker']}.mp3"
            if ruta.exists():
                archivos.append((ruta, b["speaker"]))
            else:
                archivos.append((None, b["speaker"]))
                faltantes += 1
        if faltantes:
            print(f"  Advertencia: {faltantes} bloques sin archivo en disco (se omitirán).")
        ruta_final = OUTPUT_DIR / f"{args.ep}_MaquinarIaPesada_final.mp3"
        ruta_musica = MUSICA_RAW if MUSICA_RAW.exists() else None
        duracion = montar_audio(archivos, ruta_final, ruta_musica)
        print(f"\nAudio final: {ruta_final}")
        print(f"   Duración: {duracion/60:.1f} minutos")
        print("\nProducción completada.")
        return

    # ---- Determinar qué bloques generar ----
    if args.solo_bloque is not None:
        idx = args.solo_bloque - 1
        if not (0 <= idx < len(bloques)):
            print(f"ERROR: Bloque {args.solo_bloque} no existe (total: {len(bloques)})")
            sys.exit(1)
        bloques_a_generar = [bloques[idx]]
        print(f"   Modo prueba: solo bloque {args.solo_bloque}")

    elif args.solo_speaker is not None:
        sp = args.solo_speaker.upper()
        if sp not in VOCES:
            print(f"ERROR: Presentador '{sp}' no reconocido. Usa IAGO o MARÍA.")
            sys.exit(1)
        bloques_a_generar = [b for b in bloques if b["speaker"] == sp]
        if not bloques_a_generar:
            print(f"ERROR: No hay bloques de {sp} en el guion.")
            sys.exit(1)
        print(f"   Modo solo-speaker: {len(bloques_a_generar)} bloques de {sp}")

    else:
        bloques_a_generar = bloques

    # ---- Generar audio bloque a bloque ----
    client = ElevenLabs(api_key=API_KEY)
    print(f"\nGenerando audio con ElevenLabs {MODELO}...")
    inicio = time.time()

    archivos_generados: dict[int, tuple[Path | None, str]] = {}
    archivos_ok       = 0
    archivos_fallidos = 0

    for i, bloque in enumerate(bloques_a_generar):
        ruta = generar_bloque(client, bloque, args.ep)
        archivos_generados[bloque["indice"]] = (ruta, bloque["speaker"])
        if ruta:
            archivos_ok += 1
        else:
            archivos_fallidos += 1
        if i < len(bloques_a_generar) - 1:
            time.sleep(0.5)

    tiempo_generacion = time.time() - inicio

    # ---- Modo solo-speaker: solo regenera, no monta ----
    if args.solo_speaker is not None:
        sp = args.solo_speaker.upper()
        print(f"\n{archivos_ok} bloques de {sp} regenerados ({archivos_fallidos} fallidos).")
        print("Ejecuta con --solo-montar (o sin filtros) para montar el episodio completo.")
        return

    # ---- Montar audio ----
    if archivos_ok == 0:
        print("\nNo se generó ningún bloque. Revisa tu API key y conexión.")
        sys.exit(1)

    # Para solo-bloque: montar solo ese bloque
    # Para episodio completo: reconstruir desde disk + nuevas generaciones
    if args.solo_bloque is not None:
        archivos_montar = [
            (ruta, sp)
            for _, (ruta, sp) in sorted(archivos_generados.items())
        ]
    else:
        archivos_montar = []
        for b in bloques:
            if b["indice"] in archivos_generados:
                ruta, sp = archivos_generados[b["indice"]]
            else:
                ruta_disco = TEMP_DIR / f"{args.ep}_{b['indice']:03d}_{b['speaker']}.mp3"
                ruta = ruta_disco if ruta_disco.exists() else None
                sp = b["speaker"]
            archivos_montar.append((ruta, sp))

    ruta_musica = MUSICA_RAW if MUSICA_RAW.exists() else None
    ruta_final  = OUTPUT_DIR / f"{args.ep}_MaquinarIaPesada_final.mp3"
    duracion    = montar_audio(archivos_montar, ruta_final, ruta_musica)

    print(f"\nAudio final: {ruta_final}")
    print(f"   Duración: {duracion/60:.1f} minutos")

    # Log solo en modo episodio completo
    if args.solo_bloque is None:
        guardar_log(
            ep=args.ep,
            bloques=bloques,
            archivos_ok=archivos_ok,
            archivos_fallidos=archivos_fallidos,
            duracion_segundos=duracion,
            ruta_final=ruta_final,
            tiempo_generacion=tiempo_generacion,
            con_musica=ruta_musica is not None,
        )

    print("\nProduccion completada.")


if __name__ == "__main__":
    main()
