"""Retry quirúrgico: pide al modelo modificar SOLO secciones / intervenciones
fallidas en lugar de regenerar el guion entero.

Estrategia: cuando hay 1-3 hard fails localizados (afectan a UN bloque o a
intervenciones concretas, no a la estructura global), pedimos a Haiku 4.5 un
patch JSON con las operaciones mínimas. Si Haiku falla, escalamos a Sonnet.

El patch se aplica sobre el TEXTO CRUDO (pre post-process) para que el
post-process posterior (num2words, SSML, trim fuentes) opere sobre el
resultado fusionado.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Literal

from generadores.shared import anthropic_client
from validators.result import ValidationResult

logger = logging.getLogger(__name__)

_HAIKU_MODEL = "claude-haiku-4-5-20251001"
_SONNET_MODEL = "claude-sonnet-4-5"

PatchOperation = Literal[
    "replace_section",
    "replace_intervention",
    "insert_after_intervention",
    "delete_intervention",
]


@dataclass
class Patch:
    section: str
    operation: PatchOperation
    new_content: str | None = None
    intervention_idx: int | None = None


def _build_patch_system_prompt() -> str:
    return (
        "Eres un editor de guiones del podcast MaquinarIA Pesada. Recibes un "
        "guion ya redactado y la lista de reglas HARD que no pasó. Tu tarea "
        "es devolver un JSON con la MÍNIMA cantidad de operaciones necesarias "
        "para corregir esas reglas, sin tocar nada que ya esté bien.\n\n"
        "Formato exacto del JSON que debes devolver (sin ``` ni explicaciones):\n"
        "{\n"
        '  "patches": [\n'
        "    {\n"
        '      "section": "BLOQUE_FUENTES",\n'
        '      "operation": "replace_section" | "replace_intervention" | '
        '"insert_after_intervention" | "delete_intervention",\n'
        '      "new_content": "IAGO: [tag] texto...\\nMARIA: [tag] texto...",\n'
        '      "intervention_idx": 0\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Reglas:\n"
        "- `replace_section`: sustituye todo el cuerpo de la sección (sin "
        "cabecera `# NOMBRE`). `new_content` requerido. No usar "
        "`intervention_idx`.\n"
        "- `replace_intervention`: sustituye UNA intervención dentro de la "
        "sección (0-based). Requiere `intervention_idx` y `new_content`.\n"
        "- `insert_after_intervention`: añade una intervención después de "
        "`intervention_idx`. Requiere ambas. Usa idx=-1 para insertar al "
        "principio.\n"
        "- `delete_intervention`: elimina la intervención `intervention_idx`. "
        "No requiere `new_content`.\n\n"
        "Mantén el FORMATO exacto: cada intervención empieza por `IAGO:` o "
        "`MARIA:` y va en UNA línea. Las cabeceras de sección las gestiona "
        "el sistema (no las incluyas en `new_content`)."
    )


def _format_failures_for_patch(results: list[ValidationResult]) -> str:
    blocking = [r for r in results if r.is_blocking]
    lines = ["Reglas HARD a corregir:"]
    for r in blocking:
        ctx = ""
        if hasattr(r, "context") and isinstance(r.context, dict):
            section = r.context.get("section")
            idx = r.context.get("intervention_idx")
            if section:
                ctx = f" [section={section}"
                if idx is not None:
                    ctx += f", intervention_idx={idx}"
                ctx += "]"
        lines.append(f"- {r.rule_name}{ctx}: {r.message}")
    return "\n".join(lines)


def _build_patch_user_prompt(script: str, results: list[ValidationResult],
                              context: str) -> str:
    return (
        f"## Contexto del episodio (extracto)\n{context}\n\n"
        f"## {_format_failures_for_patch(results)}\n\n"
        f"## Guion actual a editar\n```\n{script}\n```\n\n"
        "Devuelve SOLO el JSON con los patches mínimos. Nada más."
    )


_SECTION_HEADER_RE = re.compile(r"^#\s+([A-Z_]+)\s*$", re.MULTILINE)
_INTERVENTION_RE = re.compile(r"^(?:IAGO|MARIA):", re.MULTILINE)


def _split_sections(script: str) -> list[tuple[str, str]]:
    """Devuelve [(section_name, body), ...] preservando el orden.

    El body NO incluye la cabecera `# NOMBRE`. El primer elemento puede ser
    ("", preamble) si el guion tiene texto antes de la primera cabecera.
    """
    matches = list(_SECTION_HEADER_RE.finditer(script))
    if not matches:
        return [("", script)]
    result: list[tuple[str, str]] = []
    if matches[0].start() > 0:
        result.append(("", script[:matches[0].start()]))
    for i, m in enumerate(matches):
        name = m.group(1)
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(script)
        body = script[body_start:body_end]
        result.append((name, body))
    return result


def _join_sections(sections: list[tuple[str, str]]) -> str:
    out: list[str] = []
    for name, body in sections:
        if name:
            out.append(f"# {name}")
        body_stripped = body.strip("\n")
        if body_stripped:
            out.append(body_stripped)
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def _split_interventions(body: str) -> list[str]:
    """Trocea el cuerpo de una sección en intervenciones (líneas IAGO:/MARIA:).

    Cada intervención es UNA línea (formato canónico v6). Líneas vacías y
    líneas que no empiezan por IAGO:/MARIA: se descartan.
    """
    out: list[str] = []
    for line in body.splitlines():
        if _INTERVENTION_RE.match(line):
            out.append(line.rstrip())
    return out


def apply_patches(script: str, patches: list[Patch]) -> str:
    """Aplica una lista de patches al guion y devuelve el resultado."""
    sections = _split_sections(script)
    name_to_idx: dict[str, int] = {n: i for i, (n, _) in enumerate(sections) if n}

    for p in patches:
        if p.section not in name_to_idx:
            logger.warning("patch ignorado: sección %s no existe", p.section)
            continue
        idx = name_to_idx[p.section]
        name, body = sections[idx]

        if p.operation == "replace_section":
            if p.new_content is None:
                continue
            sections[idx] = (name, "\n" + p.new_content.strip() + "\n")
            continue

        interventions = _split_interventions(body)
        if p.operation == "replace_intervention":
            if p.intervention_idx is None or p.new_content is None:
                continue
            if 0 <= p.intervention_idx < len(interventions):
                interventions[p.intervention_idx] = p.new_content.strip()
        elif p.operation == "insert_after_intervention":
            if p.intervention_idx is None or p.new_content is None:
                continue
            ins_at = max(0, p.intervention_idx + 1)
            ins_at = min(ins_at, len(interventions))
            interventions.insert(ins_at, p.new_content.strip())
        elif p.operation == "delete_intervention":
            if p.intervention_idx is None:
                continue
            if 0 <= p.intervention_idx < len(interventions):
                del interventions[p.intervention_idx]

        new_body = "\n" + "\n".join(interventions) + "\n"
        sections[idx] = (name, new_body)

    return _join_sections(sections)


def _parse_patches(text: str) -> list[Patch]:
    """Parsea el JSON devuelto por el modelo a una lista de Patch."""
    t = text.strip()
    # Quita ``` fences si el modelo los añadió a pesar de las instrucciones.
    if t.startswith("```"):
        nl = t.find("\n")
        if nl != -1:
            t = t[nl + 1:]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    # Algunos modelos prefijan "json" o frases antes del objeto.
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1:
        return []
    try:
        data = json.loads(t[start:end + 1])
    except json.JSONDecodeError:
        return []
    raw_patches = data.get("patches", [])
    out: list[Patch] = []
    for rp in raw_patches:
        if not isinstance(rp, dict):
            continue
        section = rp.get("section")
        op = rp.get("operation")
        if not section or op not in (
            "replace_section", "replace_intervention",
            "insert_after_intervention", "delete_intervention",
        ):
            continue
        out.append(Patch(
            section=section,
            operation=op,
            new_content=rp.get("new_content"),
            intervention_idx=rp.get("intervention_idx"),
        ))
    return out


def request_patches(
    *,
    script: str,
    validation_results: list[ValidationResult],
    primary_model: str,
    user_prompt_context: str = "",
) -> tuple[list[Patch], anthropic_client.GenerationResult | None]:
    """Pide al modelo (Haiku con fallback a Sonnet) los patches mínimos.

    Devuelve `(patches, last_generation)` donde `last_generation` es el
    `GenerationResult` de la última llamada (para tracking de coste).
    """
    system = _build_patch_system_prompt()
    user = _build_patch_user_prompt(script, validation_results,
                                     user_prompt_context)

    # Haiku primero.
    gen = anthropic_client.generate(
        system=system,
        user=user,
        model=_HAIKU_MODEL,
        max_output_tokens=2000,
        temperature=0.2,
    )
    if gen.ok:
        patches = _parse_patches(gen.text)
        if patches:
            return patches, gen

    # Fallback a Sonnet solo si el modelo primario NO era ya Haiku.
    if "haiku" not in primary_model.lower():
        gen2 = anthropic_client.generate(
            system=system,
            user=user,
            model=_SONNET_MODEL,
            max_output_tokens=2000,
            temperature=0.2,
        )
        if gen2.ok:
            patches = _parse_patches(gen2.text)
            return patches, gen2
        return [], gen2
    return [], gen


def should_use_patch_retry(results: list[ValidationResult]) -> bool:
    """Heurística pública: ¿conviene patch retry vs full regen?

    - ≤3 hard fails
    - Ninguno estructural (orden, secciones faltantes/prohibidas)
    """
    hard = [r for r in results if r.is_blocking]
    if not hard or len(hard) > 3:
        return False
    structural = {
        "required_sections", "forbidden_sections", "section_order",
        "saludo_format",
    }
    return not any(r.rule_name in structural for r in hard)
