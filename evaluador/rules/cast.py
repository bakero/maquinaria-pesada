"""Dimensión 2 — Personajes y reparto."""

from __future__ import annotations

import re

from ..parser import Script
from ..spec_data import (
    AVISO_IA_KEYWORDS,
    BLACKLIST_INTERJECTIONS,
    expected_opener_M,
    expected_opener_T,
)
from .base import Finding, hard, soft

_ACCENT_MAP = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")


def _norm(text: str) -> str:
    return text.translate(_ACCENT_MAP).lower()


def evaluate_cast(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_check_yago_spelling(script))
    findings.extend(_check_forbidden_surnames(script))
    findings.extend(_check_blacklist_interjections(script))
    findings.extend(_check_opener_parity(script))
    findings.extend(_check_aviso_ia(script))
    findings.extend(_check_panorama_leader(script))
    findings.extend(_check_realidad_leader(script))
    findings.extend(_check_shared_block_balance(script))
    findings.extend(_check_aplicacion_balance(script))
    findings.extend(_check_leader_opens_block(script))
    findings.extend(_check_s_no_speaker(script))
    return findings


def _check_yago_spelling(script: Script) -> list[Finding]:
    """En texto hablado (no en speaker tag) NO debe aparecer 'Iago' — debe ser 'Yago'."""
    findings: list[Finding] = []
    iago_word_regex = re.compile(r"\bIago\b")
    for sec in script.sections:
        for iv in sec.interventions:
            # texto sin comentarios para evitar falsos positivos en [INTRO]
            text = iv.clean_text
            for m in iago_word_regex.finditer(text):
                findings.append(
                    hard(
                        "cast_all_yago_spelling",
                        f"En texto hablado debe ser 'Yago' (encontrado 'Iago' en pos {m.start()})",
                        line=iv.line_start,
                        speaker=iv.speaker,
                        section=sec.name,
                        snippet=_extract_snippet(text, m.start()),
                        autofixable=True,
                    )
                )
                break  # un finding por intervención basta
    return findings


def _check_forbidden_surnames(script: Script) -> list[Finding]:
    """Apellido inventado tras Maria/Yago."""
    findings: list[Finding] = []
    surname_regex = re.compile(r"\b(Maria|María|Yago)\s+([A-ZÁÉÍÓÚÑ][a-zñáéíóú]+)\b")
    for sec in script.sections:
        for iv in sec.interventions:
            text = iv.clean_text
            for m in surname_regex.finditer(text):
                # Si la palabra "siguiente" empieza una frase nueva (precedida de ". "),
                # no es apellido sino el sujeto del siguiente periodo.
                pos = m.start()
                preceding = text[max(0, pos - 3) : pos]
                if "." in preceding:
                    continue
                findings.append(
                    hard(
                        "cast_all_forbidden_surname",
                        f"Apellido inventado detectado: '{m.group(0)}'",
                        line=iv.line_start,
                        speaker=iv.speaker,
                        section=sec.name,
                        snippet=_extract_snippet(text, pos),
                        autofixable=True,
                    )
                )
                break
    return findings


def _check_blacklist_interjections(script: Script) -> list[Finding]:
    """Interjecciones-coro al inicio de intervención de validación."""
    findings: list[Finding] = []
    # Construye regex con las interjecciones (case-insensitive, al inicio del texto)
    pattern = (
        r"^(?:"
        + "|".join(re.escape(i) for i in BLACKLIST_INTERJECTIONS)
        + r")\b[.,!\s]"
    )
    blacklist_regex = re.compile(pattern, re.IGNORECASE)

    for sec in script.sections:
        for iv in sec.interventions:
            if script.kind != "S" and iv.speaker is None:
                continue
            text = iv.clean_text
            if not text:
                continue
            if blacklist_regex.match(text):
                findings.append(
                    hard(
                        "cast_all_blacklist_interjection",
                        f"Interjección de validación-coro prohibida al inicio: '{text[:30]}…'",
                        line=iv.line_start,
                        speaker=iv.speaker,
                        section=sec.name,
                        snippet=text[:60],
                        autofixable=True,
                    )
                )
    return findings


def _check_opener_parity(script: Script) -> list[Finding]:
    """M par → Maria, M impar → Yago. T impar → Yago, T par → Maria."""
    findings: list[Finding] = []
    opener = script.metadata.get("opener")
    if not opener:
        return findings

    if script.kind == "M":
        n = script.metadata.get("module_number")
        if n is None:
            return findings
        expected = expected_opener_M(n)
        if opener != expected:
            findings.append(
                hard(
                    "cast_m_opener_parity",
                    f"M{n} debe abrirlo {_pretty(expected)}; lo abre {_pretty(opener)}",
                )
            )
    elif script.kind == "T":
        n = script.metadata.get("tema_number")
        if n is None:
            return findings
        expected = expected_opener_T(n)
        if opener != expected:
            mod = script.metadata.get("module_number", "?")
            findings.append(
                hard(
                    "cast_t_opener_parity",
                    f"M{mod}_T{n} debe abrirlo {_pretty(expected)}; lo abre {_pretty(opener)}",
                )
            )
    elif script.kind == "S":
        n = script.metadata.get("s_number")
        if n is None:
            return findings
        # S no tiene speaker tag, así que la paridad es soft (no detectable sin metadata externa).
        # La dejamos como informativa.
        pass

    return findings


def _check_aviso_ia(script: Script) -> list[Finding]:
    """SALUDO_Y_PRESENTACION debe contener las keywords del aviso IA, dichas por el opener."""
    findings: list[Finding] = []
    if script.kind == "S":
        return findings
    saludo = script.section_by_name("SALUDO_Y_PRESENTACION")
    if not saludo:
        return findings

    # buscar las keywords en el texto completo del saludo
    full_text = _norm(" ".join(iv.clean_text for iv in saludo.interventions))
    missing = [kw for kw in AVISO_IA_KEYWORDS if _norm(kw) not in full_text]
    if missing:
        findings.append(
            hard(
                "cast_all_aviso_ia_present",
                f"Falta(n) keyword(s) del aviso IA: {', '.join(missing)}",
                line=saludo.line_start,
                section="SALUDO_Y_PRESENTACION",
            )
        )
        return findings  # no podemos verificar opener si falta

    # ¿quién dice el aviso?
    opener = script.metadata.get("opener")
    aviso_speaker = None
    for iv in saludo.interventions:
        norm = _norm(iv.clean_text)
        if all(_norm(kw) in norm for kw in AVISO_IA_KEYWORDS):
            aviso_speaker = iv.speaker
            break
    if opener and aviso_speaker and aviso_speaker != opener:
        findings.append(
            hard(
                "cast_all_aviso_ia_opener",
                f"Aviso IA lo dice {_pretty(aviso_speaker)}, debe decirlo el opener {_pretty(opener)}",
                line=saludo.line_start,
                section="SALUDO_Y_PRESENTACION",
            )
        )

    return findings


def _check_panorama_leader(script: Script) -> list[Finding]:
    """En BLOQUE_PANORAMA, Yago debe llevar ≥65% de las palabras (M/T)."""
    findings: list[Finding] = []
    if script.kind == "S":
        return findings
    sec = script.section_by_name("BLOQUE_PANORAMA")
    if not sec or sec.word_count == 0:
        return findings
    shares = sec.speaker_share()
    yago = shares.get("IAGO", 0)
    pct = (yago / sec.word_count) * 100
    code = (
        "cast_m_panorama_leader_yago_65"
        if script.kind == "M"
        else "cast_t_panorama_leader_yago_65"
    )
    if pct < 64:
        findings.append(
            hard(
                code,
                f"Yago lleva {pct:.1f}% en BLOQUE_PANORAMA (mínimo 65%)",
                line=sec.line_start,
                section="BLOQUE_PANORAMA",
            )
        )
    elif pct < 65:
        findings.append(
            soft(
                code,
                f"Yago lleva {pct:.1f}% en BLOQUE_PANORAMA (target 65%, tolerancia 1pp)",
                line=sec.line_start,
                section="BLOQUE_PANORAMA",
            )
        )
    return findings


def _check_realidad_leader(script: Script) -> list[Finding]:
    """En T BLOQUE_REALIDAD/CASOS, Maria debe llevar ≥60%."""
    findings: list[Finding] = []
    if script.kind != "T":
        return findings
    sec = script.section_by_name("BLOQUE_REALIDAD") or script.section_by_name(
        "BLOQUE_CASOS"
    )
    if not sec or sec.word_count == 0:
        return findings
    shares = sec.speaker_share()
    maria = shares.get("MARIA", 0)
    pct = (maria / sec.word_count) * 100
    if pct < 59:
        findings.append(
            hard(
                "cast_t_realidad_leader_maria_60",
                f"Maria lleva {pct:.1f}% en {sec.name} (mínimo 60%)",
                line=sec.line_start,
                section=sec.name,
            )
        )
    elif pct < 60:
        findings.append(
            soft(
                "cast_t_realidad_leader_maria_60",
                f"Maria lleva {pct:.1f}% en {sec.name} (target 60%, tolerancia 1pp)",
                line=sec.line_start,
                section=sec.name,
            )
        )
    return findings


def _check_shared_block_balance(script: Script) -> list[Finding]:
    """BLOQUE_DESTACADO (M) y BLOQUE_COMO (T) en rango 40-60% por speaker."""
    findings: list[Finding] = []
    if script.kind == "M":
        target_name = "BLOQUE_DESTACADO"
        code = "cast_m_destacado_balance"
    elif script.kind == "T":
        target_name = "BLOQUE_COMO"
        code = "cast_t_como_balance"
    else:
        return findings
    sec = script.section_by_name(target_name)
    if not sec or sec.word_count == 0:
        return findings
    shares = sec.speaker_share()
    total = sec.word_count
    iago_pct = shares.get("IAGO", 0) / total * 100
    maria_pct = shares.get("MARIA", 0) / total * 100
    for name, pct in (("Yago", iago_pct), ("Maria", maria_pct)):
        if pct < 40 or pct > 60:
            findings.append(
                hard(
                    code,
                    f"{name} {pct:.1f}% en {target_name} (rango 40-60%)",
                    line=sec.line_start,
                    section=target_name,
                )
            )
    return findings


def _check_aplicacion_balance(script: Script) -> list[Finding]:
    """APLICACION_PRACTICA (M): Maria 30-40%, Yago 60-70%."""
    if script.kind != "M":
        return []
    sec = script.section_by_name("APLICACION_PRACTICA")
    if not sec or sec.word_count == 0:
        return []
    shares = sec.speaker_share()
    total = sec.word_count
    maria_pct = shares.get("MARIA", 0) / total * 100
    iago_pct = shares.get("IAGO", 0) / total * 100
    findings: list[Finding] = []
    if not (30 <= maria_pct <= 40):
        findings.append(
            hard(
                "cast_m_aplicacion_balance",
                f"Maria {maria_pct:.1f}% en APLICACION_PRACTICA (rango 30-40%)",
                line=sec.line_start,
                section="APLICACION_PRACTICA",
            )
        )
    if not (60 <= iago_pct <= 70):
        findings.append(
            hard(
                "cast_m_aplicacion_balance",
                f"Yago {iago_pct:.1f}% en APLICACION_PRACTICA (rango 60-70%)",
                line=sec.line_start,
                section="APLICACION_PRACTICA",
            )
        )
    return findings


def _check_leader_opens_block(script: Script) -> list[Finding]:
    """Quien lidera el bloque debe abrir la primera intervención."""
    findings: list[Finding] = []
    leader_map = {
        "BLOQUE_PANORAMA": "IAGO",  # M y T
    }
    if script.kind == "T":
        leader_map["BLOQUE_REALIDAD"] = "MARIA"
        leader_map["BLOQUE_CASOS"] = "MARIA"
    if script.kind == "M":
        leader_map["APLICACION_PRACTICA"] = "MARIA"  # M abre con Maria
    for name, expected in leader_map.items():
        sec = script.section_by_name(name)
        if not sec:
            continue
        first_speaker = None
        for iv in sec.interventions:
            if iv.speaker:
                first_speaker = iv.speaker
                break
        if first_speaker and first_speaker != expected:
            findings.append(
                hard(
                    "cast_all_leader_opens_block",
                    f"{name} debe abrirlo {_pretty(expected)}; abre {_pretty(first_speaker)}",
                    line=sec.line_start,
                    section=name,
                )
            )
    return findings


def _check_s_no_speaker(script: Script) -> list[Finding]:
    if script.kind != "S":
        return []
    # detectado por content si parseó algo con `IAGO:` — no debería estar
    if re.search(
        r"^(IAGO|YAGO|MARIA|MAR[ÍI]A)\s*:", script.raw_text, re.MULTILINE | re.IGNORECASE
    ):
        return [
            hard(
                "cast_s_no_speaker_attribution",
                "S contiene atribución de speaker (debe ser narración neutral)",
            )
        ]
    return []


def _pretty(speaker: str) -> str:
    return {"IAGO": "Yago", "MARIA": "Maria"}.get(speaker, speaker)


def _extract_snippet(text: str, pos: int, span: int = 30) -> str:
    start = max(0, pos - span // 2)
    end = min(len(text), pos + span)
    return text[start:end]
