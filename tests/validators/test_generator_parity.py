"""Test de paridad generador ↔ validador.

Cada regla HARD del validador debe estar mencionada explícitamente en el
SYSTEM_PROMPT del generador correspondiente. Si una regla nueva entra al
validador pero no al prompt, el modelo no sabrá cumplirla y entrará en
retry-loop hasta agotar reintentos.

Este test mantiene esa sincronización: si añades una regla nueva en
validators/, también tienes que añadir su descripción en el SYSTEM_PROMPT
del generador correspondiente — el test te avisa si te olvidas de un
lado o del otro.

Ver `docs/architecture/EVALUACION_EDITORIAL.md` §"Sincronización" para
el contrato completo.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


def _system_prompt(module_path: str) -> str:
    """Carga el SYSTEM_PROMPT del módulo como string, normalizado a minúsculas."""
    path = ROOT / module_path
    text = path.read_text(encoding="utf-8")
    # Extraer entre triple-comilla tras SYSTEM_PROMPT = """\
    m = re.search(r'SYSTEM_PROMPT\s*=\s*"""\\?\n?(.*?)"""', text, re.DOTALL)
    if not m:
        return text.lower()
    return m.group(1).lower()


# Mapping: rule_name → (kinds aplicables, list[keywords que DEBEN aparecer
# en el SYSTEM_PROMPT del generador para que el modelo sepa cumplirla)
#
# Las keywords son OR — basta con que UNA aparezca. Eso permite redacciones
# distintas en cada prompt (p.ej. "stay tuned" en S como muletilla, en M
# como cliffhanger artificial).
RULE_PROMPT_PARITY: list[tuple[str, str, list[str]]] = [
    # ---- Reglas comunes a M/T/S ----
    ("blacklist_interjection", "MTS", [
        "exactamente", "claro que", "exacto",
    ]),
    ("blacklist_ai_bro", "MTS", [
        "mundo actual de la ia", "cabe mencionar", "preámbulos", "preambulos",
    ]),
    ("blacklist_coach", "MTS", [
        "excelente pregunta", "coach", "adelante con tu proyecto",
    ]),
    ("blacklist_cliffhanger", "MTS", [
        "stay tuned", "próximos episodios", "proximos episodios", "cliffhanger",
    ]),

    # ---- Reglas M y T (no S) ----
    ("glossary_term_first_use_expanded", "MT", [
        "aposición con comas", "aposicion con comas",
        "expansión castellana", "expansion castellana",
        "**es:**", "primer uso",
    ]),

    # ---- Reglas canónicas ----
    ("canonical_hook_closing", "MT", [
        "esto es maquinaria pesada. arrancamos",
    ]),
    ("canonical_concepts_opening", "MT", [
        "tres conceptos", "frase literal", "apertura canónica",
        "apertura canonica",
    ]),
    ("canonical_final_closing", "MT", [
        "y hasta aqui ha llegado", "frase canónica", "frase canonica",
    ]),
    ("canonical_s_closing", "S", [
        "maquinaria pesada", "cierre canónico", "cierre canonico",
    ]),

    # ---- Reglas estructurales M ----
    ("m_concepts_count", "M", ["cierre_conceptos", "3-5", "3 y 5"]),
    ("m_leader_panorama", "M", ["panorama", "yago"]),
    ("m_leader_aplicacion", "M", ["aplicacion_practica", "maria"]),
    ("m_fuentes_count", "M", ["bloque_fuentes", "fuentes"]),

    # ---- Reglas estructurales T ----
    ("t_concepts_count_exact_3", "T", [
        "3 conceptos", "tres conceptos",
        # El validador cuenta intervenciones (1 intervención = 1 concepto),
        # por eso el prompt usa "exactamente 3 intervenciones".
        "exactamente 3 intervenciones", "exactamente tres intervenciones",
    ]),
    ("t_leader_panorama", "T", ["panorama", "yago"]),
    ("t_leader_casos", "T", ["bloque_casos", "maria"]),
    ("t_leader_limites", "T", ["bloque_limites", "yago"]),
    ("t_casos_company_count", "T", ["empresas", "nombre propio"]),

    # ---- Reglas estructurales S ----
    ("s_no_dialogue", "S", ["sin diálogo", "sin dialogo", "una sola voz"]),
    ("s_hook_template", "S", ["hook", "h1", "h2", "h3"]),
    ("s_word_count", "S", ["157", "198", "180 palabras"]),
]


_GENERATOR_PATHS = {
    "M": "generadores/m_generator.py",
    "T": "generadores/t_generator.py",
    "S": "generadores/s_generator.py",
}


@pytest.mark.parametrize(
    "rule_name,kind,keywords",
    [
        (rule, kind, keywords)
        for rule, kinds, keywords in RULE_PROMPT_PARITY
        for kind in kinds
    ],
    ids=[
        f"{rule}/{kind}"
        for rule, kinds, _ in RULE_PROMPT_PARITY
        for kind in kinds
    ],
)
def test_rule_present_in_generator_prompt(
    rule_name: str, kind: str, keywords: list[str]
) -> None:
    """Cada regla HARD del validador tiene su explicación en el prompt del
    generador correspondiente — el modelo necesita saber qué se le exige."""
    prompt = _system_prompt(_GENERATOR_PATHS[kind])
    found = [kw for kw in keywords if kw.lower() in prompt]
    assert found, (
        f"La regla '{rule_name}' (kind={kind}) NO se menciona en "
        f"{_GENERATOR_PATHS[kind]}. Se buscaba alguna de las keywords: "
        f"{keywords}. Si la regla cambió o se renombró, actualiza el "
        f"SYSTEM_PROMPT del generador Y la lista RULE_PROMPT_PARITY de "
        f"este test (en el mismo PR). Ver "
        f"docs/architecture/EVALUACION_EDITORIAL.md §Sincronización."
    )


def test_all_listed_rules_exist_in_validators():
    """Sanity inverso: cada rule_name del listado debe existir como literal
    en validators/ (evita que el test cubra reglas obsoletas)."""
    validators_dir = ROOT / "validators"
    all_validator_text = ""
    for path in validators_dir.rglob("*.py"):
        all_validator_text += path.read_text(encoding="utf-8")
    missing = [
        rule for rule, _, _ in RULE_PROMPT_PARITY
        if f'"{rule}"' not in all_validator_text
    ]
    assert not missing, (
        f"Estas reglas del test de paridad no existen en validators/: "
        f"{missing}. O actualiza RULE_PROMPT_PARITY o reintroduce las "
        f"reglas en su validator correspondiente."
    )
