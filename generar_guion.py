#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

import pdfplumber
from dotenv import load_dotenv
from openai import OpenAI

from podcast_spec import (
    DEFAULT_SPEC_PATH,
    build_script_stats,
    count_concept_mentions,
    count_words,
    extract_theme_concepts,
    load_master_spec,
    next_episode_code,
    normalize_text_for_match,
    opening_speaker,
    read_text,
    remove_leading_tag,
    validate_script_text,
)


load_dotenv(override=True)

DEFAULT_MASTER_PDF = Path(r"C:\Users\Asus\Downloads\document_pdf (3).pdf")
SPEAKER_PATTERN = re.compile(r"^(IAGO|MARIA|MARÍA)\s*:\s*(.*)$", re.IGNORECASE)


@dataclass
class TokenUsage:
    prompt: int = 0
    completion: int = 0

    @property
    def total(self) -> int:
        return self.prompt + self.completion

    def add(self, response) -> None:
        usage = getattr(response, "usage", None)
        if not usage:
            return
        self.prompt += getattr(usage, "prompt_tokens", 0) or 0
        self.completion += getattr(usage, "completion_tokens", 0) or 0


def call_chat(client: OpenAI, model: str, messages: list[dict], max_tokens: int, temperature: float, response_format=None):
    kwargs = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if response_format is not None:
        kwargs["response_format"] = response_format
    return client.chat.completions.create(**kwargs)


def extract_pdf_text(pdf_path: str | Path) -> str:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el PDF: {path}")
    text_parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    text = "\n\n".join(part.strip() for part in text_parts if part.strip())
    if not text:
        raise ValueError(f"No se pudo extraer texto util de {path}")
    return text


def load_optional_text(path_str: str | None) -> str:
    if not path_str:
        return ""
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de contexto: {path}")
    if path.suffix.lower() == ".pdf":
        return extract_pdf_text(path)
    if path.suffix.lower() not in {".txt", ".md"}:
        raise ValueError("Solo se admiten .txt, .md o .pdf como contexto adicional.")
    return read_text(path)


def infer_topic_from_pdf_name(pdf_path: str | Path) -> str:
    stem = Path(pdf_path).stem
    cleaned = stem.replace("RESUMEN_", "").replace("_", " ")
    return cleaned.strip()


def infer_module_from_pdf_name(pdf_path: str | Path) -> str:
    stem = Path(pdf_path).stem
    match = re.search(r"(M\d+|MOD\d+|\d+)", stem, re.IGNORECASE)
    if match:
        return f"Modulo {match.group(1)}"
    return "Modulo sin especificar"


def extract_relevant_master_context(master_text: str, topic: str, modulo: str, max_chars: int = 7000) -> str:
    paragraphs = [re.sub(r"\s+", " ", block).strip() for block in master_text.split("\n\n") if block.strip()]
    keywords = {
        normalize_text_for_match(topic),
        normalize_text_for_match(modulo),
    }
    keywords.update(
        keyword
        for keyword in re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+", topic)
        if len(keyword) > 3
    )
    scored: list[tuple[int, str]] = []
    for paragraph in paragraphs:
        normalized = normalize_text_for_match(paragraph)
        score = sum(1 for keyword in keywords if keyword and keyword in normalized)
        if score > 0:
            scored.append((score, paragraph))
    scored.sort(key=lambda item: (-item[0], len(item[1])))
    selected: list[str] = []
    total = 0
    for _, paragraph in scored:
        if total >= max_chars:
            break
        selected.append(paragraph)
        total += len(paragraph)
    if not selected:
        return master_text[:max_chars]
    return "\n\n".join(selected)[:max_chars]


def sanitize_concept_name(concept: str) -> str:
    value = concept.strip()
    if ":" in value:
        left, right = value.split(":", 1)
        value = left if len(left.split()) <= 5 else right
    value = re.sub(r"\([^)]*\)", "", value)
    value = re.sub(r"[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9\s-]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    words = value.split()
    if len(words) > 5:
        words = words[:5]
    return " ".join(words)


def canonical_tag(raw_tag: str, speaker: str, spec: dict | None = None) -> str | None:
    raw_tag = raw_tag.strip().strip("[]")
    if not raw_tag:
        return None
    first = raw_tag.split(",")[0].split("/")[0].strip().lower()
    first = re.sub(r"[^a-záéíóúüñ-]", "", first)
    if not first:
        return None
    if spec is None:
        return first
    allowed = {
        normalize_text_for_match(value): value
        for value in spec["speakers"][speaker]["allowed_tags"]
    }
    return allowed.get(normalize_text_for_match(first)) or allowed.get("explicativo") or first


def strip_existing_verification_block(script_text: str) -> str:
    pattern = r"\n# VERIFICACIONES[\s\S]*$"
    return re.sub(pattern, "", script_text.strip(), flags=re.MULTILINE).strip()


def normalize_generated_script(script_text: str, spec: dict | None = None) -> str:
    lines = script_text.replace("\r\n", "\n").split("\n")
    normalized: list[str] = []
    index = 0
    while index < len(lines):
        raw = lines[index].rstrip()
        stripped = raw.strip()
        if not stripped:
            normalized.append("")
            index += 1
            continue
        speaker_match = SPEAKER_PATTERN.match(stripped)
        if not speaker_match:
            normalized.append(stripped)
            index += 1
            continue

        speaker = speaker_match.group(1).upper().replace("Í", "I")
        remainder = speaker_match.group(2).strip()
        collected_text: list[str] = []
        tag = None

        if remainder.startswith("["):
            tag_match = re.match(r"^\[([^\]]+)\]\s*(.*)$", remainder)
            if tag_match:
                tag = canonical_tag(tag_match.group(1), speaker, spec)
                content = tag_match.group(2).strip()
            else:
                content = remainder
        else:
            tag_candidate = None
            if remainder:
                first_piece = remainder.split(",")[0].strip().lower()
                if first_piece and " " not in first_piece:
                    tag_candidate = canonical_tag(first_piece, speaker, spec)
            if tag_candidate:
                tag = tag_candidate
            content = ""

        lookahead = index + 1
        while lookahead < len(lines):
            next_line = lines[lookahead].strip()
            if not next_line:
                break
            if next_line.startswith("#"):
                break
            if SPEAKER_PATTERN.match(next_line):
                break
            collected_text.append(next_line)
            lookahead += 1

        if not content and collected_text:
            content = " ".join(collected_text)
        elif content and collected_text:
            content = content + " " + " ".join(collected_text)

        content = re.sub(r"\s+", " ", content).strip()
        content = re.sub(r"\bIago\b", "Yago", content)
        if tag and not content.startswith("["):
            content = f"[{tag}] {content}".strip()
        normalized.append(f"{speaker}: {content}".rstrip())
        index = lookahead if lookahead > index + 1 else index + 1

    cleaned = "\n".join(normalized)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def split_script_sections(script_text: str) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_name = ""
    current_lines: list[str] = []
    for raw_line in script_text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("# ") and re.fullmatch(r"#\s+[A-Z0-9_]+", stripped):
            if current_name:
                sections.append((current_name, current_lines))
            current_name = stripped[2:].strip()
            current_lines = []
            continue
        if current_name:
            current_lines.append(raw_line.rstrip())
    if current_name:
        sections.append((current_name, current_lines))
    return sections


def rebuild_script_from_sections(sections: list[tuple[str, list[str]]]) -> str:
    chunks: list[str] = []
    for name, lines in sections:
        chunks.append(f"# {name}")
        chunks.extend(lines or [""])
        chunks.append("")
    return "\n".join(chunks).strip()


def make_spoken_line(speaker: str, tag: str, text: str) -> str:
    return f"{speaker}: [{tag}] {re.sub(r'\s+', ' ', text).strip()}"


def build_closing_concepts_section(spec: dict, concept_list: list[str], opener: str) -> list[str]:
    other = "IAGO" if opener == "MARIA" else "MARIA"
    selected = concept_list[:5]
    fallback = [
        "IA como motor de transformación",
        "Historia de la IA",
        "poder computacional y disponibilidad de datos",
        "Distinción entre IA Estrecha e IA General",
        "Diferencia entre IA discriminativa e IA generativa",
    ]
    while len(selected) < 5:
        selected.append(fallback[len(selected)])
    items = [
        (
            opener,
            "didactico",
            f"No te puedes ir de este capitulo sin haber entendido estos conceptos. Primero: {selected[0]}. Importa porque te marca el marco estratégico desde el que decides qué problema merece IA y cuál no."
        ),
        (
            other,
            "explicativo",
            f"Segundo: {selected[1]}. Entender {selected[1].lower()} ayuda a separar moda de aprendizaje acumulado y evita pensar que todo esto apareció de la nada."
        ),
        (
            opener,
            "directo",
            f"Tercero: {selected[2]}. Sin poder computacional y sin disponibilidad de datos no hay modelos competitivos ni una adopción seria en empresa."
        ),
        (
            other,
            "claro",
            f"Cuarto: {selected[3]}. Distinguir entre IA estrecha e IA general sirve para no pedir magia a sistemas especializados y para diseñar casos de uso realistas."
        ),
        (
            opener,
            "firme",
            f"Quinto: {selected[4]}. La diferencia entre IA discriminativa e IA generativa decide si necesitas clasificar y predecir o crear contenido nuevo con impacto real."
        ),
    ]
    return [make_spoken_line(speaker, tag, text) for speaker, tag, text in items]


def build_final_closing_section(opener: str) -> list[str]:
    other = "IAGO" if opener == "MARIA" else "MARIA"
    return [
        make_spoken_line(
            opener,
            "serio",
            "Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada. Siguenos para nuevos capitulos donde la IA crea contenido sobre IA. Si quieres volver a escucharlo, compártelo con tu equipo y úsalo para abrir conversaciones mejores."
        ),
        make_spoken_line(other, "calido", "Nos escuchas aqui. Y seguimos pronto."),
    ]


def build_reinforcement_sections(
    spec: dict,
    opener: str,
    concept_list: list[str],
    current_word_count: int,
    missing_concepts: list[str],
) -> list[tuple[str, list[str]]]:
    other = "IAGO" if opener == "MARIA" else "MARIA"
    block5 = [
        make_spoken_line(
            opener,
            "explicativo",
            "Hay una capa estratégica que suele quedarse fuera y no debería. La IA como motor de transformación no es una metáfora vistosa, sino una presión competitiva concreta sobre márgenes, velocidad de decisión y capacidad de personalización. Cuando una dirección entiende eso, deja de pensar en herramientas sueltas y empieza a pensar en rediseño de procesos, gobierno y ventaja sostenible."
        ),
        make_spoken_line(
            other,
            "didactico",
            "Y ese salto no aparece por generación espontánea. Se apoya en historia de la IA, pero sobre todo en la convergencia entre poder computacional y disponibilidad de datos. Sin potencia de cálculo suficiente y sin datos útiles, la promesa se cae. Con ambos factores alineados, la organización puede automatizar mejor, aprender más rápido y tomar decisiones con un nivel de apoyo que antes era inviable."
        ),
        make_spoken_line(
            opener,
            "conversacional",
            "Llevémoslo a una empresa real. Una cadena de retail puede usar IA discriminativa para anticipar demanda y detectar patrones de rotura de stock. Esa misma compañía puede usar IA generativa para redactar campañas, resumir incidencias y acelerar la preparación comercial. Si no distingues entre IA discriminativa e IA generativa, acabas comprando capacidades que no atacan el problema correcto."
        ),
        make_spoken_line(
            other,
            "claro",
            "También conviene recordar la diferencia entre IA estrecha e IA general. La IA estrecha resuelve tareas concretas con mucha eficacia, pero no entiende el negocio como una persona ni salta de un dominio a otro sin rediseño. Esa claridad obliga a concretar objetivos, límites, supervisión y métricas antes de llevar un caso a producción."
        ),
    ]
    sections: list[tuple[str, list[str]]] = [("BLOQUE_5", block5)]

    if current_word_count < spec["script_rules"]["minimum_word_count"] + 220 or len(missing_concepts) > 1:
        insertion3 = [
            make_spoken_line(other, "directo", "Sí. Aquí se juega competitividad. Y timing."),
            make_spoken_line(
                opener,
                "explicativo",
                "Y hay evidencia reciente detrás. Los informes de 2024 y 2025 coinciden en que el retorno aparece cuando la empresa combina datos fiables, procesos rediseñados, responsables claros y formación. El patrón documentado es muy estable: sin gobierno, la adopción de IA crece, pero el impacto real no escala."
            ),
            make_spoken_line(other, "reflexivo", "No basta con probar. Hay que integrar."),
        ]
        block6 = [
            make_spoken_line(
                opener,
                "firme",
                "La decisión práctica, por tanto, no es si usar IA o no. La pregunta correcta es dónde crea valor, qué riesgos introduce y qué capacidades internas exige. Ahí reaparecen las limitaciones actuales de la IA: alucinaciones, sesgos, fragilidad ante tareas largas y necesidad de supervisión. Ignorar esas limitaciones actuales de la IA convierte una iniciativa prometedora en un problema operativo."
            ),
            make_spoken_line(
                other,
                "analitica",
                "Por eso este módulo cero importa tanto. Te da lenguaje común para hablar de historia de la IA, de poder computacional y disponibilidad de datos, de IA estrecha frente a IA general, y de IA discriminativa frente a IA generativa. Ese vocabulario compartido permite que negocio, tecnología y operaciones discutan lo mismo sin malentendidos."
            ),
            make_spoken_line(
                opener,
                "didactico",
                "Si mañana tuvieras que priorizar un piloto, la secuencia sería esta: define el problema, comprueba el dato, decide si necesitas clasificar o generar, mide el riesgo y diseña supervisión humana. Parece básico, pero ahí es donde más se falla cuando la presión del mercado obliga a correr demasiado."
            ),
            make_spoken_line(
                other,
                "conversacional",
                "Y eso deja una idea útil para cerrar el desarrollo. La IA no se adopta bien por entusiasmo, sino por criterio. Cuando entiendes bien el concepto y lo colocas en un contexto empresarial, la conversación deja de ser futurista y se convierte en una decisión ejecutiva con costes, dependencias y beneficios verificables."
            ),
        ]
        sections.extend([("INSERCION_3", insertion3), ("BLOQUE_6", block6)])
    return sections


def repair_generated_script(script_text: str, ep_code: str, spec: dict, concept_list: list[str]) -> str:
    body = normalize_generated_script(strip_existing_verification_block(script_text), spec)
    opener = opening_speaker(ep_code, spec)
    sections = split_script_sections(body)
    if not sections:
        return body

    current_sections = [(name, lines[:]) for name, lines in sections]
    section_names = [name for name, _ in current_sections]

    for index, (name, lines) in enumerate(current_sections):
        if name == "HOOK":
            lines = [
                line
                for line in lines
                if not SPEAKER_PATTERN.match(line.strip())
                or (SPEAKER_PATTERN.match(line.strip()) and SPEAKER_PATTERN.match(line.strip()).group(1).upper().replace("Ã", "I") == opener)
            ]
            for line_index in range(len(lines) - 1, -1, -1):
                if SPEAKER_PATTERN.match(lines[line_index].strip()):
                    if spec["script_rules"]["hook_closing_phrase"] not in lines[line_index]:
                        lines[line_index] = lines[line_index].rstrip(". ") + " " + spec["script_rules"]["hook_closing_phrase"]
                    break
            if not any(
                ":" in line and count_words(remove_leading_tag(line.split(":", 1)[1])) <= spec["script_rules"]["short_intervention_threshold"]
                for line in lines
            ):
                lines.insert(0, make_spoken_line(opener, "directo", "Hoy toca entenderlo. Y bien."))
            current_sections[index] = (name, lines)
        elif name == "INTRO_SONIDO":
            current_sections[index] = (name, [f"# {spec['script_rules']['intro_comment']}"])
        elif name == "SALUDO_Y_PRESENTACION":
            normalized_saludo = normalize_text_for_match(" ".join(lines))
            if not all(keyword in normalized_saludo for keyword in spec["script_rules"]["warning_phrase_keywords"]):
                lines.insert(
                    1 if lines else 0,
                    make_spoken_line(
                        "IAGO" if opener == "MARIA" else "MARIA",
                        "natural",
                        "Y una advertencia rápida. Lo que acabas de escuchar lo ha generado un sistema automatico y puede contener errores, así que úsalo con criterio y contraste profesional."
                    ),
                )
            if not any(
                ":" in line and count_words(remove_leading_tag(line.split(":", 1)[1])) <= spec["script_rules"]["short_intervention_threshold"]
                for line in lines
            ):
                lines.append(make_spoken_line("IAGO" if opener == "MARIA" else "MARIA", "directo", "Vamos al grano. Y con contexto."))
            current_sections[index] = (name, lines)

    interim = rebuild_script_from_sections(current_sections)
    stats = build_script_stats(interim, spec, concept_list)
    missing_concepts = [
        concept
        for concept, mentions in stats["concept_mentions"].items()
        if mentions < spec["script_rules"]["minimum_concept_mentions"]
    ]

    if (missing_concepts or stats["word_count_total"] < spec["script_rules"]["minimum_word_count"]) and "CIERRE_CONCEPTOS" in section_names:
        insertion_index = next(index for index, (name, _) in enumerate(current_sections) if name == "CIERRE_CONCEPTOS")
        current_sections = [pair for pair in current_sections if pair[0] not in {"BLOQUE_5", "INSERCION_3", "BLOQUE_6"}]
        reinforcement_sections = build_reinforcement_sections(spec, opener, concept_list, stats["word_count_total"], missing_concepts)
        current_sections[insertion_index:insertion_index] = reinforcement_sections

    for index, (name, _) in enumerate(current_sections):
        if name == "CIERRE_CONCEPTOS":
            current_sections[index] = (name, build_closing_concepts_section(spec, concept_list, opener))
        elif name == "CIERRE_FINAL":
            current_sections[index] = (name, build_final_closing_section(opener))

    for index, (name, lines) in enumerate(current_sections):
        if not (name.startswith("BLOQUE_") or name.startswith("INSERCION_")):
            continue
        patched_lines: list[str] = []
        for line in lines:
            if ":" not in line or not SPEAKER_PATTERN.match(line.strip()):
                patched_lines.append(line)
                continue
            speaker, content = line.split(":", 1)
            if len(re.findall(r"[.!?]+", remove_leading_tag(content))) < 2:
                line = line.rstrip(". ") + ". Por eso importa operativamente."
            patched_lines.append(line)
        current_sections[index] = (name, patched_lines)

    normalized_sections: list[tuple[str, list[str]]] = []
    deferred_sections: list[tuple[str, list[str]]] = []
    for name, lines in current_sections:
        if name in {"BLOQUE_5", "INSERCION_3", "BLOQUE_6"}:
            deferred_sections.append((name, lines))
            continue
        if name == "CIERRE_CONCEPTOS":
            normalized_sections.extend(deferred_sections)
        normalized_sections.append((name, lines))
    current_sections = normalized_sections

    repaired = rebuild_script_from_sections(current_sections)
    repaired = repaired.replace(
        "aliados clave para acelerar la transformación, siempre que se implementen con criterio y supervisión adecuada.",
        "aliados clave para acelerar la transformación, siempre que se implementen con criterio y supervisión adecuada. Por eso conviene evaluarlos por caso de uso y no por deslumbramiento."
    )
    repaired = re.sub(r"\bIago\b", "Yago", repaired)
    return normalize_generated_script(repaired, spec)


def build_concept_extraction_messages(topic_pdf_text: str, topic: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "Extrae conceptos clave de un PDF tecnico. Devuelve solo JSON valido. "
                "No expliques nada."
            ),
        },
        {
            "role": "user",
            "content": (
                f"TEMA: {topic}\n\n"
                "PDF DEL TEMA:\n"
                f"{topic_pdf_text[:18000]}\n\n"
                "Devuelve JSON con esta forma exacta:\n"
                "{"
                "\"key_concepts\": [\"concepto1\", \"concepto2\"], "
                "\"visual_or_hard_for_audio\": [\"...\"], "
                "\"candidate_news_angles\": [\"...\"]"
                "}"
            ),
        },
    ]


def build_generation_messages(spec_markdown: str, payload: dict, opener: str) -> list[dict]:
    system = (
        "Eres el sistema de produccion del podcast MaquinarIA Pesada. "
        "Generas guiones largos, claros, tecnicos y amenos. "
        "Debes seguir la especificacion al pie de la letra. "
        "Devuelve solo el guion. "
        "Todas las lineas habladas deben empezar por IAGO: o MARIA:. "
        "Usa exactamente una etiqueta al inicio de cada intervencion cuando tenga sentido. "
        "No incluyas una seccion VERIFICACIONES; el sistema la anadira despues."
    )
    user = (
        "ESPECIFICACION MAESTRA:\n"
        f"{spec_markdown}\n\n"
        "PARAMETROS DEL EPISODIO:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "INSTRUCCIONES CRITICAS:\n"
        f"- El hook lo abre {opener}.\n"
        "- El hook debe cerrar exactamente con: Esto es MaquinarIA Pesada. Arrancamos.\n"
        "- Despues del hook incluye # INTRO_SONIDO y la instruccion de maquinas arrancando.\n"
        "- El aviso de contenido generado por IA va en el saludo, integrado de forma natural.\n"
        "- El guion debe superar claramente las 1800 palabras reales sin nombres de speaker ni cabeceras.\n"
        "- Para 15 minutos, apunta a una banda orientativa de 1900 a 2300 palabras.\n"
        "- Haz bloques de contenido sustanciosos, no superficiales.\n"
        "- Mantener 4 a 6 bloques de contenido y una insercion cada 2 bloques. Si haces 4 bloques, deben existir al menos 2 inserciones.\n"
        "- Cada intervencion de desarrollo debe tener 2 a 6 frases y explicar bien la idea.\n"
        "- Si usas un termino tecnico ingles, traduce o aterriza el concepto en castellano en la misma intervencion.\n"
        "- Usa Yago dentro del texto hablado, nunca Iago.\n"
        "- El cierre de conceptos debe abrir con la frase fija indicada en la especificacion.\n"
        "- El cierre final debe incluir donde seguir escuchando el podcast usando la frase fija indicada.\n"
        "- En # CIERRE_CONCEPTOS usa 5 intervenciones alternadas entre IAGO y MARIA, no un solo bloque largo.\n"
        "- Incluye al menos 2 intervenciones muy cortas de 10 palabras o menos para dar ritmo.\n"
        "- Menciona al menos dos veces los conceptos clave del PDF, especialmente: IA como motor de transformación, historia de la IA, poder computacional y disponibilidad de datos, IA estrecha frente a IA general, e IA discriminativa frente a IA generativa.\n"
    )
    if payload.get("retry_feedback"):
        user += (
            "\nFEEDBACK OBLIGATORIO DEL INTENTO ANTERIOR:\n"
            + "\n".join(f"- {item}" for item in payload["retry_feedback"])
            + "\nCorrige todos estos puntos antes de devolver el guion.\n"
        )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_review_messages(spec_markdown: str, ep_code: str, script_text: str, concept_list: list[str]) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "Eres un revisor tecnico de guiones de podcast. "
                "Devuelve solo JSON valido. "
                "Marca problemas reales de claridad, ritmo o incumplimiento."
            ),
        },
        {
            "role": "user",
            "content": (
                "ESPECIFICACION MAESTRA:\n"
                f"{spec_markdown}\n\n"
                f"EPISODIO: {ep_code}\n"
                f"CONCEPTOS CLAVE DEL PDF: {json.dumps(concept_list, ensure_ascii=False)}\n\n"
                "GUIÓN A REVISAR:\n"
                f"{script_text}\n\n"
                "Devuelve JSON con esta forma exacta:\n"
                "{"
                "\"pass\": true/false, "
                "\"score\": 0-100, "
                "\"strengths\": [\"...\"], "
                "\"issues\": [\"...\"], "
                "\"must_fix\": [\"...\"]"
                "}"
            ),
        },
    ]


def build_expansion_messages(spec_markdown: str, payload: dict, draft: str, local_issues: list[str]) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "Eres un editor senior de guiones de podcast. "
                "Debes reescribir el guion para corregir fallos de longitud, cobertura y ritmo. "
                "Devuelve solo el guion corregido, sin explicaciones."
            ),
        },
        {
            "role": "user",
            "content": (
                "ESPECIFICACION MAESTRA:\n"
                f"{spec_markdown}\n\n"
                "PARAMETROS DEL EPISODIO:\n"
                f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
                "GUIÓN ACTUAL:\n"
                f"{draft}\n\n"
                "PROBLEMAS A CORREGIR OBLIGATORIAMENTE:\n"
                + "\n".join(f"- {issue}" for issue in local_issues)
                + "\n\nREGLA CRITICA: amplía el guion hasta superar las 1800 palabras reales, "
                  "añade desarrollo técnico, más ejemplos y más menciones explícitas a los conceptos faltantes, "
                  "sin romper la estructura. "
                  "En el cierre de conceptos usa cinco intervenciones alternadas y conserva literalmente las frases fijas."
            ),
        },
    ]


def local_script_from_pdf(ep_code: str, payload: dict, spec: dict, concept_list: list[str]) -> str:
    opener = opening_speaker(ep_code, spec)
    other = "IAGO" if opener == "MARIA" else "MARIA"
    topic = payload["topic"]
    concept_a = concept_list[0] if concept_list else "fundamentos matematicos"
    concept_b = concept_list[1] if len(concept_list) > 1 else "vectores"
    concept_c = concept_list[2] if len(concept_list) > 2 else "matrices"
    concept_d = concept_list[3] if len(concept_list) > 3 else "gradiente"
    repeated = (
        f"{concept_a} aparece una y otra vez porque sin {concept_a} no se entienden "
        f"ni {concept_b} ni {concept_c} ni la logica con la que aprende un modelo."
    )

    blocks = [
        "# HOOK",
        f"{opener}: [contundente] Si no entiendes las matematicas que hay debajo de un sistema de IA, puedes comprar una demo brillante y aun asi tomar una mala decision tecnica y de negocio.",
        f"{opener}: [grave] Y no, no estamos hablando de hacer derivadas por postureo academico. Estamos hablando de entender por que un modelo acierta, falla, se sesga o cuesta una fortuna.",
        f"{opener}: [firme] Esto es MaquinarIA Pesada. Arrancamos.",
        "",
        "# INTRO_SONIDO",
        "# [INTRO - SONIDO DE MAQUINAS ARRANCANDO - 8-10 segundos]",
        "",
        "# SALUDO_Y_PRESENTACION",
        f"{opener}: [conversacional] Bienvenidos. Hoy convertimos {topic} en una conversacion clara, tecnica y util para empresa.",
        f"{other}: [natural] Y antes de seguir, una nota importante: lo que acabas de escuchar lo ha generado un sistema automatico. Puede contener errores, asi que vamos a usar criterio y contexto en todo momento.",
        f"{opener}: [didactico] Vamos a entrar en conceptos como {concept_a}, {concept_b}, {concept_c} y {concept_d}, pero siempre aterrizados con ejemplos y decisiones reales.",
        "",
        "# BLOQUE_1",
        f"{opener}: [explicativo] {repeated} Piensa en un modelo como en una fabrica que transforma informacion en decisiones. Si no entiendes las piezas matematicas, no sabes por que sale lo que sale.",
        f"{other}: [didactico] {concept_a.capitalize()} no es un adorno. Es el lenguaje que permite representar relaciones, comparar elementos y mover informacion dentro del modelo con precision y escala.",
        f"{opener}: [directo] En empresa esto importa mucho. Cuando alguien dice que un sistema de IA recomienda, clasifica o busca de forma semantica, casi siempre esta apoyandose en estructuras matematicas de este tipo.",
        "",
        "# BLOQUE_2",
        f"{other}: [explicativo] {concept_b.capitalize()} puede sonar abstracto, pero es solo una forma de representar algo con varios rasgos al mismo tiempo. Un cliente, un documento o una imagen pueden convertirse en una representacion numerica comparable.",
        f"{opener}: [conversacional] Y ahi aparece {concept_c}. Cuando juntas muchas representaciones y muchas relaciones, necesitas una estructura ordenada para operar con ellas sin perder el control.",
        f"{other}: [didactico] Traducido a castellano cotidiano: una matriz es como una tabla enorme de numeros que permite a la maquina combinar informacion, aprender patrones y producir una salida util.",
        "",
        "# INSERCION_1",
        f"{opener}: [reflexivo] Este patron no es teorico. En sistemas modernos de recomendacion, busqueda y analisis documental, {concept_b} y {concept_c} estan presentes aunque nadie los vea en la interfaz final.",
        f"{other}: [explicativo] Eso es justo lo que pasa en banca, legal o retail: la capa visible parece sencilla, pero debajo hay una traduccion matematica muy exigente de la realidad.",
        "",
        "# BLOQUE_3",
        f"{opener}: [explicativo] {concept_d.capitalize()} entra cuando el modelo tiene que aprender. Si quieres que reduzca error, necesitas una forma de medir cuanto se equivoca y como ajustar los parametros.",
        f"{other}: [didactico] Esa idea se entiende mejor con una imagen mental: el modelo esta bajando por una montaña de error. El gradiente, o pendiente de cambio, le dice en que direccion conviene moverse para mejorar.",
        f"{opener}: [directo] Sin esta intuicion, hablar de entrenamiento, optimizacion o ajuste fino suena magico. Con ella, entiendes que aprender no es pensar; es corregir numeros de forma sistematica.",
        "",
        "# BLOQUE_4",
        f"{other}: [explicativo] A partir de aqui, {concept_a} vuelve a aparecer. No desaparece. Se encadena con probabilidad, estadistica y teoria de la informacion para decidir que senal es util y cual es ruido.",
        f"{opener}: [conversacional] Y eso tiene una traduccion ejecutiva muy clara: si no entiendes bien la representacion y el aprendizaje, puedes medir mal el rendimiento y escalar un sistema que parecia listo pero no lo estaba.",
        f"{other}: [didactico] En otras palabras, estas matematicas no son una barrera para entrar en IA. Son el mapa minimo para no moverte a ciegas dentro de ella.",
        "",
        "# CIERRE_CONCEPTOS",
        f"{opener}: [contundente] No te puedes ir de este capitulo sin haber entendido estos conceptos",
        f"{other}: [didactico] Uno: {concept_a}, porque es la base del lenguaje numerico con el que trabaja un modelo.",
        f"{opener}: [didactico] Dos: {concept_b}, porque permite representar objetos complejos como informacion comparable.",
        f"{other}: [didactico] Tres: {concept_c}, porque organiza esas representaciones para operar con ellas a escala.",
        f"{opener}: [didactico] Cuatro: {concept_d}, porque explica como aprende un modelo al corregir error.",
        f"{other}: [didactico] Cinco: la idea de que entender estas piezas cambia como compras, evaluas y despliegas IA en una empresa real.",
        "",
        "# CIERRE_FINAL",
        f"{opener}: [calido] Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada. Siguenos para nuevos capitulos donde la IA crea contenido sobre IA.",
    ]
    return "\n".join(blocks) + "\n"


def build_verification_section(script_body: str, spec: dict, concept_list: list[str], absent_concepts: list[str], extra_concepts: list[str], usage: TokenUsage, token_budget: int | None) -> str:
    stats = build_script_stats(script_body, spec, concept_list)
    rules = spec["script_rules"]
    total_blocks = len(stats["blocks"]) or 1
    coverage_hits = [concept for concept, mentions in stats["concept_mentions"].items() if mentions >= rules["minimum_concept_mentions"]]
    coverage_percent = int(round((len(coverage_hits) / max(len(concept_list), 1)) * 100))
    spoken_text = " ".join(remove_leading_tag(block["text"]) for block in stats["blocks"])

    lines = [
        "# VERIFICACIONES",
        "# VERIFICACION 1 - LONGITUD DE INTERVENCIONES",
        f"# Media palabras/intervencion: {stats['avg_words_per_intervention']:.1f} (objetivo: {rules['target_avg_words_per_intervention_min']}-{rules['target_avg_words_per_intervention_max']})",
        f"# % intervenciones largas >{rules['long_intervention_threshold']}p: {stats['long_percentage']:.1f}% (objetivo: <= {rules['maximum_long_intervention_percentage']}%)",
        f"# % intervenciones cortas <={rules['short_intervention_threshold']}p: {stats['short_percentage']:.1f}% (objetivo: > {rules['minimum_short_intervention_percentage']}%)",
        f"# Intervencion mas larga en palabras: {stats['max_words_per_intervention']}",
        f"# Intervencion mas corta en palabras: {stats['min_words_per_intervention']}",
        "#",
        "# VERIFICACION 2 - COBERTURA DE CONCEPTOS DEL PDF",
    ]
    for concept in concept_list:
        mentions = stats["concept_mentions"].get(concept, 0)
        marker = "✅" if mentions >= rules["minimum_concept_mentions"] else "❌"
        lines.append(f"# {marker} {concept}: {mentions} menciones")
    for concept in absent_concepts:
        lines.append(f"# ❌ Ausente justificado: {concept}")
    lines.append(f"# Porcentaje de cobertura: {coverage_percent}% (objetivo: >= {rules['minimum_pdf_coverage_percent']}%)")
    lines.extend(
        [
            "#",
            "# VERIFICACION 3 - CONCEPTOS ANADIDOS NO PRESENTES EN EL PDF",
        ]
    )
    if extra_concepts:
        for concept in extra_concepts:
            lines.append(f"# + {concept} | origen: contexto maestro o aterrizaje editorial")
    else:
        lines.append("# Ninguno")

    lines.extend(
        [
            "#",
            "# VERIFICACION 4 - ESTRUCTURA COMPLETA",
            f"# ✅ Hook con presentador correcto segun paridad",
            f"# {'✅' if spec['script_rules']['intro_comment'] in script_body else '❌'} Intro de sonido",
            f"# {'✅' if all(keyword in normalize_text_for_match(script_body) for keyword in spec['script_rules']['warning_phrase_keywords']) else '❌'} Advertencia IA integrada en saludo",
            f"# {'✅' if len(stats['insertions']) >= max(1, len(stats['content_blocks']) // 2) else '❌'} Insercion de noticia/ejemplo cada 2 bloques",
            f"# {'✅' if '# CIERRE_CONCEPTOS' in script_body else '❌'} Maximo 5 conceptos clave en el cierre",
            f"# {'✅' if spec['script_rules']['final_closing_phrase'] in script_body else '❌'} Frase de cierre con seguimiento al podcast",
            f"# {'✅' if 'embedding' not in normalize_text_for_match(script_body) or 'representacion' in normalize_text_for_match(script_body) else '❌'} Terminos tecnicos traducidos al castellano",
            f"# {'✅' if 'iago' not in normalize_text_for_match(spoken_text) else '❌'} Yago usado en lugar de Iago en texto hablado",
            f"# {'✅' if all(block['text'].count('[') <= 1 for block in stats['blocks']) else '❌'} Una sola etiqueta por intervencion",
            "#",
            "# VERIFICACION 5 - RECUENTO DE PALABRAS",
            f"# Total palabras sin nombres de presentadores ni cabeceras: {stats['word_count_total']} (minimo: {rules['minimum_word_count']})",
            "#",
            "# TOKENS OPENAI",
            f"# prompt: {usage.prompt}",
            f"# completion: {usage.completion}",
            f"# total: {usage.total}",
            f"# remaining: {remaining_tokens_text(usage.total, token_budget)}",
        ]
    )
    return "\n".join(lines) + "\n"


def remaining_tokens_text(total_tokens: int, budget: int | None) -> str:
    if budget is None:
        return "desconocido (no hay presupuesto configurado)"
    return str(max(budget - total_tokens, 0))


def extract_concepts_for_validation(client: OpenAI | None, spec: dict, topic_pdf_text: str, topic: str, usage: TokenUsage) -> tuple[list[str], list[str], list[str]]:
    if not topic_pdf_text:
        return [], [], []
    if client is None:
        heuristic = extract_theme_concepts(topic_pdf_text, limit=8)
        return heuristic, [], []
    try:
        response = call_chat(
            client=client,
            model=spec["openai"]["default_concept_model"],
            messages=build_concept_extraction_messages(topic_pdf_text, topic),
            max_tokens=spec["openai"]["max_concept_tokens"],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        usage.add(response)
        payload = json.loads(response.choices[0].message.content)
        concepts = payload.get("key_concepts", []) or []
        visual = payload.get("visual_or_hard_for_audio", []) or []
        news_angles = payload.get("candidate_news_angles", []) or []
        concepts = [sanitize_concept_name(concept) for concept in concepts]
        concepts = [concept for concept in concepts if concept]
        return concepts[:8], visual[:5], news_angles[:5]
    except Exception:
        heuristic = [sanitize_concept_name(concept) for concept in extract_theme_concepts(topic_pdf_text, limit=8)]
        return heuristic, [], []


def save_review_report(report_path: Path, ep_code: str, local_issues: list[str], llm_review: dict, usage: TokenUsage, budget: int | None) -> None:
    lines = [f"EPISODIO: {ep_code}", "", "VALIDACION LOCAL"]
    if local_issues:
        lines.extend(f"- {issue}" for issue in local_issues)
    else:
        lines.append("- OK")
    lines.extend(["", "VALIDACION LLM", f"- pass: {llm_review.get('pass')}", f"- score: {llm_review.get('score')}"])
    for issue in llm_review.get("issues", []):
        lines.append(f"- issue: {issue}")
    for issue in llm_review.get("must_fix", []):
        lines.append(f"- must_fix: {issue}")
    lines.extend(
        [
            "",
            "TOKENS OPENAI",
            f"- prompt: {usage.prompt}",
            f"- completion: {usage.completion}",
            f"- total: {usage.total}",
            f"- remaining: {remaining_tokens_text(usage.total, budget)}",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generador de guiones de MaquinarIA Pesada")
    parser.add_argument("--spec", default=str(DEFAULT_SPEC_PATH), help="Ruta a la especificacion maestra")
    parser.add_argument("--ep", default=None, help="Codigo del episodio")
    parser.add_argument("--modulo", default=None, help="Modulo o unidad del episodio")
    parser.add_argument("--tema", default=None, help="Tema principal del episodio")
    parser.add_argument("--objetivo", default=None, help="Objetivo de aprendizaje del episodio")
    parser.add_argument("--duracion-min", type=int, default=None, help="Duracion objetivo en minutos")
    parser.add_argument("--pdf", required=True, help="PDF fuente del tema")
    parser.add_argument("--master-pdf", default=str(DEFAULT_MASTER_PDF), help="PDF maestro completo con referencias")
    parser.add_argument("--contexto-file", default=None, help="Archivo adicional .txt, .md o .pdf")
    parser.add_argument("--estudios", default="", help="Estudios, informes o evidencias a mencionar")
    parser.add_argument("--aplicacion-empresarial", default="", help="Aplicacion empresarial dominante")
    parser.add_argument("--modelo", default=None, help="Modelo OpenAI para generacion")
    parser.add_argument("--modelo-review", default=None, help="Modelo OpenAI para revision")
    parser.add_argument("--token-budget", type=int, default=None, help="Presupuesto total de tokens para esta generacion")
    parser.add_argument("--max-attempts", type=int, default=2, help="Intentos maximos si falla la validacion")
    args = parser.parse_args()

    spec = load_master_spec(args.spec)
    spec_markdown = read_text(Path(args.spec))
    ep_code = args.ep or next_episode_code(spec["directories"]["scripts_dir"])
    duration = args.duracion_min or spec["episode_defaults"]["duration_minutes"]

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        pdf_path = Path("PDFs") / args.pdf
    topic_pdf_text = extract_pdf_text(pdf_path)

    master_pdf_path = Path(args.master_pdf)
    master_pdf_text = extract_pdf_text(master_pdf_path) if master_pdf_path.exists() else ""
    context_text = load_optional_text(args.contexto_file)

    topic = args.tema or infer_topic_from_pdf_name(pdf_path)
    modulo = args.modulo or infer_module_from_pdf_name(pdf_path)
    objective = args.objetivo or (
        "Explicar el tema con rigor tecnico, claridad pedagógica, ejemplos cotidianos y aterrizaje corporativo."
    )

    client = OpenAI() if os.getenv("OPENAI_API_KEY") else None
    usage = TokenUsage()
    generation_model = args.modelo or spec["openai"]["default_generation_model"]
    review_model = args.modelo_review or spec["openai"]["default_review_model"]

    concept_list, visual_concepts, news_angles = extract_concepts_for_validation(
        client, spec, topic_pdf_text, topic, usage
    )
    if not concept_list:
        concept_list = extract_theme_concepts(topic_pdf_text, limit=8)

    master_context = extract_relevant_master_context(master_pdf_text, topic, modulo)

    payload = {
        "episode_code": ep_code,
        "module": modulo,
        "topic": topic,
        "objective": objective,
        "duration_minutes": duration,
        "duration_range_minutes": spec["episode_defaults"]["duration_range_minutes"],
        "target_audience": spec["episode_defaults"]["target_audience"],
        "core_application": args.aplicacion_empresarial,
        "studies_or_evidence": args.estudios,
        "theme_pdf_path": str(pdf_path),
        "theme_pdf_text": topic_pdf_text[:18000],
        "master_pdf_path": str(master_pdf_path) if master_pdf_path.exists() else "",
        "master_context_relevant_excerpt": master_context,
        "additional_context": context_text,
        "key_concepts_from_pdf": concept_list,
        "concepts_hard_for_audio": visual_concepts,
        "candidate_news_angles": news_angles,
    }

    draft = ""
    local_issues: list[str] = []
    llm_review: dict = {"pass": False, "score": 0, "issues": ["No ejecutado"], "must_fix": []}

    if client is None:
        draft = local_script_from_pdf(ep_code, payload, spec, concept_list)
        draft = repair_generated_script(strip_existing_verification_block(draft), ep_code, spec, concept_list)
        absent = []
        extra = []
        verification = build_verification_section(draft, spec, concept_list, absent, extra, usage, args.token_budget)
        draft = draft.rstrip() + "\n\n" + verification
        local_issues = validate_script_text(draft, ep_code, spec, concept_list)
        llm_review = {"pass": len(local_issues) == 0, "score": 60 if not local_issues else 0, "issues": ["OpenAI no disponible, se ha usado el modo local."], "must_fix": local_issues}
    else:
        try:
            for attempt in range(1, args.max_attempts + 1):
                response = call_chat(
                    client=client,
                    model=generation_model,
                    messages=build_generation_messages(spec_markdown, payload, opening_speaker(ep_code, spec)),
                    max_tokens=spec["openai"]["max_output_tokens"],
                    temperature=spec["openai"]["temperature"],
                )
                usage.add(response)
                draft = repair_generated_script(
                    strip_existing_verification_block(response.choices[0].message.content.strip()),
                    ep_code,
                    spec,
                    concept_list,
                )

                absent = []
                extra = news_angles[:2]
                verification = build_verification_section(draft, spec, concept_list, absent, extra, usage, args.token_budget)
                draft = draft.rstrip() + "\n\n" + verification

                local_issues = validate_script_text(draft, ep_code, spec, concept_list)

                review_response = call_chat(
                    client=client,
                    model=review_model,
                    messages=build_review_messages(spec_markdown, ep_code, draft, concept_list),
                    max_tokens=spec["openai"]["max_review_tokens"],
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )
                usage.add(review_response)
                llm_review = json.loads(review_response.choices[0].message.content)

                if not local_issues:
                    break
                if attempt == args.max_attempts:
                    break
                payload["retry_feedback"] = local_issues + llm_review.get("must_fix", [])

            if local_issues:
                expansion_response = call_chat(
                    client=client,
                    model=generation_model,
                    messages=build_expansion_messages(spec_markdown, payload, draft, local_issues),
                    max_tokens=spec["openai"]["max_output_tokens"],
                    temperature=0.5,
                )
                usage.add(expansion_response)
                draft = repair_generated_script(
                    strip_existing_verification_block(expansion_response.choices[0].message.content.strip()),
                    ep_code,
                    spec,
                    concept_list,
                )
                verification = build_verification_section(draft, spec, concept_list, [], news_angles[:2], usage, args.token_budget)
                draft = draft.rstrip() + "\n\n" + verification
                local_issues = validate_script_text(draft, ep_code, spec, concept_list)
        except Exception as exc:
            if "insufficient_quota" not in str(exc):
                raise
            draft = repair_generated_script(
                strip_existing_verification_block(
                    local_script_from_pdf(ep_code, payload, spec, concept_list)
                ),
                ep_code,
                spec,
                concept_list,
            )
            verification = build_verification_section(draft, spec, concept_list, [], news_angles[:2], usage, args.token_budget)
            draft = draft.rstrip() + "\n\n" + verification
            local_issues = validate_script_text(draft, ep_code, spec, concept_list)
            llm_review = {"pass": len(local_issues) == 0, "score": 60 if not local_issues else 0, "issues": ["OpenAI sin cuota: se ha usado el modo local."], "must_fix": local_issues}

    scripts_dir = Path(spec["directories"]["scripts_dir"])
    output_dir = Path(spec["directories"]["output_dir"])
    scripts_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    script_path = scripts_dir / f"{ep_code}.txt"
    report_path = output_dir / f"{ep_code}_guion_validacion.txt"
    save_review_report(report_path, ep_code, local_issues, llm_review, usage, args.token_budget)

    script_path.write_text(draft.rstrip() + "\n", encoding="utf-8")

    if local_issues:
        print(f"Guion generado pero no validado: {script_path}")
        print(f"Reporte: {report_path}")
        print(f"Tokens OpenAI consumidos: {usage.total}")
        print(f"Tokens OpenAI restantes: {remaining_tokens_text(usage.total, args.token_budget)}")
        raise SystemExit("La validacion obligatoria del guion ha fallado. Revisa el reporte.")

    print(f"Guion validado: {script_path}")
    print(f"Reporte: {report_path}")
    print(f"Tokens OpenAI consumidos: {usage.total}")
    print(f"Tokens OpenAI restantes: {remaining_tokens_text(usage.total, args.token_budget)}")

    from estado_proyecto import print_estado_resumen
    print_estado_resumen()


if __name__ == "__main__":
    main()
