"""Generador especialista de episodios T (Tema) — v6."""
from __future__ import annotations

import re
from pathlib import Path

from generadores import base_generator as bg
from generadores.shared import pdf_reader, pre_writing
from validators import t_validator
from validators.result import ValidationResult

MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """\
Eres un guionista del podcast MaquinarIA Pesada generando un episodio T (Tema).

FORMATO LITERAL OBLIGATORIO del guion (devuélvelo así, sin XML ni markdown
adicional):

```
# NOMBRE_SECCION
IAGO: [tag] texto de la intervención completo en una línea
MARIA: [tag] respuesta o intervención

# OTRA_SECCION
...
```

- Cabeceras de sección con `# NOMBRE_SECCION` (sin caracteres extra).
- Cada intervención empieza por `IAGO:` o `MARIA:` (literal, en mayúsculas).
- Etiqueta `[tag]` opcional al principio (lista cerrada: didactico,
  explicativo, directo, serio, firme, contundente, grave, tenso,
  conversacional, reflexivo, curioso, ironico, esceptico, natural, pausado,
  calido, claro, analitica).
- PROHIBIDO usar `<Yago>`, `<Maria>`, `<enfasis>`, `<sonido>` ni ninguna
  etiqueta XML/HTML. PROHIBIDO usar markdown `**negrita**`, listas o tablas
  dentro de los diálogos.

Reglas duras de formato v6:

1. Estructura en este orden EXACTO con cabeceras "# SECCION":
   HOOK, INTRO_SONIDO, SALUDO_Y_PRESENTACION, BLOQUE_PANORAMA, BLOQUE_COMO,
   BLOQUE_CASOS, BLOQUE_LIMITES, BLOQUE_FUENTES, CIERRE_CONCEPTOS,
   CIERRE_FINAL, VERIFICACIONES.
2. Duración 25-28 min — word count entre 3700 y 4500 (NUNCA fuera de 2925-4485).
3. HOOK 30-60 s, cierra con "Esto es MaquinarIA Pesada. Arrancamos.".
4. SALUDO_Y_PRESENTACION con 3 intervenciones SEPARADAS + aviso de IA
   advertencia (12-18s, contiene "sistema automatico" y "puede contener errores").
5. Apertura por paridad del nº de TEMA: T impar → Yago, T par → Maria.
   El opener dice HOOK + aviso.
6. BLOQUE_PANORAMA (3-4 min): Yago lidera ≥65 %.
7. BLOQUE_COMO (5-6 min): mecanismo técnico, compartido 40-60 %.
8. BLOQUE_CASOS (4-5 min): casos reales de empresa con NOMBRE PROPIO
   (mínimo 2). Maria lidera ≥60 %.
9. BLOQUE_LIMITES (3-4 min): qué NO es / cuándo no usarlo. Yago lidera ≥55 %.
   Incluye patrones explícitos tipo "no es", "no debe confundirse con",
   "el error común es", "cuando no".
10. BLOQUE_FUENTES (2-3 min): EXACTAMENTE 3 fuentes del tema con autor/año/
    título y por qué importan. NO URLs en audio.
11. CIERRE_CONCEPTOS: EXACTAMENTE 3 conceptos, abre con
    "No te puedes ir de este capitulo sin haber entendido estos conceptos".
12. CIERRE_FINAL: frase canónica + puente al siguiente T del módulo.
13. Cero interjecciones de coro. Sin apellidos para Maria/Yago.
14. Etiquetas TTS de la lista cerrada. Intervenciones de desarrollo
    60-200 palabras, frases ≤32 palabras.
15. Números en palabras (excepto años de papers con autor).
16. NO incluyas APLICACION_PRACTICA — eso es exclusivo del M.

Devuelve SOLO el guion.
"""


def _tema_numbers(episode_id: str) -> tuple[int, int]:
    m = re.match(r"^M(\d+)_T(\d+)", episode_id)
    if not m:
        raise ValueError(f"episode_id no es M{{n}}_T{{x}}: {episode_id!r}")
    return int(m.group(1)), int(m.group(2))


def build_user_prompt(*, episode_id: str, repo_root: Path) -> str:
    modulo_n, tema_n = _tema_numbers(episode_id)
    parts: list[str] = [
        f"Genera el episodio T del tema {tema_n} del módulo {modulo_n}."
    ]

    tema_path = pdf_reader.find_tema(repo_root, modulo_n, tema_n)
    if tema_path:
        pdf_result = pdf_reader.read_pdf(tema_path)
        if pdf_result.text:
            pw = pre_writing.extract_pre_writing(pdf_result.text)
            parts.append("\n## PDF del tema")
            parts.append(pdf_result.text[:10000])
            parts.append("\n## Pre-escritura extraída")
            parts.append(f"Datos numéricos: {pw.datos_numericos[:6]}")
            parts.append(f"Casos con nombre propio: {pw.casos_nombre_propio[:5]}")
            if pw.frase_fuerza:
                parts.append(f"Frase-fuerza: {pw.frase_fuerza}")
            parts.append(f"Contraintuitivos: {pw.contraintuitivos[:3]}")
    else:
        parts.append(f"\n## AVISO: falta el PDF del tema M{modulo_n}_T{tema_n}.")

    # Fuentes auxiliares cuando existen.
    aux = repo_root / "PDFs" / "auxiliares"
    casos_path = aux / "casos_empresariales_ia.md"
    if casos_path.exists():
        parts.append("\n## Casos empresariales (úsalos en BLOQUE_CASOS)")
        parts.append(casos_path.read_text(encoding="utf-8")[:6000])

    fuentes_path = aux / "fuentes_directas.md"
    if fuentes_path.exists():
        parts.append("\n## Fuentes directas (alimentan BLOQUE_FUENTES)")
        parts.append(fuentes_path.read_text(encoding="utf-8")[:4000])

    return "\n".join(parts)


def _validate_fn(text: str, episode_id: str) -> list[ValidationResult]:
    return t_validator.validate(text, episode_id)


def generate(episode_id: str, repo_root: Path | None = None) -> bg.PipelineResult:
    repo_root = (repo_root or Path(__file__).resolve().parents[1]).resolve()
    user_prompt = build_user_prompt(episode_id=episode_id, repo_root=repo_root)
    request = bg.PipelineRequest(
        episode_id=episode_id, kind="T",
        system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt,
        model=MODEL, repo_root=repo_root,
        max_output_tokens=12000, temperature=0.7,
        validate_fn=_validate_fn,
    )
    return bg.run_pipeline(request)
