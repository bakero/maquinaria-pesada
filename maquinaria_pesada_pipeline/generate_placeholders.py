"""Genera placeholders minimos para los assets faltantes (logo, intro, sintonia, music)."""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / "outputs" / "_placeholders"
OUT.mkdir(parents=True, exist_ok=True)

# 1) Logo PNG transparente con texto MP
logo = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
d = ImageDraw.Draw(logo)
d.ellipse((8, 8, 248, 248), fill=(245, 196, 0, 255), outline=(13, 13, 13, 255), width=8)
try:
    f = ImageFont.truetype("C:/Windows/Fonts/ariblk.ttf", 110)
except OSError:
    f = ImageFont.load_default()
d.text((54, 60), "MP", font=f, fill=(13, 13, 13, 255))
logo_path = OUT / "logo_placeholder.png"
logo.save(logo_path)
print(f"[OK] logo: {logo_path}")

# 2) Sintonia MP3 (5s tono 220Hz) usando ffmpeg
sintonia_path = OUT / "sintonia_placeholder.mp3"
subprocess.run([
    "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=5",
    "-ar", "44100", "-ac", "2", "-b:a", "128k", str(sintonia_path),
], check=True, capture_output=True)
print(f"[OK] sintonia: {sintonia_path}")

# 3) Background music (10s tono 110Hz)
bg_path = OUT / "background_music_placeholder.mp3"
subprocess.run([
    "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=110:duration=10",
    "-ar", "44100", "-ac", "2", "-b:a", "128k", str(bg_path),
], check=True, capture_output=True)
print(f"[OK] background_music: {bg_path}")

# 4) Intro video MP4 (3s con logo sobre fondo amarillo + sintonia)
intro_path = OUT / "intro_placeholder.mp4"
intro_img = Image.new("RGB", (1920, 1080), (245, 196, 0))
d = ImageDraw.Draw(intro_img)
try:
    f_big = ImageFont.truetype("C:/Windows/Fonts/ariblk.ttf", 140)
except OSError:
    f_big = ImageFont.load_default()
d.text((420, 460), "MAQUINARIA PESADA", font=f_big, fill=(13, 13, 13))
intro_img_path = OUT / "intro_frame.jpg"
intro_img.save(intro_img_path, "JPEG", quality=92)

subprocess.run([
    "ffmpeg", "-y",
    "-loop", "1", "-t", "3", "-i", str(intro_img_path),
    "-i", str(sintonia_path),
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
    "-vf", "scale=1920:1080",
    "-c:a", "aac", "-b:a", "192k", "-shortest",
    str(intro_path),
], check=True, capture_output=True)
print(f"[OK] intro_video: {intro_path}")

print("\nPlaceholders listos. Rutas:")
print(f"  LOGO:       {logo_path}")
print(f"  INTRO:      {intro_path}")
print(f"  SINTONIA:   {sintonia_path}")
print(f"  BACKGROUND: {bg_path}")
