#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normalizar_guiones.py
---------------------
LEGACY / STANDALONE — NO forma parte del pipeline de generación.
Los episodios se generan ÚNICAMENTE con generar_guion.py (M) y
generar_guion_t.py (T). Ver GENERACION.md.

⚠️  Este script genera el formato PRE-v5 (# BLOQUE_1..4, # INSERCION_1/2), que
los specs T/M v5 marcan como secciones PROHIBIDAS. NO ejecutar sobre guiones
ya en formato v5: el resultado sería rechazado por el validador. Se conserva
solo como conversor de guiones de codex antiguo (formato B legado).

Convierte guiones del formato B (legado) al formato A requerido por podcast_spec.py,
y corrige los problemas estructurales de los guiones en formato A.

FORMATO B (legado, generado por codex antiguo):
  # INTRO              → (hook, sin frase de cierre, sin secciones de presentación)
  # NÚCLEO TEMÁTICO    → (todo el contenido sin sub-secciones)
  # CIERRE CON CTA     → (cierre sin frases fijas)

FORMATO A (correcto, validado por podcast_spec.py):
  # HOOK               (con "Esto es MaquinarIA Pesada. Arrancamos." al final)
  # INTRO_SONIDO
  # [INTRO - SONIDO DE MAQUINAS ARRANCANDO - 8-10 segundos]
  # SALUDO_Y_PRESENTACION
  # BLOQUE_1 … # BLOQUE_4+
  # INSERCION_1 (… INSERCION_2)
  # CIERRE_CONCEPTOS   (con frase fija de apertura)
  # CIERRE_FINAL       (con frase fija de despedida)
  # VERIFICACIONES

Uso:
  python normalizar_guiones.py                   # todos los guiones en Guiones/
  python normalizar_guiones.py --file M2_T_...txt
  python normalizar_guiones.py --dry-run         # muestra cambios sin escribir
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Forzar UTF-8 en consola Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ─── Config ───────────────────────────────────────────────────────────────────

BASE_DIR   = Path(__file__).parent
GUIONES_DIR = BASE_DIR / "Guiones"

# Fuente única de verdad de las frases fijas: el spec JSON (ver podcast_spec.py).
sys.path.insert(0, str(BASE_DIR))
from podcast_spec import load_spec  # noqa: E402

_RULES = load_spec(BASE_DIR / "PODCAST_M_SPEC.md")["script_rules"]
HOOK_CLOSING_PHRASE      = _RULES["hook_closing_phrase"]
INTRO_COMMENT            = "# " + _RULES["intro_comment"]
CONCEPTS_CLOSING_PHRASE  = _RULES["concepts_closing_phrase"]
FINAL_CLOSING_PHRASE     = _RULES["final_closing_phrase"]

SPEAKER_RE = re.compile(r"^(IAGO|MAR[IÍ]A)\s*:", re.IGNORECASE)
# Captura nombres de seccion: MAYUSCULAS, digitos, guion_bajo, espacio, guion, em-dash, en-dash
# Excluye lineas de comentario (con minusculas, dos-puntos, barras, tildes, etc.)
SECTION_RE = re.compile(r"^#\s+([A-Z\xc1\xc9\xcd\xd3\xda\xd1][A-Z\xc1\xc9\xcd\xd3\xda\xd10-9_ \-–—]*)\s*$")


# ─── Data structures ──────────────────────────────────────────────────────────

@dataclass
class Section:
    name: str             # '' → file header (before first section)
    lines: list[str] = field(default_factory=list)

    def has_phrase(self, phrase: str) -> bool:
        text = "\n".join(self.lines)
        return phrase.lower() in text.lower()

    def speaker_lines(self) -> list[int]:
        """Índices de las líneas que son intervenciones de speaker."""
        return [i for i, l in enumerate(self.lines) if SPEAKER_RE.match(l.strip())]

    def text(self) -> str:
        return "\n".join(self.lines)


def parse_sections(text: str) -> list[Section]:
    """Divide el guion en secciones. La primera sección ('') es el header."""
    sections: list[Section] = [Section(name="")]
    for line in text.splitlines():
        m = SECTION_RE.match(line.strip())
        if m:
            title = m.group(1).strip()
            sections.append(Section(name=title))
        else:
            sections[-1].lines.append(line)
    return sections


def render_sections(sections: list[Section]) -> str:
    parts: list[str] = []
    for sec in sections:
        if sec.name:
            parts.append(f"# {sec.name}")
        if sec.lines:
            parts.append("\n".join(sec.lines))
    return "\n".join(parts)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def module_number(path: Path) -> int:
    m = re.search(r"M(\d+)", path.stem)
    return int(m.group(1)) if m else 0


def expected_opener(mod: int) -> str:
    return "MARIA" if mod % 2 == 0 else "IAGO"


def normalize_speaker_name(raw: str) -> str:
    """Devuelve 'IAGO' o 'MARIA' (sin tilde)."""
    s = raw.strip().upper()
    if "IAGO" in s:
        return "IAGO"
    return "MARIA"


def first_speaker(section: Section) -> Optional[str]:
    for line in section.lines:
        m = SPEAKER_RE.match(line.strip())
        if m:
            return normalize_speaker_name(m.group(1))
    return None


def swap_speakers_in_section(section: Section) -> None:
    """Intercambia IAGO ↔ MARÍA en todas las líneas de la sección."""
    new_lines = []
    for line in section.lines:
        # Mantiene la forma original del nombre (IAGO, MARÍA, MARIA)
        l = re.sub(r"^(\s*)(IAGO)(\s*:)", r"\1__IAGO__\3", line, flags=re.IGNORECASE)
        l = re.sub(r"^(\s*)(MAR[IÍ]A)(\s*:)", r"\1IAGO\3", l, flags=re.IGNORECASE)
        l = re.sub(r"^(\s*)__IAGO__(\s*:)", r"\1MARÍA\2", l)
        new_lines.append(l)
    section.lines = new_lines


def last_nonempty_speaker_line_idx(section: Section) -> int:
    """Índice de la última línea con speaker en la sección (-1 si no hay)."""
    last = -1
    for i, line in enumerate(section.lines):
        if SPEAKER_RE.match(line.strip()):
            last = i
    return last


def add_hook_closing(section: Section, opener: str) -> None:
    """Añade la frase de cierre del hook si no existe."""
    if section.has_phrase(HOOK_CLOSING_PHRASE):
        return
    speaker = "IAGO" if opener == "IAGO" else "MARÍA"
    closing_line = f"{speaker}: [directo] {HOOK_CLOSING_PHRASE}"
    last_idx = last_nonempty_speaker_line_idx(section)
    if last_idx >= 0:
        section.lines.insert(last_idx + 1, closing_line)
    else:
        section.lines.append(closing_line)


def make_intro_sonido() -> Section:
    sec = Section(name="INTRO_SONIDO")
    sec.lines = ["", INTRO_COMMENT, ""]
    return sec


def make_saludo(mod: int) -> Section:
    """Genera el bloque de saludo y presentación boilerplate."""
    sec = Section(name="SALUDO_Y_PRESENTACION")
    tema_map = {
        0: "el módulo cero, la introducción estratégica a la I.A",
        1: "el módulo uno, los fundamentos y el razonamiento en I.A",
        2: "el módulo dos, las matemáticas que necesitas para la I.A",
        3: "el módulo tres, el machine learning clásico",
        4: "el módulo cuatro, el deep learning",
        5: "el módulo cinco, el procesamiento del lenguaje natural y los grandes modelos",
        6: "el módulo seis, la ingeniería de prompts",
        7: "el módulo siete, los sistemas RAG",
        8: "el módulo ocho, la ingeniería y operaciones de modelos de lenguaje",
        9: "el módulo nueve, la infraestructura y el despliegue",
        10: "el módulo diez, los sistemas multi-agente",
        11: "el módulo once, la automatización inteligente",
        12: "el módulo doce, la seguridad en I.A",
        13: "el módulo trece, la gobernanza y la ética en I.A",
        14: "el módulo catorce, la estrategia empresarial con I.A",
    }
    tema = tema_map.get(mod, f"el módulo {mod}")
    sec.lines = [
        "",
        f"IAGO: [conversacional] Bienvenidos a MaquinarIA Pesada. Soy Yago, y esto es {tema}.",
        "",
        "MARÍA: [conversacional] Y yo soy María. Antes de arrancar, la advertencia de siempre: "
        "este episodio ha sido generado por un sistema automático de inteligencia artificial "
        "y puede contener errores. Contrastad siempre con fuentes especializadas.",
        "",
        "IAGO: [directo] Vamos allá.",
        "",
    ]
    return sec


def split_nucleo_into_bloques(section: Section) -> list[Section]:
    """
    Divide las líneas de NÚCLEO TEMÁTICO en BLOQUE_1..4 + INSERCION_1.
    Heurística: divide el cuerpo de intervenciones en cuartos y coloca
    los marcadores de bloque entre grupos. INSERCION_1 va entre los bloques 2 y 3.
    """
    lines = section.lines
    speaker_idxs = [i for i, l in enumerate(lines) if SPEAKER_RE.match(l.strip())]
    n = len(speaker_idxs)

    if n < 8:
        # Muy pocas líneas: un solo bloque
        bloque = Section(name="BLOQUE_1")
        bloque.lines = lines[:]
        return [bloque]

    # Puntos de corte aproximados en cuartos
    # Para 4 bloques necesitamos 3 puntos de corte + 1 para INSERCION
    cuts_at_quarter = [n // 4, n // 2, 3 * n // 4]

    # Convertir índices de speaker a índices de línea (tomamos línea ANTES del grupo)
    def line_idx_for_speaker(speaker_pos: int) -> int:
        """Índice de línea correspondiente al speaker número speaker_pos."""
        return speaker_idxs[min(speaker_pos, len(speaker_idxs) - 1)]

    cut_line_idxs = [line_idx_for_speaker(c) for c in cuts_at_quarter]

    # Asegura que los cortes están ordenados y son distintos
    cut_line_idxs = sorted(set(cut_line_idxs))
    while len(cut_line_idxs) < 3:
        cut_line_idxs.append(cut_line_idxs[-1] + 1)

    c1, c2, c3 = cut_line_idxs[0], cut_line_idxs[1], cut_line_idxs[2]

    # Busca un buen punto de corte real (entre bloques, no en medio de una frase)
    # Preferimos un salto de línea vacía justo antes del índice de corte
    def find_nearest_blank(idx: int, lines: list[str], window: int = 5) -> int:
        for offset in range(0, window):
            for delta in (offset, -offset):
                check = idx + delta
                if 0 <= check < len(lines) and lines[check].strip() == "":
                    return check
        return idx  # fallback

    c1 = find_nearest_blank(c1, lines)
    c2 = find_nearest_blank(c2, lines)
    c3 = find_nearest_blank(c3, lines)

    segs = [
        lines[:c1],
        lines[c1:c2],
        lines[c2:c3],
        lines[c3:],
    ]

    def make_insercion(num: int) -> Section:
        ins = Section(name=f"INSERCION_{num}")
        ins.lines = ["", f"# [INSERCION {num} - dato de actualidad o estadistica relevante]", ""]
        return ins

    # La validacion requiere min_insertions = max(1, n_bloques // 2) = max(1, 4//2) = 2
    # Ponemos INSERCION_1 tras BLOQUE_2 e INSERCION_2 tras BLOQUE_3
    result: list[Section] = []
    for i, seg in enumerate(segs, start=1):
        b = Section(name=f"BLOQUE_{i}")
        b.lines = seg if seg else [""]
        result.append(b)
        if i == 2:
            result.append(make_insercion(1))
        elif i == 3:
            result.append(make_insercion(2))

    return result


def split_cierre_cta(section: Section) -> list[Section]:
    """
    Divide el CIERRE CON CTA en CIERRE_CONCEPTOS + CIERRE_FINAL.
    Heurística: los últimos 2 speaker exchanges van a CIERRE_FINAL;
    el resto va a CIERRE_CONCEPTOS.
    Añade las frases fijas requeridas si no existen.
    """
    lines = section.lines
    speaker_idxs = [i for i, l in enumerate(lines) if SPEAKER_RE.match(l.strip())]
    n = len(speaker_idxs)

    # CIERRE_FINAL: últimas 2 intervenciones (MARIA + IAGO idealmente)
    if n >= 4:
        split_at_speaker = speaker_idxs[-2]   # penúltima intervención
        # Busca línea vacía justo antes
        cut = split_at_speaker
        for offset in range(1, 6):
            candidate = split_at_speaker - offset
            if candidate >= 0 and lines[candidate].strip() == "":
                cut = candidate
                break
    elif n >= 2:
        cut = speaker_idxs[-1]  # última intervención en CIERRE_FINAL
    else:
        cut = len(lines)

    conceptos_lines = lines[:cut]
    final_lines = lines[cut:]

    # ── CIERRE_CONCEPTOS ──────────────────────────────────────────────────────
    cierre_conceptos = Section(name="CIERRE_CONCEPTOS")
    # Añade frase fija de apertura si no existe
    if not any(CONCEPTS_CLOSING_PHRASE.lower() in l.lower() for l in conceptos_lines):
        cierre_conceptos.lines = [
            "",
            f"MARÍA: [directo] {CONCEPTS_CLOSING_PHRASE}. Repasa los puntos clave de este episodio.",
            "",
        ] + conceptos_lines
    else:
        cierre_conceptos.lines = conceptos_lines

    # ── CIERRE_FINAL ──────────────────────────────────────────────────────────
    cierre_final = Section(name="CIERRE_FINAL")
    if not any(FINAL_CLOSING_PHRASE.lower() in l.lower() for l in final_lines):
        # Inserta la frase antes de la última línea de speaker
        sp_in_final = [i for i, l in enumerate(final_lines) if SPEAKER_RE.match(l.strip())]
        insert_before = sp_in_final[-1] if sp_in_final else len(final_lines)
        final_with_phrase = (
            final_lines[:insert_before]
            + ["", f"MARÍA: [conversacional] {FINAL_CLOSING_PHRASE}", ""]
            + final_lines[insert_before:]
        )
        cierre_final.lines = final_with_phrase
    else:
        cierre_final.lines = final_lines

    return [cierre_conceptos, cierre_final]


def make_verificaciones() -> Section:
    sec = Section(name="VERIFICACIONES")
    sec.lines = [
        "",
        "# VERIFICACION 1 - ESTRUCTURA",
        "# OK Normalizado por normalizar_guiones.py",
        "# Pendiente: revisar manualmente el contenido de bloques y frases fijas",
        "",
    ]
    return sec


# ─── Transformaciones principales ─────────────────────────────────────────────

def transform_format_b(sections: list[Section], mod: int) -> tuple[list[Section], list[str]]:
    """
    Convierte Format B (INTRO / NUCLEO TEMATICO / CIERRE CON CTA) a Format A.
    Devuelve (secciones_nuevas, lista_de_warnings).
    Soporta multiples secciones NUCLEO TEMATICO (con sub-titulos via em-dash).
    """
    warnings: list[str] = []
    # Indice por nombre (primera ocurrencia) para lookups unicos
    by_name: dict[str, Section] = {}
    for s in sections:
        key = s.name.upper().strip()
        if key not in by_name:
            by_name[key] = s
    # Lista ordenada de todos los nombres (permite multiples con el mismo prefijo)
    all_names: list[str] = [s.name.upper().strip() for s in sections]

    # Header (lineas antes del primer #)
    header_sec = sections[0] if sections and sections[0].name == "" else Section(name="")

    # ── HOOK ─────────────────────────────────────────────────────────────────
    intro_key = next((k for k in all_names if re.match(r"INTRO$", k)), None)
    if intro_key is None:
        warnings.append("No se encontro seccion # INTRO en guion B.")
        hook = Section(name="HOOK", lines=[""])
    else:
        hook = Section(name="HOOK", lines=by_name.get(intro_key, Section(name="HOOK")).lines[:])

    opener = expected_opener(mod)
    hook_first = first_speaker(hook)
    if hook_first and hook_first != opener:
        warnings.append(
            f"Speaker parity: modulo {mod} necesita {opener} pero abre {hook_first}. "
            f"Intercambiando IAGO<->MARIA en HOOK."
        )
        swap_speakers_in_section(hook)

    add_hook_closing(hook, opener)

    # ── INTRO_SONIDO ─────────────────────────────────────────────────────────
    intro_sonido = make_intro_sonido()

    # ── SALUDO_Y_PRESENTACION ─────────────────────────────────────────────────
    saludo = make_saludo(mod)

    # ── NUCLEO TEMATICO → BLOQUE_1…4 + INSERCION_1 ───────────────────────────
    # Consolida multiples secciones NUCLEO TEMATICO (incluyendo las con sub-titulo)
    nucleo_keys = [k for k in all_names if re.match(r"N[U\xda]CLEO\s+TEM", k, re.IGNORECASE)]
    bloque_creativo_key = next(
        (k for k in all_names if re.match(r"BLOQUE\s+CREATIVO", k, re.IGNORECASE)), None
    )

    if nucleo_keys:
        all_nucleo_lines: list[str] = []
        seen: set[str] = set()
        for k in nucleo_keys:
            if k not in seen:
                seen.add(k)
                if k in by_name:
                    all_nucleo_lines.extend(by_name[k].lines)
        if len(nucleo_keys) > 1:
            warnings.append(f"Consolidadas {len(nucleo_keys)} secciones NUCLEO TEMATICO.")
        nucleo_sec = Section(name="NUCLEO_MERGED", lines=all_nucleo_lines)
        if bloque_creativo_key and bloque_creativo_key in by_name:
            nucleo_sec.lines = nucleo_sec.lines + by_name[bloque_creativo_key].lines
            warnings.append("BLOQUE CREATIVO fusionado al final del NUCLEO TEMATICO.")
        bloque_sections = split_nucleo_into_bloques(nucleo_sec)
    else:
        warnings.append("No se encontro # NUCLEO TEMATICO. Se crea BLOQUE_1 vacio.")
        bloque_sections = [Section(name="BLOQUE_1", lines=[""])]

    # ── INSERCION_X adicionales (las que esten fuera del NUCLEO) ─────────────
    insercion_extras: list[Section] = []
    for k in all_names:
        m_ins = re.match(r"INSERCI[OO]N[_ ]?(\d+)", k, re.IGNORECASE)
        if m_ins and int(m_ins.group(1)) > 1 and k in by_name:
            insercion_extras.append(Section(name=f"INSERCION_{m_ins.group(1)}", lines=by_name[k].lines[:]))

    # ── CIERRE CON CTA → CIERRE_CONCEPTOS + CIERRE_FINAL ────────────────────
    cierre_key = next((k for k in all_names if re.match(r"CIERRE\s+CON\s+CTA", k, re.IGNORECASE)), None)
    if cierre_key and cierre_key in by_name:
        cierre_sections = split_cierre_cta(by_name[cierre_key])
    else:
        warnings.append("No se encontro # CIERRE CON CTA. Se crean secciones vacias.")
        cc = Section(name="CIERRE_CONCEPTOS")
        cc.lines = [f"MARIA: [directo] {CONCEPTS_CLOSING_PHRASE}."]
        cf = Section(name="CIERRE_FINAL")
        cf.lines = [f"MARIA: [conversacional] {FINAL_CLOSING_PHRASE}",
                    "IAGO: [ironico] Nos escuchamos."]
        cierre_sections = [cc, cf]

    # ── VERIFICACIONES ────────────────────────────────────────────────────────
    verificaciones = make_verificaciones()

    # ── Ensamblaje ────────────────────────────────────────────────────────────
    result: list[Section] = (
        [header_sec, hook, intro_sonido, saludo]
        + bloque_sections
        + insercion_extras
        + cierre_sections
        + [verificaciones]
    )
    return result, warnings


def fix_format_a(sections: list[Section], mod: int) -> tuple[list[Section], list[str]]:
    """
    Corrige problemas en guiones que ya están en Formato A:
    - Speaker parity en HOOK
    - Frases fijas faltantes
    - Sección VERIFICACIONES
    """
    warnings: list[str] = []
    by_name = {s.name.upper().strip(): s for s in sections}

    hook = by_name.get("HOOK")
    opener = expected_opener(mod)

    if hook:
        hook_first = first_speaker(hook)
        if hook_first and hook_first != opener:
            warnings.append(
                f"Parity: módulo {mod} necesita {opener} pero abre {hook_first}. "
                f"Intercambiando IAGO↔MARÍA en HOOK."
            )
            swap_speakers_in_section(hook)
        add_hook_closing(hook, opener)
    else:
        warnings.append("No se encontró sección # HOOK en guion A.")

    # Asegura frases fijas en cierre
    cierre_conceptos = by_name.get("CIERRE_CONCEPTOS")
    if cierre_conceptos and not cierre_conceptos.has_phrase(CONCEPTS_CLOSING_PHRASE):
        cierre_conceptos.lines = [
            "", f"MARÍA: [directo] {CONCEPTS_CLOSING_PHRASE}.", ""
        ] + cierre_conceptos.lines
        warnings.append("Frase de apertura de CIERRE_CONCEPTOS añadida.")

    cierre_final = by_name.get("CIERRE_FINAL")
    if cierre_final and not cierre_final.has_phrase(FINAL_CLOSING_PHRASE):
        sp_idxs = [i for i, l in enumerate(cierre_final.lines) if SPEAKER_RE.match(l.strip())]
        ins = sp_idxs[-1] if sp_idxs else len(cierre_final.lines)
        cierre_final.lines = (
            cierre_final.lines[:ins]
            + [f"MARÍA: [conversacional] {FINAL_CLOSING_PHRASE}"]
            + cierre_final.lines[ins:]
        )
        warnings.append("Frase de cierre final añadida en CIERRE_FINAL.")

    # Asegura VERIFICACIONES
    if "VERIFICACIONES" not in by_name:
        sections = list(sections) + [make_verificaciones()]
        warnings.append("Sección VERIFICACIONES añadida.")

    return sections, warnings


# ─── Detección de formato ─────────────────────────────────────────────────────

def detect_format(sections: list[Section]) -> str:
    """Devuelve 'A', 'B', 'A_hybrid' o 'unknown'."""
    names = {s.name.upper().strip() for s in sections}

    has_hook         = "HOOK" in names
    has_intro        = any(re.match(r"INTRO$", n) for n in names)
    has_nucleo       = any(re.match(r"N[U\xda]CLEO\s+TEM", n, re.IGNORECASE) for n in names)
    has_cierre_cta   = any(re.match(r"CIERRE\s+CON\s+CTA", n, re.IGNORECASE) for n in names)
    has_bloque       = any(re.match(r"BLOQUE_\d", n) for n in names)
    has_saludo       = "SALUDO_Y_PRESENTACION" in names
    has_intro_sonido = "INTRO_SONIDO" in names

    # Formato A puro: tiene HOOK sin NUCLEO
    if has_hook:
        return "A"
    # Formato hibrido A: INTRO como hook pero estructura interna de A
    if has_intro and (has_intro_sonido or has_bloque or has_saludo) and not has_nucleo:
        return "A_hybrid"
    # Formato B: tiene INTRO + NUCLEO o CIERRE CTA
    if has_intro and (has_nucleo or has_cierre_cta):
        return "B"
    return "unknown"


# ─── Lectura / escritura ──────────────────────────────────────────────────────

def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="strict")
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            raise
    return path.read_text(encoding="latin-1", errors="replace")


# ─── Proceso principal por archivo ────────────────────────────────────────────

def normalize_file(path: Path, dry_run: bool = False) -> dict:
    text = read_text(path)
    sections = parse_sections(text)
    fmt = detect_format(sections)
    mod = module_number(path)

    if fmt == "unknown":
        return {"path": path, "status": "SKIP", "reason": "Formato desconocido", "warnings": []}

    opener = expected_opener(mod)

    if fmt == "B":
        new_sections, warnings = transform_format_b(sections, mod)
        action = "B->A"
    elif fmt == "A_hybrid":
        # Solo renombra INTRO->HOOK y aplica fix_format_a
        for sec in sections:
            if re.match(r"INTRO$", sec.name.upper().strip()):
                sec.name = "HOOK"
                break
        new_sections, warnings = fix_format_a(sections, mod)
        warnings.insert(0, "Hibrido: INTRO renombrado a HOOK.")
        action = "hybrid->A"
    else:  # "A"
        new_sections, warnings = fix_format_a(sections, mod)
        action = "A->fix"

    new_text = render_sections(new_sections)

    if not dry_run:
        # Backup
        bak = path.with_suffix(".txt.bak")
        if not bak.exists():
            bak.write_text(text, encoding="utf-8")
        path.write_text(new_text, encoding="utf-8")

    return {
        "path": path,
        "status": "OK",
        "action": action,
        "format_detected": fmt,
        "mod": mod,
        "expected_opener": opener,
        "warnings": warnings,
        "dry_run": dry_run,
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Normaliza guiones al Formato A")
    parser.add_argument("--file", default=None, help="Archivo .txt específico (ruta relativa a Guiones/)")
    parser.add_argument("--dry-run", action="store_true", help="Muestra cambios sin escribir")
    parser.add_argument("--all",  action="store_true", help="Procesa todos los guiones (por defecto si no se pasa --file)")
    args = parser.parse_args()

    if args.file:
        candidates = [GUIONES_DIR / args.file]
    else:
        candidates = sorted(GUIONES_DIR.glob("M*.txt"))

    if not candidates:
        print("No se encontraron guiones para procesar.")
        sys.exit(1)

    total_ok = total_skip = total_warn = 0

    for path in candidates:
        if not path.exists():
            print(f"[SKIP] No existe: {path}")
            total_skip += 1
            continue

        result = normalize_file(path, dry_run=args.dry_run)
        status = result.get("status", "?")
        action = result.get("action", "")
        fmt    = result.get("format_detected", "?")
        mod    = result.get("mod", "?")
        warns  = result.get("warnings", [])

        dr = " [DRY-RUN]" if args.dry_run else ""
        print(f"\n{'='*60}")
        print(f"  {path.name}")
        print(f"  Modulo : {mod}  |  Formato: {fmt}  |  Accion: {action}{dr}")

        if status == "SKIP":
            print(f"  [SKIP] {result.get('reason', '')}")
            total_skip += 1
        elif status == "OK":
            if warns:
                total_warn += 1
                for w in warns:
                    print(f"  [!] {w}")
            else:
                total_ok += 1
                print("  [OK] Sin advertencias.")

    print(f"\n{'='*60}")
    print(f"RESUMEN: OK={total_ok}  CON_WARN={total_warn}  SKIP={total_skip}")
    print(f"{'  [DRY-RUN: ningún archivo modificado]' if args.dry_run else ''}")


if __name__ == "__main__":
    # Bitácora diaria centralizada (logs/run/). Si daylog fallara, el pipeline
    # sigue igual gracias al nullcontext de respaldo.
    import sys as _sys
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="normalizar_guiones.py", params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        main()
