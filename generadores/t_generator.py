"""Generador especialista de episodios T (Tema) — v6."""
from __future__ import annotations

import re
from pathlib import Path

from generadores import base_generator as bg
from generadores.shared import pdf_reader, pre_writing
from generadores.shared.anthropic_client import CacheableBlock
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
2. Duración 25-28 min — word count OBLIGATORIO entre 3700 y 4500. La validación
   rechaza CUALQUIER guion fuera de [2925, 4485]. Cuenta antes de entregar.
   Apunta a 3800-4200 para tener margen. Si te quedas corto, AÑADE un caso
   más en BLOQUE_CASOS o un sub-mecanismo en BLOQUE_COMO; NO recortes los
   bloques ya escritos.
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
10. BLOQUE_FUENTES (2-3 min): EXACTAMENTE 3 FUENTES — ni 2, ni 4, ni 5.
    Cada fuente lleva su año en palabras (ej.: "Vaswani y otros, dos mil
    diecisiete..."). EN TOTAL EXACTAMENTE 3 AÑOS DISTINTOS aparecen en el
    bloque, ligados a sus fuentes. **NO repitas años entre fuentes** (si
    dos fuentes son del mismo año el validador solo cuenta una y será
    HARD-FAIL). **NO menciones un 4º o 5º año en ninguna parte del bloque**
    (ni en aclaraciones, ni en datos de adopción dentro del bloque, ni en
    referencias laterales). Si quieres dar contexto temporal usa "hoy",
    "actualmente", "en los últimos años" — sin cifrar año. NO leas URLs.
    ANTES de cerrar el bloque: cuenta los años distintos. Si son 2 → AÑADE
    una tercera fuente. Si son 4+ → ELIMINA fuentes o convierte años
    laterales a expresiones temporales.
11. BLOQUE_CASOS: menciona LITERALMENTE al menos 2 empresas con su
    nombre propio reconocible (OpenAI, Anthropic, Google, Meta, Microsoft,
    IBM, Amazon, BBVA, Santander, Telefonica, Spotify, Netflix, etc.).
    Maria lidera ≥60 % palabras en este bloque.
12. BLOQUE_PANORAMA: Yago lidera con ≥65 % palabras del bloque (turnos
    suyos más largos y frecuentes; Maria solo entra 1 turno por cada 3 de Yago).
13. BLOQUE_COMO: reparto compartido — Yago debe quedar entre 40 % y 60 %
    de las palabras del bloque. Maria interviene SUSTANCIALMENTE: 4-6
    turnos largos (60-120 palabras cada uno) aportando ejemplos, matices,
    o detalles complementarios. NO uses a Maria solo para preguntas
    cortas — debe explicar pasos del mecanismo con el mismo nivel técnico
    que Yago.
14. BLOQUE_LIMITES: Yago lidera ≥55 %. Debe contener al menos uno de
    estos patrones explícitos: "no es", "no debe confundirse con",
    "el error común es", "cuando no".
15. CIERRE_CONCEPTOS: EXACTAMENTE 3 intervenciones (una por concepto).
    Abre con esta frase literal palabra por palabra:
    "No te puedes ir de este capitulo sin haber entendido estos conceptos"
16. CIERRE_FINAL: debe contener EXACTAMENTE esta frase literal al final
    (palabra por palabra). Antes puedes añadir 1-2 intervenciones de
    puente al siguiente T del módulo, pero la frase canónica final es:
    "Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada. Siguenos para nuevos capitulos donde la I.A. crea contenido sobre I.A."
17. HOOK cierra LITERALMENTE con: "Esto es MaquinarIA Pesada. Arrancamos."
18. Apertura por paridad del nº de TEMA: T impar → Yago opener, T par →
    Maria opener. El opener dice HOOK + el aviso de IA.
19. Aviso de IA advertencia: contiene LITERALMENTE "sistema automatico"
    y "puede contener errores", entre 30 y 50 palabras (12-18s).
20. Cero interjecciones de coro ("exacto", "exactamente"). Sin apellidos
    para Maria/Yago.
21. Etiquetas TTS de la lista cerrada. Intervenciones de desarrollo
    60-200 palabras.
22. Reglas TTS críticas (no negociable):
    - NINGUNA frase >32 palabras. Si la idea es larga, pártela en dos.
    - No encadenes más de 3 frases cortas (<12 palabras) seguidas.
    - Reacciones/preguntas de la voz de apoyo ≤15 palabras.
23. NUNCA escribas cifras en dígitos en el habla. Números en palabras
    ("ochenta y ocho por ciento", "dos mil veintitres"). Excepción: años
    de papers acompañados de autor.
24. NO incluyas APLICACION_PRACTICA — eso es exclusivo del M.

24.1 ⚠️ ANTI-UNDERSHOOT WORD COUNT — APLICAR SIEMPRE:
    Tras escribir el guion completo, CUENTA las palabras totales del diálogo.
    Si el total <3700 (estás CORTO):
    - AÑADE un cuarto caso de empresa en BLOQUE_CASOS de 200-300 palabras
      con cifra concreta documentada. Ejemplo de plantilla a copiar:
      "MARIA: [didactico] El caso de [Empresa] es especialmente revelador.
      [Empresa] implementó [técnica] en [contexto/año en palabras] y
      [verbo] [cifra concreta en palabras]. [Detalle del proceso, 2-3
      frases adicionales]. El resultado: [métrica final en palabras]."
    - Empresas válidas adicionales (catálogo extendido): Morgan Stanley,
      JPMorgan, Harvey AI, Lemonade, OpenAI, Anthropic, Google, Microsoft,
      IBM, BBVA, Santander, Zara, Netflix, Spotify, Meta, NVIDIA, GitHub,
      Stripe, Walmart, Amazon, Pfizer, Roche, Cognition AI, Zendesk,
      Weights & Biases, DataRobot.
    - Si tras añadir el caso sigues <3700, AMPLIA BLOQUE_COMO con UN
      sub-mecanismo adicional explicado por Maria (150-200 palabras).
    - NO ENTREGUES guion T con word_count <3700. El validador es estricto.

24.2 ⚠️ ANTI-DESBALANCE BLOQUE_COMO:
    BLOQUE_COMO requiere que tanto Yago como Maria queden entre 35% y 65%
    de las palabras del bloque. Si Maria <35%:
    - AÑADE un sub-mecanismo completo explicado por Maria de 150-200
      palabras (4-6 frases técnicas, mismo nivel que Yago).
    - Maria NO puede limitarse a preguntas cortas en COMO — debe explicar
      pasos del mecanismo (forward pass, backpropagation, embeddings,
      attention, etc. — depende del tema).
    Si Yago <35%: lo contrario, dale a Yago otro turno de desarrollo.

25. ⚠️ PRE-CIERRE DE GUION — VERIFICACIÓN OBLIGATORIA antes de devolver:
    Antes de devolver el guion, RECORRE mentalmente esta checklist:
    [ ] HOOK termina con "Esto es MaquinarIA Pesada. Arrancamos."
    [ ] HOOK lo abre el speaker correcto por paridad del nº de TEMA
        (T impar→Yago, T par→Maria).
    [ ] SALUDO tiene 3 intervenciones separadas; el aviso de IA lo da el opener.
    [ ] BLOQUE_PANORAMA: Yago ≥65% (cuenta palabras).
    [ ] BLOQUE_COMO: ambos speakers entre 40% y 60%. Maria explica al menos
        UN sub-mecanismo completo (4-6 frases, 70-120 palabras).
    [ ] BLOQUE_CASOS: Maria ≥60%; menciona ≥2 EMPRESAS con nombre propio
        reconocible (Harvey AI, Morgan Stanley, JPMorgan, IBM, Microsoft,
        Google, OpenAI, Anthropic, Lemonade, Zara, Nordea, BBVA, McKinsey...).
    [ ] BLOQUE_LIMITES: Yago ≥55%; usa "no es"/"no debe confundirse"/etc.
    [ ] BLOQUE_FUENTES: EXACTAMENTE 3 fuentes con 3 AÑOS DISTINTOS (no 2,
        no 4, no 5). CUENTA los años explícitos en el bloque.
    [ ] CIERRE_CONCEPTOS: EXACTAMENTE 3 intervenciones; la 1ª combina la
        apertura canónica con "Primero: [concepto]" en un solo bloque.
    [ ] CIERRE_FINAL incluye literal la frase canónica.
    [ ] Word count total del diálogo: 3800-4200 palabras (mínimo duro 2925).
    [ ] PINGPONG: en cada bloque, el speaker de APOYO debe tener ratio
        palabras / palabras-líder ≤ 0.33. En PANORAMA y LIMITES Maria
        sólo hace preguntas/reacciones breves de 5-12 palabras; en
        CASOS, Yago igual.
    [ ] FRASES LARGAS: ninguna frase debe superar 32 palabras. Pártelas
        en 2 más cortas usando puntos.
    [ ] FRASES CORTAS SEGUIDAS: no más de 3 frases ≤8 palabras seguidas
        en una misma intervención. Fusiona con conectores.
    [ ] TAGS TTS: usa SOLO [didactico], [analitico], [reflexivo], [claro],
        [explicativo], [curioso], [escéptico], [enfático].
    Si alguna casilla falla, CORRIGE antes de devolver.

Devuelve SOLO el guion.
"""


def _tema_numbers(episode_id: str) -> tuple[int, int]:
    m = re.match(r"^M(\d+)_T(\d+)", episode_id)
    if not m:
        raise ValueError(f"episode_id no es M{{n}}_T{{x}}: {episode_id!r}")
    return int(m.group(1)), int(m.group(2))


def build_user_prompt(*, episode_id: str, repo_root: Path) -> str:
    modulo_n, tema_n = _tema_numbers(episode_id)
    # Paridad del nº de TEMA: impar → Yago, par → Maria.
    opener = "IAGO" if tema_n % 2 == 1 else "MARIA"
    opener_spoken = "Yago" if opener == "IAGO" else "Maria"
    other = "MARIA" if opener == "IAGO" else "IAGO"
    parts: list[str] = [
        f"Genera el episodio T del tema {tema_n} del módulo {modulo_n}.",
        "",
        f"## ⚠️ OPENER OBLIGATORIO (paridad T{tema_n}): {opener} "
        f"(nombre hablado: '{opener_spoken}')",
        f"El HOOK lo abre {opener}. El aviso de IA en SALUDO_Y_PRESENTACION "
        f"lo pronuncia {opener} (NO {other}). HARD-FAIL si abre el speaker contrario "
        f"o si {other} pronuncia el aviso de IA.",
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

    # ⚠️ Checklist final — patrón de fallos sistemáticos: opener equivocado,
    # word_count corto, BLOQUE_COMO desbalanceado, fuentes con años repetidos,
    # CASOS sin nombres reconocibles.
    parts.append(
        "\n## ⚠️ CHECKLIST OBLIGATORIO ANTES DE DEVOLVER EL GUION\n"
        f"1. HOOK abierto por {opener} ('{opener_spoken}'); aviso de IA pronunciado "
        f"por {opener} (NO {other}).\n"
        "2. Palabras totales del diálogo entre 3700 y 4200 (rango duro 2925-4485).\n"
        "   Si te quedas corto, AÑADE: un sub-mecanismo más en BLOQUE_COMO, o un\n"
        "   caso más en BLOQUE_CASOS, o ampliar BLOQUE_LIMITES con un anti-patrón.\n"
        "   NO recortes nada.\n"
        "3. CIERRE_CONCEPTOS: EXACTAMENTE 3 INTERVENCIONES. La PRIMERA contiene\n"
        "   la apertura literal \"No te puedes ir de este capitulo sin haber\n"
        "   entendido estos conceptos\" + \"Primero: [concepto 1]\" — EN UN ÚNICO\n"
        "   BLOQUE del opener. Bloque 2: \"Segundo: [concepto 2]\" (otro speaker).\n"
        "   Bloque 3: \"Tercero: [concepto 3]\" (opener).\n"
        "4. CIERRE_FINAL: incluye la frase canónica de cierre.\n"
        "   ⚠️ CRÍTICO: escribe 'I.A.' con PUNTOS (NO expandas a 'inteligencia\n"
        "   artificial'). El TTS lo pronunciará 'i-a' como marca, coherente\n"
        "   con 'MaquinarIA'. Las tildes son válidas y se aceptan.\n"
        "   Frase exacta a incluir literal:\n"
        "   \"Y hasta aquí ha llegado nuestro episodio de MaquinarIA Pesada. \"\n"
        "   \"Síguenos para nuevos capítulos donde la I.A. crea contenido sobre I.A.\"\n"
        "5. BLOQUE_PANORAMA: Yago lidera con ≥65% de palabras. Maria solo\n"
        "   1 pregunta por cada 3 turnos de Yago (≤15 palabras cada pregunta).\n"
        "6. BLOQUE_COMO: COMPARTIDO. Yago entre 40% y 60%. Si Maria queda <40%,\n"
        "   AÑÁDELE otro sub-mecanismo completo de 4-6 frases (70-120 palabras)\n"
        "   antes de cerrar el bloque. Maria DEBE explicar al menos 2 sub-mecanismos.\n"
        "7. BLOQUE_CASOS: Maria lidera con ≥60% de palabras. Menciona EXPLÍCITAMENTE\n"
        "   al menos 2 empresas con nombre propio reconocible. Lista canónica:\n"
        "   Harvey AI, Morgan Stanley, JPMorgan, IBM, Microsoft, Google, OpenAI,\n"
        "   Anthropic, Meta, Lemonade, Zara, Nordea, BBVA, Santander, Telefonica,\n"
        "   Netflix, Spotify, Salesforce, McKinsey, Gartner.\n"
        "8. BLOQUE_LIMITES: Yago lidera ≥55%. Incluye textualmente uno o más de:\n"
        "   \"no es\", \"no debe confundirse con\", \"el error común es\", \"cuando no\".\n"
        "9. BLOQUE_FUENTES: EXACTAMENTE 3 FUENTES con 3 AÑOS DISTINTOS ENTRE SÍ.\n"
        "   ⚠️ 2, 4 o 5 fuentes/años → HARD-FAIL. 3 es OBLIGATORIO. No repitas\n"
        "   años. Después de escribir el bloque, CUENTA los años distintos\n"
        "   mencionados y CONFIRMA que son exactamente 3. Si hay 4 o más años\n"
        "   en el bloque (aunque sea en aclaraciones laterales), elimínalos o\n"
        "   reescríbelos como expresiones sin año (\"hoy\", \"actualmente\").\n"
        "   Cada fuente: autor o institución + año en palabras\n"
        "   (ej.: \"Vaswani y otros, dos mil diecisiete\").\n"
        "10. Word count final: vuelve a contar. Si <3700, AÑADE bloque hasta\n"
        "    llegar a 3800 mínimo. Mejor 3900-4200. No entregues guion <3700."
    )

    return "\n".join(parts)


def _validate_fn(text: str, episode_id: str) -> list[ValidationResult]:
    return t_validator.validate(text, episode_id)


def generate(episode_id: str, repo_root: Path | None = None) -> bg.PipelineResult:
    repo_root = (repo_root or Path(__file__).resolve().parents[1]).resolve()
    user_prompt = build_user_prompt(episode_id=episode_id, repo_root=repo_root)
    # SYSTEM_PROMPT cacheado con TTL 1h (estable entre TODOS los episodios).
    # El user_prompt v6 con checklist completo va sin cache para preservar
    # el efecto enforcement (word_count, leader_balance, casos_company).
    request = bg.PipelineRequest(
        episode_id=episode_id, kind="T",
        system_blocks=[CacheableBlock(text=SYSTEM_PROMPT, ttl="1h")],
        user_prompt=user_prompt,
        model=MODEL, repo_root=repo_root,
        max_output_tokens=12000, temperature=0.7,
        validate_fn=_validate_fn,
        # T necesita 5 retries del v6 — el word_count enforcement requiere
        # iteraciones para subir de ~3300 al target 3700-4200.
        max_retries=bg.env_max_retries("T", 5),
        # T exige EXACTAMENTE 3 fuentes con años distintos. Si el modelo se
        # pasa, recortamos a 3. El undershoot (<3) sigue dependiendo del
        # retry con feedback.
        trim_fuentes_max_years=3,
    )
    return bg.run_pipeline(request)
