"""
Identidad visual de MaquinarIA Pesada - REGLAS ABSOLUTAS.
Estos colores y reglas se usan en todo el pipeline.
"""

BRAND = {
    "color_amarillo_cat":      "#F5C400",
    "color_negro":             "#0D0D0D",
    "color_gris_rejilla":      "#1A1A1A",
    "color_acero":             "#888888",
    "color_azul_electrico":    "#4DB8FF",
    "color_blanco_subtitulos": "#E8E8E8",
    "color_alerta":            "#CC2200",
    "voz_maria_color":         "#F5C400",
    "voz_iago_color":          "#4DB8FF",
    "fuente_titulos":          "Arial Black",
    "fuente_datos":            "system-ui",
}

LOGO_WATERMARK = {
    "position":         "bottom_right",
    "margin_px":        12,
    "size_px":          72,
    "opacity":          0.65,
    "zone_protected":   (1836, 996, 1920, 1080),
}

RESOLUTIONS = {
    "1920x1080": (1920, 1080),
    "1280x720":  (1280, 720),
}

POSITIONS_1080P = {
    "TOP_LEFT":          (60, 60),
    "TOP_CENTER":        (760, 60),
    "TOP_RIGHT":         (1460, 60),
    "MID_LEFT":          (60, 440),
    "MID_CENTER":        (760, 440),
    "MID_RIGHT":         (1460, 440),
    "BOTTOM_LEFT":       (60, 800),
    "BOTTOM_CENTER":     (760, 800),
    "BOTTOM_RIGHT_SAFE": (1460, 800),
    "BOTTOM_FULL_WIDTH": (60, 920),
}

SECTION_LABELS = {
    "INTRO_SONIDO":       "Intro",
    "VERIFICACIONES":     "Verificaciones",
    "INTRODUCCION":       "Introduccion",
    "BLOQUE_1":           "Bloque 1",
    "BLOQUE_2":           "Bloque 2",
    "BLOQUE_3":           "Bloque 3",
    "BLOQUE_4":           "Bloque 4",
    "CIERRE_CONCEPTOS":   "Conceptos clave",
    "DESPEDIDA":          "Despedida",
    "OUTRO":              "Outro",
}

STICKERS_PROMPTS = {
    "nobody_reads_tos":  "small humorous warning icon, terms of service, scroll of fine print",
    "winter_is_coming":  "snowy mountain peaks with cold wind, bleak winter mood",
    "linkedin_guru":     "cartoon man in suit pointing dramatically, fake guru style",
    "expensive_mistake": "money flying away, broken piggy bank",
    "speedrun":          "running stick figure leaving trail, blurry speed lines",
    "this_is_fine":      "small dog sitting at table, calm but room is on fire",
    "lawyer_up":         "courthouse building with gavel and balance scales",
    "stonks":            "green up arrow chart, exaggerated growth meme",
    "wave_bye":          "cartoon hand waving goodbye, friendly farewell",
}


def hex_to_rgb(hex_color: str) -> tuple:
    """Convierte '#F5C400' a (245, 196, 0)."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple:
    r, g, b = hex_to_rgb(hex_color)
    return (r, g, b, alpha)
