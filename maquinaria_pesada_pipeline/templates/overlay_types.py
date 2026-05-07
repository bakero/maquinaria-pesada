"""
Tipos de overlay disponibles para el videopodcast.
Cada funcion recibe un dict de datos y devuelve PIL.Image RGBA con transparencia.
Los overlays se componen luego sobre el background del frame.
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Colores de marca
YELLOW = (245, 196, 0, 255)
BLUE = (77, 184, 255, 255)
WHITE = (232, 232, 232, 255)
DARK = (13, 13, 13, 230)
GREY = (136, 136, 136, 255)
RED = (204, 34, 0, 255)


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Intenta cargar Arial Black, fallback a default."""
    candidates_bold = [
        "C:/Windows/Fonts/ariblk.ttf",  # Arial Black
        "C:/Windows/Fonts/impact.ttf",
        "/System/Library/Fonts/Supplemental/Arial Black.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    candidates_regular = [
        "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for c in (candidates_bold if bold else candidates_regular):
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _draw_rounded(draw: ImageDraw.ImageDraw, box, radius, fill, outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _measure(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


# ─────────────────────────────────────────────────────────────
#  OVERLAYS
# ─────────────────────────────────────────────────────────────


def stat_card(data: dict) -> Image.Image:
    label = data.get("label", "DATO")
    value = data.get("value", "—")
    subtitle = data.get("subtitle", "")
    color = data.get("color", "#F5C400")

    w, h = 380, 200
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    _draw_rounded(d, (0, 0, w - 1, h - 1), 16, fill=(13, 13, 13, 235),
                  outline=tuple(int(color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) + (255,),
                  width=3)

    f_label = _get_font(20, bold=True)
    f_value = _get_font(64, bold=True)
    f_sub = _get_font(18, bold=False)

    d.text((20, 18), label.upper(), font=f_label, fill=WHITE)
    rgb = tuple(int(color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    d.text((20, 60), str(value), font=f_value, fill=rgb + (255,))
    if subtitle:
        d.text((20, h - 36), subtitle, font=f_sub, fill=GREY)
    return img


def name_tag(data: dict) -> Image.Image:
    name = data.get("name", "MARIA")
    color = data.get("color", "#F5C400")
    rgb = tuple(int(color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))

    f = _get_font(26, bold=True)
    img_tmp = Image.new("RGBA", (10, 10))
    d_tmp = ImageDraw.Draw(img_tmp)
    tw, th = _measure(d_tmp, name.upper(), f)
    w = tw + 60
    h = th + 30

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_rounded(d, (0, 0, w - 1, h - 1), 12, fill=(13, 13, 13, 220),
                  outline=rgb + (255,), width=2)
    # Bullet point
    d.ellipse((14, h // 2 - 6, 26, h // 2 + 6), fill=rgb + (255,))
    d.text((36, 13), name.upper(), font=f, fill=WHITE)
    return img


def section_indicator(data: dict) -> Image.Image:
    label = data.get("label", "BLOQUE")
    color = data.get("color", "#F5C400")
    rgb = tuple(int(color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))

    f = _get_font(22, bold=True)
    img_tmp = Image.new("RGBA", (10, 10))
    d_tmp = ImageDraw.Draw(img_tmp)
    tw, th = _measure(d_tmp, label.upper(), f)
    w = tw + 50
    h = th + 24

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_rounded(d, (0, 0, w - 1, h - 1), 8, fill=(245, 196, 0, 240))
    d.text((25, 11), label.upper(), font=f, fill=(13, 13, 13, 255))
    return img


def hierarchy_diagram(data: dict) -> Image.Image:
    """Diagrama vertical: titulo + lista de items conectados por linea."""
    title = data.get("title", "Jerarquia")
    items = data.get("items", ["IA", "ML", "DL", "LLM"])
    w, h = 360, 100 + len(items) * 60
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_rounded(d, (0, 0, w - 1, h - 1), 14, fill=(13, 13, 13, 230),
                  outline=YELLOW, width=2)
    f_title = _get_font(22, bold=True)
    f_item = _get_font(20, bold=True)
    d.text((20, 18), title.upper(), font=f_title, fill=YELLOW)
    cx = w // 2
    y = 60
    for i, it in enumerate(items):
        d.line([(cx, y), (cx, y + 20)], fill=GREY, width=2)
        y += 24
        d.rectangle((20, y, w - 20, y + 36), fill=(26, 26, 26, 255), outline=YELLOW)
        d.text((30, y + 8), str(it), font=f_item, fill=WHITE)
        y += 40
    return img


def two_column_compare(data: dict) -> Image.Image:
    left_t = data.get("left_title", "A")
    right_t = data.get("right_title", "B")
    left_items = data.get("left_items", [])
    right_items = data.get("right_items", [])
    w, h = 600, 240
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_rounded(d, (0, 0, w - 1, h - 1), 14, fill=(13, 13, 13, 230),
                  outline=YELLOW, width=2)
    f_t = _get_font(22, bold=True)
    f_i = _get_font(18)
    d.text((30, 18), left_t.upper(), font=f_t, fill=YELLOW)
    d.text((w // 2 + 20, 18), right_t.upper(), font=f_t, fill=BLUE)
    d.line([(w // 2, 50), (w // 2, h - 20)], fill=GREY, width=1)
    for i, it in enumerate(left_items[:5]):
        d.text((30, 60 + i * 28), f"• {it}", font=f_i, fill=WHITE)
    for i, it in enumerate(right_items[:5]):
        d.text((w // 2 + 20, 60 + i * 28), f"• {it}", font=f_i, fill=WHITE)
    return img


def bar_chart(data: dict) -> Image.Image:
    title = data.get("title", "Comparativa")
    bars = data.get("bars", [])  # [{"label":..., "value": 0-100}, ...]
    w, h = 460, 80 + len(bars) * 40
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_rounded(d, (0, 0, w - 1, h - 1), 14, fill=(13, 13, 13, 230),
                  outline=YELLOW, width=2)
    f_t = _get_font(20, bold=True)
    f_l = _get_font(16)
    d.text((20, 16), title.upper(), font=f_t, fill=YELLOW)
    y = 60
    max_val = max((b.get("value", 0) for b in bars), default=100) or 100
    for b in bars:
        d.text((20, y), str(b.get("label", "")), font=f_l, fill=WHITE)
        bar_w = int((w - 200) * (b.get("value", 0) / max_val))
        d.rectangle((180, y + 2, 180 + bar_w, y + 22), fill=YELLOW)
        d.text((180 + bar_w + 8, y), f"{b.get('value', 0)}", font=f_l, fill=GREY)
        y += 32
    return img


def warning_badge(data: dict) -> Image.Image:
    label = data.get("label", "ALERTA")
    f = _get_font(22, bold=True)
    img_tmp = Image.new("RGBA", (10, 10))
    d_tmp = ImageDraw.Draw(img_tmp)
    tw, th = _measure(d_tmp, label.upper(), f)
    w = tw + 60
    h = th + 24
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_rounded(d, (0, 0, w - 1, h - 1), 8, fill=RED, outline=(255, 255, 255, 255), width=2)
    d.text((30, 11), label.upper(), font=f, fill=WHITE)
    return img


def regulation_alert(data: dict) -> Image.Image:
    title = data.get("title", "EU AI ACT")
    text = data.get("text", "Riesgo alto · Multa 35M€")
    w, h = 420, 130
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_rounded(d, (0, 0, w - 1, h - 1), 12, fill=(40, 8, 4, 240),
                  outline=RED, width=3)
    f_t = _get_font(24, bold=True)
    f_b = _get_font(18)
    d.text((20, 16), title.upper(), font=f_t, fill=RED)
    d.text((20, 60), text, font=f_b, fill=WHITE)
    return img


def highlight_quote(data: dict) -> Image.Image:
    text = (data.get("text", "...") or "...").strip()
    author = data.get("author", "")
    f_q = _get_font(28, bold=True)
    f_a = _get_font(20)

    # Layout: max width 1100px, padding 30px, line height ~38px
    max_text_w = 1040
    padding = 30
    line_h = 38

    # Word-wrap manual usando textbbox para medir cada linea
    img_tmp = Image.new("RGBA", (10, 10))
    d_tmp = ImageDraw.Draw(img_tmp)

    def _wrap(quoted: str) -> list[str]:
        words = quoted.split()
        lines, current = [], ""
        for w in words:
            tentative = (current + " " + w).strip()
            bbox = d_tmp.textbbox((0, 0), tentative, font=f_q)
            if bbox[2] - bbox[0] <= max_text_w:
                current = tentative
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)
        return lines

    quoted = f"“{text}”"
    lines = _wrap(quoted)

    text_h = len(lines) * line_h
    author_h = (line_h + 8) if author else 0
    box_h = padding + text_h + author_h + padding
    box_w = max_text_w + 2 * padding

    img = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_rounded(d, (0, 0, box_w - 1, box_h - 1), 14,
                  fill=(13, 13, 13, 235), outline=YELLOW, width=2)

    y = padding
    for ln in lines:
        d.text((padding, y), ln, font=f_q, fill=WHITE)
        y += line_h
    if author:
        d.text((padding, box_h - padding - line_h), f"— {author}",
               font=f_a, fill=YELLOW)
    return img


def end_card(data: dict) -> Image.Image:
    title = data.get("title", "MaquinarIA Pesada")
    sub = data.get("subtitle", "Hasta el proximo episodio")
    w, h = 720, 220
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_rounded(d, (0, 0, w - 1, h - 1), 18, fill=(13, 13, 13, 240),
                  outline=YELLOW, width=4)
    f_t = _get_font(40, bold=True)
    f_s = _get_font(22)
    d.text((30, 40), title, font=f_t, fill=YELLOW)
    d.text((30, h - 60), sub, font=f_s, fill=WHITE)
    return img


def recap_grid(data: dict) -> Image.Image:
    items = data.get("items", [])
    cols = 2
    rows = max(1, (len(items) + cols - 1) // cols)
    cell_w, cell_h = 280, 80
    pad = 12
    w = cols * cell_w + (cols + 1) * pad
    h = rows * cell_h + (rows + 1) * pad + 50
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_rounded(d, (0, 0, w - 1, h - 1), 16, fill=(13, 13, 13, 230),
                  outline=YELLOW, width=2)
    f_t = _get_font(22, bold=True)
    f_i = _get_font(18)
    d.text((20, 14), "CONCEPTOS CLAVE", font=f_t, fill=YELLOW)
    for idx, it in enumerate(items[:cols * rows]):
        r = idx // cols
        c = idx % cols
        x = pad + c * (cell_w + pad)
        y = 50 + pad + r * (cell_h + pad)
        d.rectangle((x, y, x + cell_w, y + cell_h),
                    fill=(26, 26, 26, 255), outline=YELLOW)
        d.text((x + 10, y + cell_h // 2 - 10), str(it)[:32], font=f_i, fill=WHITE)
    return img


# ─────────────────────────────────────────────────────────────
#  REGISTRY
# ─────────────────────────────────────────────────────────────

OVERLAY_BUILDERS = {
    "stat_card":          stat_card,
    "name_tag":           name_tag,
    "section_indicator":  section_indicator,
    "hierarchy_diagram":  hierarchy_diagram,
    "two_column_compare": two_column_compare,
    "bar_chart":          bar_chart,
    "warning_badge":      warning_badge,
    "regulation_alert":   regulation_alert,
    "highlight_quote":    highlight_quote,
    "end_card":           end_card,
    "recap_grid":         recap_grid,
}


def build_overlay(overlay_type: str, data: dict) -> Image.Image | None:
    fn = OVERLAY_BUILDERS.get(overlay_type)
    if fn is None:
        # Fallback genrico: name_tag con el texto del overlay
        return name_tag({"name": overlay_type, "color": "#888888"})
    try:
        return fn(data or {})
    except Exception:
        return None
