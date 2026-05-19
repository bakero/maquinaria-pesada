"""Modelo del pipeline para la página Pizarra.

Define el grafo conceptual del generador:

  Claude (esfera) ──> PDF (cuadrado)
                              │
                              ▼
                  lanzar_produccion.py (esfera)
                              │
                              ▼
                         GUION (cuadrado)
                              │
                              ▼
              generate_escaleta.py (esfera)
                              │
                              ▼
                       ESCALETA (cuadrado)
                              │
                              ▼
              generar_episodio_v2.py (esfera)
                              │
                              ▼
                  EPISODIO (audio, cuadrado)

Cada nodo de tipo "componente" puede tener un path a su código fuente,
que la página renderiza en un panel lateral.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import paths


@dataclass
class Pieza:
    id: str
    label: str
    kind: str             # "component" (esfera) | "content" (cuadrado)
    icon: str = ""        # emoji para el centro del cuadrado
    code_path: str | None = None    # ruta relativa al repo, solo en componentes
    description: str = ""

    def code_full_path(self) -> Path | None:
        if not self.code_path:
            return None
        return paths.repo_root() / self.code_path


@dataclass
class Flecha:
    src: str
    dst: str
    label: str = ""


def pipeline_default() -> tuple[list[Pieza], list[Flecha]]:
    """Pipeline de referencia: Claude → PDF → guion → escaleta → audio."""
    piezas = [
        Pieza(
            id="claude",
            label="Claude",
            kind="component",
            icon="🤖",
            code_path="cockpit/core/ai_client.py",
            description="Modelo Anthropic Claude. Genera el PDF temático a partir del programa.",
        ),
        Pieza(
            id="pdf",
            label="PDF temático",
            kind="content",
            icon="📕",
            description="PDFs/Mn_T_<Slug>.pdf — material fuente del módulo.",
        ),
        Pieza(
            id="gen_guion",
            label="lanzar_produccion.py",
            kind="component",
            icon="📝",
            code_path="lanzar_produccion.py",
            description="Pipeline CLI canónico: PDF/glosario → guion .md (M/T/S) con generadores especialistas.",
        ),
        Pieza(
            id="guion",
            label="GUION",
            kind="content",
            icon="📄",
            description="Guiones/Mn_<Slug>.txt — texto del podcast.",
        ),
        Pieza(
            id="gen_escaleta",
            label="generate_escaleta.py",
            kind="component",
            icon="🗂️",
            code_path="maquinaria_pesada_pipeline/tools/generate_escaleta.py",
            description="Convierte el guion en escaleta estructurada por bloques/escenas.",
        ),
        Pieza(
            id="escaleta",
            label="ESCALETA",
            kind="content",
            icon="🗒️",
            description="escaletas/Mn_*.md — guion estructurado por bloques.",
        ),
        Pieza(
            id="gen_audio",
            label="generar_episodio_v2.py",
            kind="component",
            icon="🎙️",
            code_path="generar_episodio_v2.py",
            description="Sintetiza audio MP3 con ElevenLabs a partir del guion + escaleta.",
        ),
        Pieza(
            id="episodio",
            label="EPISODIO (audio)",
            kind="content",
            icon="🎧",
            description="episodios/Mn.mp3 — podcast renderizado.",
        ),
    ]
    flechas = [
        Flecha("claude", "pdf", "genera"),
        Flecha("pdf", "gen_guion", "entrada"),
        Flecha("gen_guion", "guion", "produce"),
        Flecha("guion", "gen_escaleta", "entrada"),
        Flecha("gen_escaleta", "escaleta", "produce"),
        Flecha("escaleta", "gen_audio", "entrada"),
        Flecha("gen_audio", "episodio", "produce"),
    ]
    return piezas, flechas


def to_dot(piezas: list[Pieza], flechas: list[Flecha]) -> str:
    """Serializa el pipeline a Graphviz DOT.

    Componentes → círculo amarillo CAT (esferas).
    Contenidos  → caja gris con icono grande.
    """
    lines = [
        "digraph Pizarra {",
        '  rankdir=LR;',
        '  bgcolor="#0D0D0D";',
        '  node [fontname="Oswald", fontcolor="#F2F2F2"];',
        '  edge [color="#F5C400", fontcolor="#A8A8A8", fontname="Barlow Condensed", penwidth=2, arrowsize=1.1];',
    ]
    for p in piezas:
        if p.kind == "component":
            lines.append(
                f'  "{p.id}" ['
                f'shape=circle, style="filled,bold", fillcolor="#F5C400", '
                f'color="#D4A800", fontcolor="#0D0D0D", penwidth=2, width=1.4, '
                f'fixedsize=true, label="{p.icon}\\n{p.label}"];'
            )
        else:
            lines.append(
                f'  "{p.id}" ['
                f'shape=box, style="filled,bold", fillcolor="#1A1A1A", '
                f'color="#F5C400", fontcolor="#F2F2F2", penwidth=2, '
                f'label=<<FONT POINT-SIZE="28">{p.icon}</FONT><BR/>'
                f'<FONT POINT-SIZE="12">{p.label}</FONT>>];'
            )
    for f in flechas:
        lines.append(f'  "{f.src}" -> "{f.dst}" [label="{f.label}"];')
    lines.append("}")
    return "\n".join(lines)


# ---- Persistencia del lienzo editable -----------------------------------
# La página Pizarra deja editar el grafo (arrastrar, añadir, quitar). El
# lienzo se persiste como JSON para que sobreviva entre sesiones.


def board_path() -> Path:
    return paths.repo_root() / "cockpit" / "pizarra_board.json"


def load_board() -> dict | None:
    """Lee el lienzo guardado, o None si no existe (la página usa su default)."""
    p = board_path()
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def save_board(data: dict) -> None:
    """Persiste el lienzo (nodes + edges) tal cual lo manda la página."""
    p = board_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "nodes": data.get("nodes", []),
        "edges": data.get("edges", []),
    }
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
