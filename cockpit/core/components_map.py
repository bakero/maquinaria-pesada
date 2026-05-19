"""Mapa de componentes del sistema: nodos + aristas, persistido en JSON.

Tres tipos de nodos:
  - system: pieza de software (pipeline, cockpit page, módulo)
  - generated: output del sistema (guion, episodio, vídeo, asset)
  - generator: motor IA (Anthropic, OpenAI, ElevenLabs, Kling, Whisper)

Las aristas describen relaciones direccionadas:
  generator -- produces --> generated
  system    -- uses     --> generator
  generated -- feeds    --> system

Render: graphviz nativo (`st.graphviz_chart`). Edición: tablas Streamlit.
Una IA puede proponer cambios al JSON sin tocar la app — el path está en la
whitelist del sandbox.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import paths


@dataclass
class Node:
    id: str
    label: str
    kind: str  # system | generated | generator
    description: str = ""


@dataclass
class Edge:
    src: str
    dst: str
    relation: str = "uses"  # uses | produces | feeds | depends_on


@dataclass
class ComponentsMap:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> ComponentsMap:
        return cls(
            nodes=[Node(**n) for n in d.get("nodes", [])],
            edges=[Edge(**e) for e in d.get("edges", [])],
        )

    def to_dict(self) -> dict:
        return {
            "nodes": [asdict(n) for n in self.nodes],
            "edges": [asdict(e) for e in self.edges],
        }


def map_path() -> Path:
    return paths.repo_root() / "cockpit" / "components_map.json"


def load() -> ComponentsMap:
    p = map_path()
    if not p.exists():
        return _default_map()
    try:
        return ComponentsMap.from_dict(json.loads(p.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, TypeError):
        return _default_map()


def save(m: ComponentsMap) -> None:
    p = map_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(m.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


KIND_STYLE: dict[str, dict[str, str]] = {
    "system": {"shape": "box", "style": "filled", "fillcolor": "#1f2937", "fontcolor": "white"},
    "generated": {"shape": "note", "style": "filled", "fillcolor": "#fef3c7"},
    "generator": {"shape": "ellipse", "style": "filled", "fillcolor": "#dbeafe"},
}


def to_dot(m: ComponentsMap) -> str:
    """Serializa a DOT para st.graphviz_chart."""
    lines = ["digraph G {", '  rankdir=LR;', '  node [fontname="Helvetica"];']
    for n in m.nodes:
        style = KIND_STYLE.get(n.kind, {})
        attrs = ", ".join(f'{k}="{v}"' for k, v in style.items())
        lines.append(f'  "{n.id}" [label="{n.label}", {attrs}];')
    for e in m.edges:
        lines.append(f'  "{e.src}" -> "{e.dst}" [label="{e.relation}"];')
    lines.append("}")
    return "\n".join(lines)


def _default_map() -> ComponentsMap:
    """Mapa inicial poblado a partir de lo que ya existe en el repo."""
    nodes = [
        # Generadores IA
        Node("ai-anthropic", "Anthropic Claude", "generator", "claude-sonnet/haiku/opus"),
        Node("ai-openai", "OpenAI GPT", "generator", "gpt-4o, gpt-4.1, mini"),
        Node("ai-whisper", "OpenAI Whisper", "generator", "transcripción local"),
        Node("ai-elevenlabs", "ElevenLabs", "generator", "TTS de podcasts"),
        Node("ai-kling", "Kling", "generator", "generación de vídeo"),
        # Sistemas/pipelines
        Node("pipe-guion", "lanzar_produccion.py", "system", "PDF → guion .md (M/T/S)"),
        Node("pipe-episodio", "generar_episodio_v2.py", "system", "guion → audio MP3"),
        Node("pipe-validar", "validar_episodio.py", "system", "QA del guion (M/T/S)"),
        Node("pipe-escaleta", "generate_escaleta.py", "system", "guion → escaleta de escenas"),
        Node("pipe-video", "video_compositor.py", "system", "ensambla vídeo final"),
        Node("cockpit", "Cockpit Streamlit", "system", "centro de control"),
        # Generados
        Node("out-guion", "Guiones/*.txt", "generated", "salidas de pipe-guion"),
        Node("out-audio", "episodios/*.mp3", "generated", "podcasts terminados"),
        Node("out-escaleta", "escaletas/*.json", "generated", "guion estructurado por bloques"),
        Node("out-video", "Videos/*.mp4", "generated", "vídeo final del episodio"),
    ]
    edges = [
        Edge("pipe-guion", "ai-anthropic", "uses"),
        Edge("pipe-guion", "ai-openai", "uses"),
        Edge("pipe-guion", "out-guion", "produces"),
        Edge("pipe-escaleta", "ai-anthropic", "uses"),
        Edge("pipe-escaleta", "out-escaleta", "produces"),
        Edge("out-guion", "pipe-episodio", "feeds"),
        Edge("pipe-episodio", "ai-elevenlabs", "uses"),
        Edge("pipe-episodio", "out-audio", "produces"),
        Edge("out-audio", "pipe-validar", "feeds"),
        Edge("out-escaleta", "pipe-video", "feeds"),
        Edge("pipe-video", "ai-kling", "uses"),
        Edge("pipe-video", "out-video", "produces"),
        Edge("cockpit", "pipe-guion", "depends_on"),
        Edge("cockpit", "pipe-episodio", "depends_on"),
        Edge("cockpit", "pipe-validar", "depends_on"),
    ]
    return ComponentsMap(nodes=nodes, edges=edges)


def add_node(m: ComponentsMap, node: Node) -> ComponentsMap:
    if any(n.id == node.id for n in m.nodes):
        raise ValueError(f"Ya existe un nodo con id «{node.id}»")
    m.nodes.append(node)
    return m


def add_edge(m: ComponentsMap, edge: Edge) -> ComponentsMap:
    ids = {n.id for n in m.nodes}
    if edge.src not in ids:
        raise ValueError(f"src «{edge.src}» no existe")
    if edge.dst not in ids:
        raise ValueError(f"dst «{edge.dst}» no existe")
    m.edges.append(edge)
    return m


def remove_node(m: ComponentsMap, node_id: str) -> ComponentsMap:
    m.nodes = [n for n in m.nodes if n.id != node_id]
    m.edges = [e for e in m.edges if e.src != node_id and e.dst != node_id]
    return m
