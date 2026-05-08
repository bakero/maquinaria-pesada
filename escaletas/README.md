# Escaletas de episodios — MaquinarIA Pesada

Cada archivo `.md` en esta carpeta es la **escaleta de produccion del video**
de un episodio. Es la fuente única de verdad para el render: define momento
a momento qué pasa en pantalla, qué cámara, qué elementos aparecen, qué
transiciones, qué efectos.

## Filosofía

Una escaleta es lo que un guionista de programa de televisión entrega a
producción: una hoja de ruta que cualquier editor puede seguir sin
ambigüedad.

## Convención de nombres

```
escaletas/
  EP-MOD000_escaleta.md   ← M0 Introducción Estratégica
  EP-MOD001_escaleta.md   ← M1 Fundamentos del razonamiento
  ...
```

## Estructura del archivo

Cada escaleta tiene:

1. **Cabecera (frontmatter YAML)**: metadata reutilizable por el pipeline.
2. **Bloques temporales** ordenados (lead silence · hook · sintonía ·
   saludo · bloques 1..N · cierre conceptos · cierre final · outro).
3. **Por cada intervención** dentro de cada bloque:
   - Timecode IN / OUT (`MM:SS.mmm`)
   - Speaker (María / Yago)
   - Texto exacto del guion
   - Tono original
   - **Plano sugerido** (establishing / two-shot / close-up Maria /
     close-up Yago / detail / outro)
   - **On-screen** (qué overlays aparecen, cuándo, dónde, con qué color)
   - **Transición de salida** (corte seco en pausa / fundido / etc.)
4. **Notas de dirección** del guionista para el editor.

## Cómo se genera

```bash
python maquinaria_pesada_pipeline/tools/generate_escaleta.py --episode EP-MOD000
```

Toma como input:

- `Guiones/M{N}_T_*.txt` → guion etiquetado
- `PDFs/RESUMEN_M{N}_*.pdf` → conceptos del temario
- `Videos/escenas_biblioteca/_concepts_index.json` → catálogo del máster
- `episodios/M{N}_E_*.mp3` → audio producido
- `episodios/temp/EP-MOD{NNN}_NNN_*.mp3` → chunks individuales (timestamps)
- `_archivo/EP-MOD{NNN}_produccion.log` → log de producción con bloques
- `aligned_interventions.json` → alineamiento Whisper

Pasa todo a Claude Sonnet con prompt de "guionista profesional de
programas de entretenimiento" y obtiene el markdown estructurado.

Coste aproximado por escaleta: ~$0.30-0.50.

## Cómo se usa

El pipeline `run_pipeline.py` puede consumir la escaleta como input
canónico (futuro paso `5c`): si existe la escaleta para el episodio, la
usa en lugar de generar el `scene_timeline.json` desde cero. Esto da
consistencia entre todos los episodios del máster.
