# Sesión: feature/genepisodios

**Worktree:** `C:\Users\Asus\maquinaria_pesada\.claude\worktrees\genepisodios`
**Rama:** `feature/genepisodios`
**Main path:** `C:\Users\Asus\maquinaria_pesada` → en `master` (no tocar desde aquí)
**Última actualización:** 2026-05-07

---

## Regla de sesión (invariante)

> Todo cambio introducido en la **generación** debe tener su contraparte en
> `validar_episodio.py`: un check que confirme, tras la generación, que ese
> cambio se aplica correctamente en todos los episodios producidos.
> **Sin verificación → el cambio no está completo.**

---

## Flujo de consolidación

- Desarrollar en `feature/genepisodios`
- Cuando algo funcione → merge a `master` + push
- No mezclar con otras ramas activas (`videopodcast`, `APPContenidos`)

---

## Scope de esta rama

**Tocar:**
`generar_guion.py`, `generar_episodio_v2.py`, `producir_episodio.py`,
`podcast_spec.py`, `validar_episodio.py`, `lanzar_produccion.py`,
`normalizar_guiones.py`, `dual_debate*.py`,
`PODCAST_MASTER_SPEC.md`, `INSTRUCCIONES.txt`, `VOICE_CONFIG_REFERENCE.md`,
`Guiones/`, `PDFs/`, `episodios/`

**No tocar:**
`maquinaria_pesada_pipeline/` (→ rama videopodcast)
`cockpit/` (→ rama APPContenidos)

---

## Estado de producción (2026-05-07)

| Módulo | PDF | Guión | Audio | Video |
|--------|-----|-------|-------|-------|
| M0 | ✓ | ✓ | ✓ | ✓ | COMPLETO |
| M1, M2 | ✓ | ✓ | ✓ | ✗ | falta video |
| M3–M14 | ✓ | ✓ | ✗ | ✗ | falta audio |

**Todos los guiones normalizados a Formato A.**

> ⚠️ Los scripts de producción (`lanzar_produccion.py`, `estado_proyecto.py`)
> deben ejecutarse desde el **main path** `C:\Users\Asus\maquinaria_pesada`,
> NO desde este worktree. El worktree no tiene `episodios/` ni `.env`.

> ⚠️ Si se obtiene WinError 10061 al llamar a ElevenLabs, verificar primero
> que la API key en `.env` es válida: `ELEVENLABS_API_KEY=sk_...`

---

## Historial de commits en esta rama

```
533d840 chore: ignore .bak backup files
747d179 fix: normalize guiones B->A, improve production logging and validation
f45696c feat: add normalizar_guiones.py (formato B legacy -> A converter)
```

---

## Cambios introducidos en esta rama

### `podcast_spec.py`
- Tag validation normaliza acentos antes de comparar (`normalize_text_for_match`)

### `normalizar_guiones.py` (nuevo)
- Convierte guiones Formato B → Formato A
- Detecta formatos: A, A_hybrid, B, unknown
- Corrige paridad de speaker en HOOK (IAGO impares, MARÍA pares)
- Añade frases obligatorias faltantes
- Genera `.bak` antes de sobreescribir

### `lanzar_produccion.py`
- Log por episodio: `episodios/{ep}_cmd.log` (stdout + stderr completo)
- Log maestro: `episodios/produccion_runs.log` (acumula sesiones)
- Error hint extraction en consola al fallar
- Timeout de 30 min por episodio

### `generar_episodio_v2.py`
- Separación hard vs soft en `parsear_guion`:
  - Hard → `SystemExit` (estructurales: secciones, speaker, frases obligatorias)
  - Soft → `[WARN]` + continúa (calidad: word count, frases por bloque)

### Guiones M0–M14
- Todos convertidos a Formato A con `normalizar_guiones.py`

---

## Pendientes conocidos

- [ ] Generar 15 audios (ejecutar `lanzar_produccion.py`)
- [ ] Guiones M1–M14 tienen soft warnings de calidad (word count, sentence count) — no bloquean generación
- [ ] Revisar `validar_episodio.py` para añadir checks de las mejoras introducidas

---

## Comandos útiles

**IMPORTANTE: los comandos de producción se ejecutan desde el main path,
no desde este worktree.**

```bash
# --- Desde C:\Users\Asus\maquinaria_pesada (main path) ---

# Ver estado de producción
python estado_proyecto.py

# Lanzar producción (todos los pendientes)
python lanzar_produccion.py

# Lanzar un episodio concreto
python lanzar_produccion.py --ep M3_E_Machine_Learning_Clasico

# Validar episodio generado
python validar_episodio.py --ep M0_E_Introduccion_Estrategica --guion Guiones/M0_T_Introduccion_Estrategica.txt

# --- Desde este worktree (desarrollo de código) ---

# Normalizar guiones (dry-run)
python normalizar_guiones.py --dry-run

# Push de cambios
git add -p && git commit -m "..." && git push origin feature/genepisodios
```
