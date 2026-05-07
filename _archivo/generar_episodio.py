#!/usr/bin/env python3
"""
MaquinarIa Pesada — Script de generación automática de episodios
Versión 1.0

Uso:
    python generar_episodio.py --guion EP001_guion_etiquetas.txt --ep EP001
    python generar_episodio.py --guion EP002_guion_etiquetas.txt --ep EP002

Requisitos:
    pip install elevenlabs pydub

Variables de entorno necesarias:
    ELEVENLABS_API_KEY=tu_api_key_aqui

O puedes escribir la key directamente en la variable API_KEY más abajo (no recomendado para producción).
"""

import os
import sys
import argparse
import time
import glob as _glob
from pathlib import Path
from datetime import datetime

# Forzar UTF-8 en la consola Windows para que los emojis no rompan el proceso
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Añadir ffmpeg al PATH si no está disponible en el shell actual.
# Prioridad: 1) WinGet (ffmpeg oficial)  2) CapCut (versión recortada, sin encoder MP3)
def _setup_ffmpeg():
    import shutil
    # Buscar ffmpeg oficial instalado por WinGet
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
    # Fallback: CapCut (solo si no hay otra opción)
    capcut_candidates = sorted(
        _glob.glob(r"C:\Users\Asus\AppData\Local\CapCut\Apps\*\ffmpeg.exe"),
        reverse=True,
    )
    if capcut_candidates:
        ffmpeg_dir = str(Path(capcut_candidates[0]).parent)
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

_setup_ffmpeg()

# ============================================================
# CONFIGURACIÓN — edita estos valores
# ============================================================

API_KEY = os.environ.get("ELEVENLABS_API_KEY", "TU_API_KEY_AQUI")

VOCES = {
    "IAGO":  "851ejYcv2BoNPjrkw93G",   # Tony
    "MARÍA": "h3l1RP4XfcWsPwoRp9G6",   # Sheila
}

MODELO = "eleven_v3"

CONFIGURACION_VOCES = {
    "IAGO": {
        "stability":        0.50,
        "similarity_boost": 0.65,
        "style":            0.00,
        "use_speaker_boost": False,   # No disponible en v3
    },
    "MARÍA": {
        "stability":        0.55,
        "similarity_boost": 0.65,
        "style":            0.00,
        "use_speaker_boost": False,
    },
}

OUTPUT_DIR = Path("output")
TEMP_DIR   = Path("output/temp")

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
    from pydub.utils import which
    # ffmpeg no está en el PATH en Windows — usar el de CapCut si está disponible
    if not which("ffmpeg"):
        import glob as _glob
        _candidates = sorted(_glob.glob(
            r"C:\Users\Asus\AppData\Local\CapCut\Apps\*\ffmpeg.exe"
        ), reverse=True)
        if _candidates:
            AudioSegment.converter = _candidates[0]
            AudioSegment.ffmpeg    = _candidates[0]
            AudioSegment.ffprobe   = _candidates[0].replace("ffmpeg.exe", "ffprobe.exe")
except ImportError:
    print("ERROR: Instala pydub para el montaje de audio:")
    print("  pip install pydub")
    print("  También necesitas ffmpeg instalado en tu sistema.")
    sys.exit(1)

# ============================================================
# PARSER DEL GUIÓN
# ============================================================

def parsear_guion(ruta_guion: str) -> list[dict]:
    """
    Lee el archivo de guión y devuelve lista de bloques.
    Cada bloque: {"speaker": "IAGO"|"MARÍA", "text": "texto con etiquetas"}
    Ignora líneas vacías y comentarios (#).
    Ignora líneas de instrucciones técnicas entre corchetes sin presentador.
    """
    bloques = []
    with open(ruta_guion, "r", encoding="utf-8") as f:
        for num_linea, linea in enumerate(f, 1):
            linea = linea.strip()

            # Ignorar vacías y comentarios
            if not linea or linea.startswith("#"):
                continue

            # Detectar presentador
            if linea.startswith("IAGO:"):
                texto = linea[5:].strip()
                bloques.append({
                    "speaker":   "IAGO",
                    "voice_id":  VOCES["IAGO"],
                    "text":      texto,
                    "linea":     num_linea,
                })
            elif linea.startswith("MARÍA:"):
                texto = linea[6:].strip()
                bloques.append({
                    "speaker":   "MARÍA",
                    "voice_id":  VOCES["MARÍA"],
                    "text":      texto,
                    "linea":     num_linea,
                })
            # Cualquier otra línea se ignora (instrucciones técnicas)

    return bloques

# ============================================================
# GENERACIÓN DE AUDIO
# ============================================================

def generar_bloque(
    client:   ElevenLabs,
    bloque:   dict,
    indice:   int,
    ep:       str,
    reintentos: int = 3,
) -> Path | None:
    """
    Genera el audio de un bloque y lo guarda como WAV temporal.
    Devuelve la ruta del archivo generado o None si falla.
    """
    speaker  = bloque["speaker"]
    voice_id = bloque["voice_id"]
    texto    = bloque["text"]
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
                ),
                output_format="mp3_44100_128",
            )

            # Guardar audio
            with open(nombre_archivo, "wb") as f:
                for chunk in audio_generator:
                    if chunk:
                        f.write(chunk)

            print(f"  [{indice:03d}] {speaker} — ✓ guardado: {nombre_archivo.name}")
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
# MONTAJE DE AUDIO
# ============================================================

SILENCIO_MISMO_SPEAKER_MS    = 250   # 0.25s entre intervenciones del mismo presentador
SILENCIO_DISTINTO_SPEAKER_MS = 500   # 0.50s entre presentadores distintos

def montar_audio(
    archivos:  list[tuple[Path, str]],
    ruta_final: Path,
) -> float:
    """
    Monta todos los bloques en un único archivo MP3.
    archivos: lista de (ruta_archivo, speaker)
    Devuelve la duración total en segundos.
    """
    print("\n🎙️  Montando audio final...")

    episodio = AudioSegment.empty()
    speaker_anterior = None

    for ruta, speaker in archivos:
        if ruta is None:
            continue

        # Silencio entre bloques
        if speaker_anterior is not None:
            if speaker == speaker_anterior:
                silencio_ms = SILENCIO_MISMO_SPEAKER_MS
            else:
                silencio_ms = SILENCIO_DISTINTO_SPEAKER_MS
            episodio += AudioSegment.silent(duration=silencio_ms)

        try:
            segmento = AudioSegment.from_mp3(str(ruta))
            episodio += segmento
            speaker_anterior = speaker
        except Exception as e:
            print(f"  ERROR montando {ruta.name}: {e}")

    # Normalizar a -16 LUFS (aproximación con pydub: normalize a -16 dBFS)
    episodio = episodio.normalize()
    episodio = episodio.apply_gain(-16 - episodio.dBFS)

    # Exportar
    episodio.export(
        str(ruta_final),
        format="mp3",
        bitrate="192k",
        tags={
            "title":   "MaquinarIa Pesada",
            "artist":  "MaquinarIa Pesada",
            "comment": "Generado automáticamente con IA",
        }
    )

    duracion_segundos = len(episodio) / 1000
    return duracion_segundos

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
):
    total_chars = sum(len(b["text"]) for b in bloques)
    creditos_estimados = total_chars  # 1 crédito por carácter en ElevenLabs

    log = f"""
========================================
LOG DE PRODUCCIÓN — {ep}
========================================
Fecha:              {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Modelo:             {MODELO}
Voz IAGO:           Tony ({VOCES["IAGO"]})
Voz MARÍA:          Sheila ({VOCES["MARÍA"]})

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
Créditos estimados: {creditos_estimados}

BLOQUES GENERADOS
-----------------
"""
    for i, b in enumerate(bloques, 1):
        log += f"  [{i:03d}] {b['speaker']}: {b['text'][:60]}...\n" if len(b['text']) > 60 else f"  [{i:03d}] {b['speaker']}: {b['text']}\n"

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
        description="Generador automático de episodios de MaquinarIa Pesada"
    )
    parser.add_argument(
        "--guion", required=True,
        help="Ruta al archivo de guión con etiquetas (ej: EP001_guion_etiquetas.txt)"
    )
    parser.add_argument(
        "--ep", required=True,
        help="Código del episodio (ej: EP001)"
    )
    parser.add_argument(
        "--solo-bloque", type=int, default=None,
        help="Generar solo un bloque específico (para pruebas)"
    )
    args = parser.parse_args()

    # Validar API key
    if API_KEY == "TU_API_KEY_AQUI":
        print("ERROR: Configura tu API key de ElevenLabs.")
        print("  Opción 1: export ELEVENLABS_API_KEY=tu_key")
        print("  Opción 2: edita la variable API_KEY en el script")
        sys.exit(1)

    # Crear directorios
    OUTPUT_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)

    # Parsear guión
    print(f"\n📄 Leyendo guión: {args.guion}")
    bloques = parsear_guion(args.guion)
    print(f"   {len(bloques)} bloques encontrados")

    # Modo prueba: solo un bloque
    if args.solo_bloque is not None:
        idx = args.solo_bloque - 1
        if 0 <= idx < len(bloques):
            bloques = [bloques[idx]]
            print(f"   Modo prueba: generando solo bloque {args.solo_bloque}")
        else:
            print(f"ERROR: Bloque {args.solo_bloque} no existe (total: {len(bloques)})")
            sys.exit(1)

    # Inicializar cliente
    client = ElevenLabs(api_key=API_KEY)

    # Generar bloques
    print(f"\n🎙️  Generando audio con ElevenLabs {MODELO}...")
    inicio = time.time()

    archivos_generados = []
    archivos_ok = 0
    archivos_fallidos = 0

    for i, bloque in enumerate(bloques, 1):
        ruta = generar_bloque(client, bloque, i, args.ep)
        archivos_generados.append((ruta, bloque["speaker"]))

        if ruta is not None:
            archivos_ok += 1
        else:
            archivos_fallidos += 1

        # Pausa entre llamadas para evitar rate limiting
        if i < len(bloques):
            time.sleep(0.5)

    tiempo_generacion = time.time() - inicio

    # Montar audio final
    if archivos_ok > 0:
        ruta_final = OUTPUT_DIR / f"{args.ep}_MaquinarIaPesada_final.mp3"
        duracion = montar_audio(archivos_generados, ruta_final)
        print(f"\n✅ Audio final: {ruta_final}")
        print(f"   Duración: {duracion/60:.1f} minutos")
    else:
        print("\n❌ No se generó ningún bloque. Revisa tu API key y conexión.")
        sys.exit(1)

    # Log de producción
    guardar_log(
        ep=args.ep,
        bloques=bloques,
        archivos_ok=archivos_ok,
        archivos_fallidos=archivos_fallidos,
        duracion_segundos=duracion,
        ruta_final=ruta_final,
        tiempo_generacion=tiempo_generacion,
    )

    print("\nProduccion completada.")

    from estado_proyecto import print_estado_resumen
    print_estado_resumen()

if __name__ == "__main__":
    main()
