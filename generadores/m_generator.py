"""Generador especialista de episodios M (Módulo) — v6.

Composición: construye los prompts y delega en `base_generator.run_pipeline()`.
"""
from __future__ import annotations

import re
from pathlib import Path

from generadores import base_generator as bg
from generadores.shared import ficha_aplicacion, pdf_reader, pre_writing
from validators import m_validator
from validators.result import ValidationResult

MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """\
Eres un guionista del podcast MaquinarIA Pesada generando un episodio M (Módulo).

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

Reglas duras de formato v6 — debes respetarlas todas:

1. Estructura del guion en este orden EXACTO con cabeceras "# SECCION":
   HOOK, INTRO_SONIDO, SALUDO_Y_PRESENTACION, BLOQUE_PANORAMA,
   BLOQUE_DESTACADO, APLICACION_PRACTICA, BLOQUE_FUENTES,
   CIERRE_CONCEPTOS, CIERRE_FINAL, VERIFICACIONES.
2. Duración 18-22 min — word count entre 2700 y 3300 (NUNCA fuera de 2400-3680).
3. HOOK 30-60 s. Cierra exactamente con: "Esto es MaquinarIA Pesada. Arrancamos."
4. SALUDO_Y_PRESENTACION con 3 intervenciones SEPARADAS: opener saluda,
   otro saluda, opener da el aviso de IA enganche (18-25s, contiene
   literalmente "sistema automatico" y "puede contener errores").
5. Apertura por paridad del módulo: M par → Maria abre, M impar → Yago.
   El opener dice HOOK + aviso.
6. BLOQUE_PANORAMA: Yago lidera ≥65 %.
7. BLOQUE_DESTACADO: 2-3 conceptos más impactantes, compartido 40-60 %.
8. APLICACION_PRACTICA: 3 momentos (Maria abre 45-60s; Yago detalla
   high-level 2-2.5 min; cierre conjunto 30-45s). Maria 30-40 %, Yago 60-70 %.
9. BLOQUE_FUENTES: 3-4 fuentes-marco del módulo entero, cada una con
   autor/año/título y por qué importa. NO leer URLs en audio.
10. CIERRE_CONCEPTOS: 3-5 conceptos canónicos, abre con
    "No te puedes ir de este capitulo sin haber entendido estos conceptos".
11. CIERRE_FINAL incluye literalmente la frase canónica de cierre + CTA a T.
12. Cero interjecciones de validación-coro ("exactamente", "claro que sí",
    "exacto", etc.). Apellidos prohibidos para Maria/Yago.
13. Etiquetas TTS: una por intervención, lista cerrada. Una sola voz por
    turno con cuerpo de desarrollo de 4-10 frases (60-200 palabras).
14. Frases ≤32 palabras. No abusar de frases cortas seguidas.
15. Números en palabras (excepto años de papers acompañados de autor).
16. La aplicación práctica NO aparece en el HOOK.

Genera SOLO el guion en este formato, sin explicaciones ni preámbulos.
"""


def _module_n(episode_id: str) -> int:
    m = re.match(r"^M(\d+)$", episode_id)
    if not m:
        raise ValueError(f"episode_id no es M{{n}}: {episode_id!r}")
    return int(m.group(1))


def build_user_prompt(*, episode_id: str, repo_root: Path) -> str:
    """Construye el prompt user inyectando PDF + pre-escritura + ficha
    aplicación + fuentes-marco."""
    n = _module_n(episode_id)
    parts: list[str] = [f"Genera el episodio M{n} sobre el módulo {n} del máster."]

    # PDF RESUMEN del módulo.
    resumen_path = pdf_reader.find_resumen(repo_root, n)
    if resumen_path:
        pdf_result = pdf_reader.read_pdf(resumen_path)
        if pdf_result.text:
            pw = pre_writing.extract_pre_writing(pdf_result.text)
            parts.append("\n## PDF RESUMEN del módulo")
            parts.append(pdf_result.text[:8000])
            parts.append("\n## Pre-escritura extraída")
            parts.append(f"Datos numéricos: {pw.datos_numericos[:8]}")
            parts.append(f"Casos con nombre propio: {pw.casos_nombre_propio[:6]}")
            if pw.frase_fuerza:
                parts.append(f"Frase-fuerza: {pw.frase_fuerza}")
            parts.append(f"Contraintuitivos: {pw.contraintuitivos[:4]}")

    # Ficha de aplicación práctica.
    override = repo_root / "PDFs" / "aplicacion_practica" / f"M{n}.md"
    ficha = ficha_aplicacion.build_ficha(
        modulo_n=n, repo_root=repo_root,
        override_path=override if override.exists() else None,
    )
    ficha_aplicacion.save_ficha(ficha, repo_root)
    parts.append("\n## Ficha de aplicación práctica (del sistema generador)")
    parts.append(ficha.to_markdown())

    # Fuentes-marco: PDF maestro del corpus + PDFs de los temas del módulo.
    master_pdf = None
    for name in ("master IA.pdf", "master_IA.pdf", "MasterIA.pdf"):
        cand = repo_root / "PDFs" / "auxiliares" / name
        if cand.exists():
            master_pdf = cand
            break
    if master_pdf is not None:
        master_result = pdf_reader.read_pdf(master_pdf)
        if master_result.text:
            parts.append(
                "\n## Bibliografía maestra del corpus (úsala como fuente "
                "principal para BLOQUE_FUENTES)"
            )
            # Truncamos para no inflar el prompt; el LLM elige las 3-4 más
            # relevantes al módulo.
            parts.append(master_result.text[:10000])
    else:
        parts.append(
            "\n## AVISO: falta PDFs/auxiliares/master IA.pdf; "
            "BLOQUE_FUENTES quedará incompleto sin esta bibliografía."
        )

    # Temas del módulo (contexto adicional para enriquecer BLOQUE_FUENTES).
    temas_dir = repo_root / "PDFs" / "temas"
    if temas_dir.exists():
        temas_paths = sorted(temas_dir.glob(f"M{n}_T*.pdf"))
        if temas_paths:
            parts.append(
                f"\n## Temas del módulo (PDFs disponibles, {len(temas_paths)})"
            )
            for tp in temas_paths:
                parts.append(f"- {tp.relative_to(repo_root).as_posix()}")

    return "\n".join(parts)


def _validate_factory(repo_root: Path):
    def validate(text: str, episode_id: str) -> list[ValidationResult]:
        return m_validator.validate(text, episode_id, repo_root=repo_root)
    return validate


def generate(episode_id: str, repo_root: Path | None = None) -> bg.PipelineResult:
    """Genera el guion de un episodio M y devuelve el PipelineResult."""
    repo_root = (repo_root or Path(__file__).resolve().parents[1]).resolve()
    user_prompt = build_user_prompt(episode_id=episode_id, repo_root=repo_root)
    request = bg.PipelineRequest(
        episode_id=episode_id, kind="M",
        system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt,
        model=MODEL, repo_root=repo_root,
        max_output_tokens=10000, temperature=0.7,
        validate_fn=_validate_factory(repo_root),
    )
    return bg.run_pipeline(request)
