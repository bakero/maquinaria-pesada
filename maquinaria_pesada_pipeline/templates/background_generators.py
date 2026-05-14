"""
Generadores de fondos industriales para los frames del videopodcast.
Cada generador devuelve una PIL.Image RGB del tamano (w, h).
"""

import math
import random

from PIL import Image, ImageDraw


def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def generate_grid(w: int, h: int, base: str = "#0A0A0A",
                  line: str = "#1A1A1A", step: int = 40) -> Image.Image:
    """Fondo industrial: cuadricula de lineas finas."""
    img = Image.new("RGB", (w, h), hex_to_rgb(base))
    d = ImageDraw.Draw(img)
    color = hex_to_rgb(line)
    for x in range(0, w, step):
        d.line([(x, 0), (x, h)], fill=color, width=1)
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=color, width=1)
    return img


def generate_circuit(w: int, h: int, base: str = "#050D14",
                     line: str = "#0D1F2D", step: int = 40) -> Image.Image:
    """Fondo tipo placa de circuito: rejilla con nodos."""
    img = generate_grid(w, h, base=base, line=line, step=step)
    d = ImageDraw.Draw(img)
    accent = hex_to_rgb("#1A3550")
    rng = random.Random(42)
    for _ in range((w * h) // 20000):
        x = rng.randrange(0, w, step)
        y = rng.randrange(0, h, step)
        r = rng.choice([2, 3, 4])
        d.ellipse([x - r, y - r, x + r, y + r], fill=accent)
    return img


def generate_diagonal(w: int, h: int, base: str = "#080808",
                      line: str = "#111111", angle: int = 135,
                      spacing: int = 12) -> Image.Image:
    """Fondo de lineas diagonales."""
    img = Image.new("RGB", (w, h), hex_to_rgb(base))
    d = ImageDraw.Draw(img)
    color = hex_to_rgb(line)
    rad = math.radians(angle)
    dx = int(math.cos(rad) * (w + h))
    dy = int(math.sin(rad) * (w + h))
    diag = int(math.hypot(w, h))
    for offset in range(-diag, diag, spacing):
        x0 = offset
        y0 = 0
        x1 = offset + dx
        y1 = dy
        d.line([(x0, y0), (x1, y1)], fill=color, width=1)
    return img


BACKGROUNDS = {
    "industrial_grid": generate_grid,
    "circuit_board":   generate_circuit,
    "data_diagonal":   generate_diagonal,
}


def get_background(name: str, w: int, h: int) -> Image.Image:
    fn = BACKGROUNDS.get(name, generate_grid)
    return fn(w, h)
