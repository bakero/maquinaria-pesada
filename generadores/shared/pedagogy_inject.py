"""Inyector pedagógico post-generación.

Idea: en vez de pedir al modelo que expanda términos técnicos en primera
mención (regla que generaba conflictos con word_count y balance), aplicamos
la expansión DESPUÉS de generar el guion, como transformación determinista.

Para cada término técnico de la lista canónica:
- Busca su primera aparición (post-overrides, en texto fonético)
- Si NO tiene expansión cercana, inserta la expansión justo después
- Si ya tiene expansión cercana, no toca

Diseñado para no romper:
- Frases canónicas (HOOK closing, CIERRE_FINAL)
- Cabeceras de sección
- Etiquetas TTS [tag]
- Formato IAGO:/MARIA:
"""
from __future__ import annotations

import re

# Lista de (term_post_override, expansion_a_insertar, expansion_marker_para_dedup)
# - term_post_override: como aparece en el .txt tras pronunciation_overrides
# - expansion_a_insertar: lo que se inserta entre comas justo tras el termino
# - expansion_marker: regex de comprobacion para detectar si ya esta expandido
#
# Las expansiones van en CASTELLANO (sin el termino ingles completo) porque
# leer "Retrieval-Augmented Generation" en TTS castellano suena raro. Los
# nombres propios de producto (open ei ai, etc.) se preservan con su override.
_INJECTIONS: tuple[tuple[str, str, str], ...] = (
    # (term, expansion_castellana, marker_para_no_duplicar)
    # Términos en su forma POST-override (siglas deletreadas en castellano).
    ("ele ele eme", "grandes modelos de lenguaje",
     r"(grandes modelos|modelos de lenguaje|large language)"),
    ("rag", "generación aumentada por recuperación",
     r"(retrieval|recuperaci[oó]n|aumentad)"),
    ("fain tiuning", "ajuste fino del modelo",
     r"(ajuste fino|ajustar el modelo|afinar)"),
    ("embedin", "vector que representa significado",
     r"(representaci[oó]n|vector|incrustaci[oó]n)"),
    ("ge pe te", "modelo generativo preentrenado",
     r"(generative pre|generativo|transformador generativo)"),
    ("chat ge pe te", "asistente conversacional basado en inteligencia artificial",
     r"(asistente conversacional|chatbot)"),
    ("paiplain", "flujo de procesamiento",
     r"(secuencia|tuber[ií]a|flujo de proces|cadena de proces)"),
    ("a pe i", "interfaz de programación de aplicaciones",
     r"interfaz"),
    ("ge pe u", "unidad de procesamiento gráfico",
     r"(unidad de procesamiento|tarjeta gráfica)"),
    ("te pe u", "unidad de procesamiento tensorial",
     r"unidad de procesamiento tensorial"),
    ("deitaset", "conjunto de datos",
     r"conjunto de datos"),
    ("erre ele ache efe", "aprendizaje por refuerzo con retroalimentación humana",
     r"(aprendizaje por refuerzo|reinforcement learning)"),
    ("eme ce pe", "protocolo de contexto del modelo",
     r"(model context protocol|protocolo de contexto)"),
    ("ce o te", "cadena de pensamiento",
     r"(cadena de pensamiento|razonamiento paso a paso|chain.of.thought)"),
    ("jota ese o ene", "formato de datos estructurado",
     r"formato"),
    ("fréimuork", "marco de trabajo",
     r"marco de trabajo"),
    ("dropáut", "técnica de regularización por apagado aleatorio",
     r"(regularizaci[oó]n|apagado aleatorio)"),
    ("fiu shot", "con pocos ejemplos",
     r"(pocos ejemplos|few.shot)"),
    ("zero shot", "sin ejemplos previos",
     r"(sin ejemplos|cero ejemplos|zero.shot)"),
    ("hagin feis", "plataforma comunitaria de modelos de IA",
     r"(plataforma|comunidad de modelos)"),
    ("paitorch", "biblioteca de aprendizaje profundo",
     r"(biblioteca|framework de)"),
    ("tensorflou", "biblioteca de aprendizaje profundo",
     r"(biblioteca|framework de)"),
    # Siglas IA mas frecuentes
    ("pe ce a", "análisis de componentes principales",
     r"(an[aá]lisis de componentes|principal component)"),
    ("hache i te ele", "humano en el bucle",
     r"(humano en el bucle|human.in.the.loop)"),
    ("erre ene ene", "red neuronal recurrente",
     r"red neuronal recurrente"),
    ("ele ese te eme", "red de memoria a largo y corto plazo",
     r"(memoria a largo|long short.term)"),
    ("ce ene ene", "red neuronal convolucional",
     r"red neuronal convolucional"),
    ("ku lora", "adaptación de bajo rango con cuantización",
     r"(adaptaci[oó]n de bajo rango|low.rank adaptation)"),
)

# Caracteres que NO pueden preceder a la insercion (estamos dentro de cabecera
# de seccion o tras "IAGO:" / "MARIA:" sin texto previo).
_HEADER_RE = re.compile(r"^#\s+[A-Z_]+\s*$", re.MULTILINE)


def _has_expansion_near(text: str, pos: int, marker: str, window: int = 250) -> bool:
    chunk = text[max(0, pos - window): pos + window]
    return bool(re.search(marker, chunk, re.IGNORECASE))


def _find_first_safe(text: str, term: str) -> int | None:
    """Encuentra la primera aparicion del termino que NO este en cabecera,
    SSML break o linea vacia.

    Acepta lineas con IAGO:/MARIA: (formato M/T) y lineas de texto narrativo
    continuo (formato S, sin speaker prefix).
    """
    pattern = re.compile(rf"(?<![\w]){re.escape(term)}(?![\w])", re.IGNORECASE)
    for m in pattern.finditer(text):
        pos = m.start()
        line_start = text.rfind("\n", 0, pos) + 1
        line_end = text.find("\n", pos)
        if line_end == -1:
            line_end = len(text)
        line = text[line_start:line_end].strip()
        # Saltar: cabecera, vacia, SSML break, frase canonica del cierre S.
        if not line:
            continue
        if line.startswith("#"):
            continue
        if line.startswith("<break"):
            continue
        # Frase canonica de cierre S: "Mas sobre X en el episodio T de MaquinarIA Pesada."
        # NO inyectar dentro de ella (el termino seria el del tema y rompe el cierre).
        if re.search(r"m[aá]s sobre .+ en el episodio t de maquinaria pesada",
                     line, re.IGNORECASE):
            continue
        return m.end()
    return None


def inject_first_mentions(text: str) -> tuple[str, list[str]]:
    """Inyecta expansiones en primeras menciones de terminos sin expansion cerca.

    Devuelve (texto_modificado, lista_de_terminos_inyectados).
    """
    out = text
    injected: list[str] = []
    # Procesar de mayor a menor longitud para no romper coincidencias.
    sorted_terms = sorted(_INJECTIONS, key=lambda x: -len(x[0]))
    for term, expansion, marker in sorted_terms:
        end_pos = _find_first_safe(out, term)
        if end_pos is None:
            continue
        # ¿Ya esta expandido cerca?
        if _has_expansion_near(out, end_pos, marker):
            continue
        # Insertar `, expansion,` justo despues del termino.
        # Si el caracter siguiente es ya una coma o punto, ajustar.
        # Pattern: insertar tras end_pos.
        suffix_char = out[end_pos] if end_pos < len(out) else " "
        if suffix_char in (",", ".", ";", ":", "?", "!"):
            # Reemplazar el patron "term[puntuacion]" por "term, exp[puntuacion]"
            insertion = f", {expansion}"
        else:
            # "term " -> "term, exp,"
            insertion = f", {expansion},"
        out = out[:end_pos] + insertion + out[end_pos:]
        injected.append(term)
    return out, injected
