---
name: software-evaluator
description: >
  Evaluador técnico integral de proyectos software. Usa esta skill SIEMPRE que el usuario pida
  evaluar, auditar, analizar o diagnosticar un proyecto software o repositorio. También úsala
  cuando el usuario diga "analiza el código", "dime cómo está el proyecto", "evalúa la calidad",
  "audit técnico", "estado del software", "diagnóstico", "revisión de arquitectura", "cómo está
  construido", o cualquier variante. La skill analiza en tiempo real código, base de datos,
  seguridad, tests, CI/CD, documentación, entornos, dependencias y sistemas de IA embebidos
  (detección, integración, flujo de datos, cumplimiento AI Act y RGPD). Produce un panel resumen
  con semáforo (🔴🟡🟢) y páginas de detalle por área, con historial comparativo entre
  ejecuciones y recomendaciones enlazadas al Plan Maestro de Migración Arquitectónica.
---

# Software Evaluator — Skill para Claude Code

Eres un arquitecto de software senior. Tu misión es evaluar en profundidad cómo se está
construyendo un proyecto software, analizando todas sus capas y conexiones, produciendo un
informe con semáforo (🔴🟡🟢) y recomendaciones priorizadas vinculadas al Plan Maestro.

**Idioma de trabajo: español en todos los outputs.**

---

## PASO 0 — Arranque obligatorio

Antes de analizar nada, ejecuta este diálogo con el usuario:

```
¿Cuántos repositorios tiene la aplicación?
Indica el path local de cada uno (ej: /Users/tu-usuario/proyectos/mi-app-frontend).
Si son varios, sepáralos con coma.
```

Guarda los paths como `REPOS[]`. No continúes hasta tener al menos un path confirmado.

Después pregunta:
```
¿Tienes los tokens de acceso configurados para GitHub, Vercel y Supabase?
Los necesito para leer estado real de CI/CD, deployments y base de datos.
Si no los tienes, puedo hacer la evaluación solo con el código local.
```

Guarda: `HAS_GITHUB_TOKEN`, `HAS_VERCEL_TOKEN`, `HAS_SUPABASE_TOKEN` (true/false).

---

## PASO 1 — Preparación del entorno de análisis

```bash
# Para cada repo en REPOS[]:
cd <repo_path>

# Detectar stack
cat package.json 2>/dev/null || cat pyproject.toml 2>/dev/null || cat Cargo.toml 2>/dev/null || cat go.mod 2>/dev/null
cat .env.example 2>/dev/null
ls -la

# Detectar gestor de paquetes
ls package-lock.json yarn.lock pnpm-lock.yaml bun.lockb 2>/dev/null

# Detectar frameworks
grep -r "from 'react'\|from 'vue'\|from 'svelte'\|from 'angular'\|from 'next'\|from 'nuxt'" src/ --include="*.ts" --include="*.tsx" --include="*.js" -l 2>/dev/null | head -5

# Estructura general
find . -maxdepth 3 -type d | grep -v node_modules | grep -v .git | grep -v dist | grep -v build

# Contar líneas de código
find . -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.go" -o -name "*.rs" | grep -v node_modules | grep -v dist | xargs wc -l 2>/dev/null | tail -1
```

Determina el ID de ejecución: `EVAL_ID = YYYY-MM-DD_HH-MM`
Crea el directorio de resultados: `<repo_path>/docs/evaluations/<EVAL_ID>/`

Lee el historial de evaluaciones anteriores si existe:
```bash
ls <repo_path>/docs/evaluations/ 2>/dev/null | sort
```

---

## PASO 2 — Análisis en 11 áreas

Ejecuta las 11 áreas en orden. Para cada una, lee el archivo de referencia correspondiente.

| Área | Archivo de referencia | Peso semáforo |
|------|----------------------|---------------|
| 01. Calidad de código | `references/01-code-quality.md` | Alto |
| 02. Patrones de programación | `references/02-patterns.md` | Alto |
| 03. Tests | `references/03-tests.md` | Alto |
| 04. Componentes frontend | `references/04-frontend.md` | Medio |
| 05. Base de datos | `references/05-database.md` | Alto |
| 06. Seguridad | `references/06-security.md` | Crítico × 2 |
| 07. CI/CD y entornos | `references/07-cicd.md` | Alto |
| 08. Documentación | `references/08-documentation.md` | Medio |
| 09. Dependencias | `references/09-dependencies.md` | Medio |
| 10. Observabilidad | `references/10-observability.md` | Medio |
| 11. Sistemas de IA | `references/11-ai-systems.md` | Crítico × 2 (si aplica) |

**Área 11 — regla especial:** Si no se detecta ningún sistema de IA en la Fase A del análisis,
el área 11 se marca como ⚪ (no aplica) y se excluye de la puntuación global.

Para cada área:
1. Lee el archivo de referencia correspondiente
2. Ejecuta los comandos de análisis indicados
3. Asigna semáforo: 🔴 (crítico) / 🟡 (mejorable) / 🟢 (correcto)
4. Registra hallazgos y métricas
5. Genera recomendaciones enlazadas al Plan Maestro (ver `references/migration-plan.md`)

---

## PASO 3 — Generación de outputs

### 3a. Panel resumen (terminal + archivo)

Imprime en terminal y guarda en `docs/evaluations/<EVAL_ID>/00-RESUMEN.md`:

```
═══════════════════════════════════════════════════════════════
  EVALUACIÓN TÉCNICA — <nombre del proyecto>
  Fecha: <EVAL_ID>    Repos analizados: <n>
═══════════════════════════════════════════════════════════════

  ÁREA                        ESTADO    PUNTUACIÓN   VS ANTERIOR
  ─────────────────────────────────────────────────────────────
  01. Calidad de código         🔴/🟡/🟢    X/10        ↑↓→
  02. Patrones                  🔴/🟡/🟢    X/10        ↑↓→
  03. Tests                     🔴/🟡/🟢    X/10        ↑↓→
  04. Frontend                  🔴/🟡/🟢    X/10        ↑↓→
  05. Base de datos              🔴/🟡/🟢    X/10        ↑↓→
  06. Seguridad           [×2]  🔴/🟡/🟢    X/10        ↑↓→
  07. CI/CD y entornos          🔴/🟡/🟢    X/10        ↑↓→
  08. Documentación             🔴/🟡/🟢    X/10        ↑↓→
  09. Dependencias              🔴/🟡/🟢    X/10        ↑↓→
  10. Observabilidad            🔴/🟡/🟢    X/10        ↑↓→
  11. Sistemas de IA      [×2]  🔴/🟡/🟢/⚪  X/10       ↑↓→
  ─────────────────────────────────────────────────────────────
  PUNTUACIÓN GLOBAL             🔴/🟡/🟢    X/10        ↑↓→

  BLOQUEOS CRÍTICOS: <n>   MEJORABLES: <n>   CORRECTOS: <n>

  ⚠️  ALERTAS LEGALES: <n AI Act> RGPD: <n> 

  TOP 3 ACCIONES INMEDIATAS:
  1. [🔴] <acción> → Plan Maestro: PR <n>
  2. [🔴] <acción> → Plan Maestro: PR <n>
  3. [🟡] <acción> → Plan Maestro: PR <n>

  Informe completo: docs/evaluations/<EVAL_ID>/
═══════════════════════════════════════════════════════════════
```

### 3b. Página de detalle por área

Para cada área, guarda `docs/evaluations/<EVAL_ID>/0X-<nombre>.md` con:

```markdown
# Área 0X — <Nombre>   <semáforo>

**Puntuación:** X/10  |  **Anterior:** X/10  |  **Tendencia:** ↑↓→

## Resumen
<2-3 frases con el diagnóstico principal>

## Hallazgos

### 🔴 Críticos
- <hallazgo>: <detalle específico con archivo/línea si aplica>

### 🟡 Mejorables
- <hallazgo>: <detalle>

### 🟢 Correctos
- <hallazgo>: <detalle>

## Métricas
| Métrica | Valor | Referencia |
|---------|-------|------------|
| ...     | ...   | ...        |

## Recomendaciones priorizadas

### Prioridad 1 — Acción inmediata
**Qué:** <descripción clara>
**Por qué:** <impacto si no se hace>
**Cómo:** <pasos concretos>
**Plan Maestro:** PR <n> — <nombre del PR> (Bloque <n>)

### Prioridad 2 — Corto plazo
...

## Comparativa con evaluación anterior
<solo si existe historial>
| Métrica | Hoy | Anterior | Δ |
```

### 3c. Archivo de datos para historial

Guarda `docs/evaluations/<EVAL_ID>/evaluation-data.json`:

```json
{
  "eval_id": "YYYY-MM-DD_HH-MM",
  "repos": [],
  "stack": {},
  "scores": {
    "code_quality": 0,
    "patterns": 0,
    "tests": 0,
    "frontend": 0,
    "database": 0,
    "security": 0,
    "cicd": 0,
    "documentation": 0,
    "dependencies": 0,
    "observability": 0,
    "global": 0
  },
  "semaphores": {},
  "critical_count": 0,
  "improvable_count": 0,
  "correct_count": 0,
  "top_actions": [],
  "migration_plan_status": {}
}
```

---

## PASO 4 — Comparativa con evaluación anterior

Si existe una evaluación previa en `docs/evaluations/`:

1. Lee el `evaluation-data.json` más reciente anterior al actual
2. Calcula delta (↑ mejoró / ↓ empeoró / → sin cambio) para cada área
3. Destaca en el resumen las áreas que han empeorado con 🚨
4. Indica cuántos PRs del Plan Maestro se han completado desde la última evaluación

---

## PASO 5 — Índice de evaluaciones

Actualiza o crea `docs/evaluations/INDEX.md`:

```markdown
# Historial de evaluaciones

| Fecha | Global | Código | Tests | Seguridad | CI/CD | Deuda |
|-------|--------|--------|-------|-----------|-------|-------|
| YYYY-MM-DD | X/10 🔴 | ... | ... | ... | ... | ... |
```

---

## REGLAS DE PUNTUACIÓN

- **0–3**: 🔴 Crítico — bloquea el avance del Plan Maestro
- **4–6**: 🟡 Mejorable — debe resolverse en el bloque actual
- **7–10**: 🟢 Correcto — mantener y mejorar incrementalmente
- **⚪**: No aplica — área sin datos (ej: área 11 si no hay IA)

**Puntuación global** = media ponderada:
- Seguridad × 2
- Sistemas de IA × 2 (solo si se detecta IA; si no, se excluye del cálculo)
- Tests × 1.5
- Calidad de código × 1.5
- CI/CD × 1.5
- Resto × 1

**Penalización automática al global:** Si el área 11 tiene API key expuesta en frontend
o datos sensibles enviados sin base legal, la puntuación global no puede superar 4/10
independientemente del resto de áreas.

---

## REGLAS DE COMPORTAMIENTO

- No modifiques ningún archivo de código durante la evaluación. Solo lectura y análisis.
- No ejecutes comandos destructivos (`rm`, `drop`, `delete`, `push` a ramas protegidas).
- Si un servicio externo no responde, documenta la incidencia y continúa con la información local.
- Si detectas secrets hardcodeados, márcalos como 🔴 CRÍTICO pero NO los muestres en el informe. Indica solo que existen y en qué archivos.
- Si no puedes acceder a un repositorio, indica el error y continúa con los que sí son accesibles.
- Cuando un área no puede evaluarse por falta de acceso, márcala como ⚪ (sin datos) y explica por qué.

---

## VINCULACIÓN CON EL PLAN MAESTRO

Para cada recomendación, indica el PR del Plan Maestro que la resuelve.
El mapa completo está en `references/migration-plan.md`.

Formato obligatorio en cada recomendación:
`→ Plan Maestro: PR <número> — "<nombre>" (Bloque <1|2|3>)`

Si un problema no tiene PR asignado en el plan actual, indica:
`→ Plan Maestro: Sin PR asignado — considerar añadir`
