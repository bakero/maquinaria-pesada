"""
Gestor de stickers de humor.
- Si hay carpeta de stickers configurada, busca PNGs por nombre.
- Si no, genera un placeholder estilizado con texto.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

STICKER_LABELS = {
    "nobody_reads_tos":  "TOS\n📜",
    "winter_is_coming":  "AI\nWINTER",
    "linkedin_guru":     "LinkedIn\nGuru",
    "expensive_mistake": "$$$",
    "speedrun":          "SPEED\nRUN",
    "this_is_fine":      "THIS\nIS FINE",
    "lawyer_up":         "AI\nACT",
    "stonks":            "STONKS",
    "wave_bye":          "BYE",
}


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/ariblk.ttf",
        "C:/Windows/Fonts/impact.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _placeholder_sticker(name: str, size: int = 220) -> Image.Image:
    label = STICKER_LABELS.get(name, name.replace("_", "\n").upper())
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # circulo base amarillo con borde negro
    d.ellipse((4, 4, size - 4, size - 4),
              fill=(245, 196, 0, 235),
              outline=(13, 13, 13, 255), width=4)
    f = _get_font(28)
    bbox = d.multiline_textbbox((0, 0), label, font=f, align="center", spacing=4)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.multiline_text(
        ((size - tw) // 2, (size - th) // 2),
        label, font=f, fill=(13, 13, 13, 255),
        align="center", spacing=4,
    )
    return img


def get_sticker(name: str, folder: str | Path | None = None,
                size: int = 220) -> Image.Image:
    """
    Devuelve PIL.Image RGBA del sticker.
    Si existe en la carpeta como `<name>.png`, se carga; si no, placeholder.
    """
    if folder:
        p = Path(folder) / f"{name}.png"
        if p.exists():
            try:
                img = Image.open(p).convert("RGBA")
                if img.width != size:
                    ratio = size / max(img.width, img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.LANCZOS)
                return img
            except Exception:
                pass
    return _placeholder_sticker(name, size)
