# Listado de tareas — Semanas previas + 9 semanas de podcast

**MaquinarIA Pesada · Pre-Fase 0 + Fase 0 + Fase 1 (Módulo 0 + arranque Módulo 1)**

**Convenciones:**
- **`LISTA`** = fecha límite para tener la tarea terminada
- **`SALE`** = fecha de producción/publicación pública
- **`OWNER`**: TÚ (manual) · CLAUDE (Claude Code) · MIXTO (genera Claude, ajustás tú)
- **`CHECK`** = tarea de verificación
- **`DEP`** = dependencia (tarea que tiene que estar lista antes)
- Hora por defecto de publicación: **08:00** para audio · **09:00** para LinkedIn (salvo que se indique otra)

---

## BLOQUE 0 — Pre-lanzamiento (antes del 18/05/2026)

### Producción del sistema y activos base

**T001** · Pipeline de generación de guion del podcast operativo · `OWNER:` TÚ · `LISTA:` 04/05/2026 · `SALE:` —
**T002** · Pipeline de generación de voz (ElevenLabs) operativo con IAgo y MarIA configurados · `OWNER:` TÚ · `LISTA:` 04/05/2026 · `SALE:` —
**T003** · Pipeline de edición final de audio operativo · `OWNER:` TÚ · `LISTA:` 04/05/2026 · `SALE:` —
**T004** · Generación de los 6 T del Módulo 0 (audio final) · `OWNER:` MIXTO · `LISTA:` 08/05/2026 · `SALE:` —
**T005** · Generación del M0 (resumen del módulo + APLICACION_PRACTICA, audio final) · `OWNER:` MIXTO · `LISTA:` 15/05/2026 · `SALE:` —
**T006** · CHECK: escucha completa de los 6 T del M0, validación de calidad de voz, ritmo y contenido · `OWNER:` TÚ · `LISTA:` 11/05/2026 · `SALE:` —
**T007** · CHECK: escucha completa del M0, validación de calidad y duración (~15-17 min) · `OWNER:` TÚ · `LISTA:` 18/05/2026 · `SALE:` —
**T008** · Selección de 7 T representativos + 3 M significativos para prelist (de momento solo M0 disponible — material parcial OK para prelist) · `OWNER:` TÚ · `LISTA:` 18/05/2026 · `SALE:` —

### Sistema visual y plantillas

**T009** · Plantilla Figma armada: paleta CAT (#0D0D0D, #F5C400, #4DB8FF, #CC2200), tipografías display + monospace, componentes logo/tag · `OWNER:` TÚ · `LISTA:` 11/05/2026 · `SALE:` —
**T010** · Frame infografía estática 1080×1080 + 1080×1350 en Figma · `OWNER:` TÚ · `LISTA:` 11/05/2026 · `SALE:` — · `DEP:` T009
**T011** · Frame quotable 1080×1080 en Figma · `OWNER:` TÚ · `LISTA:` 11/05/2026 · `SALE:` — · `DEP:` T009
**T012** · Frame carrusel 1080×1350 (8 slides reutilizables) en Figma · `OWNER:` TÚ · `LISTA:` 11/05/2026 · `SALE:` — · `DEP:` T009
**T013** · Banco de capturas reales del sistema (Claude Code generando, JSON del guion, repo commits, panel de Spotify) — 8-10 capturas listas para reutilizar en build-in-public · `OWNER:` TÚ · `LISTA:` 15/05/2026 · `SALE:` —
**T014** · CHECK: squint test de las plantillas (¿se lee en mobile, hay contraste, una forma central?) · `OWNER:` TÚ · `LISTA:` 12/05/2026 · `SALE:` — · `DEP:` T009-T012

### Cuentas, accesos y configuración técnica

**T015** · Cuenta Spotify for Podcasters creada y verificada · `OWNER:` TÚ · `LISTA:` 11/05/2026 · `SALE:` —
**T016** · Cuenta iVoox creada y verificada · `OWNER:` TÚ · `LISTA:` 11/05/2026 · `SALE:` —
**T017** · RSS de Spotify for Podcasters configurado y distribuyendo a Apple Podcasts + Amazon Music · `OWNER:` TÚ · `LISTA:` 13/05/2026 · `SALE:` — · `DEP:` T015
**T018** · CHECK: verificar que Apple Podcasts y Amazon Music reciben el RSS (puede tardar 24-72h en aparecer) · `OWNER:` TÚ · `LISTA:` 17/05/2026 · `SALE:` — · `DEP:` T017
**T019** · Plantilla de descripción de episodio para Spotify (200-400 palabras con keywords) · `OWNER:` MIXTO · `LISTA:` 13/05/2026 · `SALE:` —
**T020** · Plantilla de descripción de episodio para iVoox (categoría: Tecnología → IA) · `OWNER:` MIXTO · `LISTA:` 13/05/2026 · `SALE:` —
**T021** · LinkedIn — perfil revisado y alineado con posicionamiento (foto, headline, "about") · `OWNER:` TÚ · `LISTA:` 15/05/2026 · `SALE:` —

### Materiales para la prelist

**T022** · Documento de invitación a prelist (qué van a oír, qué pedís, plazo, link al podcast privado) · `OWNER:` TÚ · `LISTA:` 22/05/2026 · `SALE:` —
**T023** · Formulario de feedback de la prelist (4-5 preguntas concretas del calendario v2 §3.3) · `OWNER:` TÚ · `LISTA:` 22/05/2026 · `SALE:` —
**T024** · Mecanismo de entrega de los episodios a la prelist (¿enlace privado de Spotify, Google Drive, otro?) · `OWNER:` TÚ · `LISTA:` 22/05/2026 · `SALE:` —
**T025** · Lista inicial de contactos para DM directo de reclutamiento (10-15 personas cercanas) · `OWNER:` TÚ · `LISTA:` 23/05/2026 · `SALE:` —

---

## SEMANA 1 — 18 a 22 mayo 2026 (Pre-Fase 0 · Calentar feed)

### Producción de contenido S1

**T026** · Redactar post S1 lunes (Build-in-public — sistema con Claude Code, 4 patrones que no salieron a la primera) · `OWNER:` TÚ · `LISTA:` 17/05/2026 · `SALE:` 18/05/2026
**T027** · Seleccionar captura del repo/JSON para post S1 lunes · `OWNER:` TÚ · `LISTA:` 17/05/2026 · `SALE:` 18/05/2026 · `DEP:` T013
**T028** · CHECK: pasar checklist style guide §6 a post S1 lunes · `OWNER:` TÚ · `LISTA:` 17/05/2026 · `SALE:` 18/05/2026 · `DEP:` T026
**T029** · Publicar post S1 lunes en LinkedIn · `OWNER:` TÚ · `LISTA:` 18/05/2026 09:00 · `SALE:` 18/05/2026 · `DEP:` T028

**T030** · Redactar post S1 miércoles (Reflexión "cómo aprendo tecnología", referencia a Un tema al día / Hoy en El País) · `OWNER:` TÚ · `LISTA:` 19/05/2026 · `SALE:` 20/05/2026
**T031** · CHECK: pasar checklist style guide §6 a post S1 miércoles · `OWNER:` TÚ · `LISTA:` 19/05/2026 · `SALE:` 20/05/2026 · `DEP:` T030
**T032** · Publicar post S1 miércoles en LinkedIn · `OWNER:` TÚ · `LISTA:` 20/05/2026 09:00 · `SALE:` 20/05/2026 · `DEP:` T031

**T033** · Redactar post S1 jueves (Hot take consultoría — empresas compran tecnología antes de saber qué problema tienen) · `OWNER:` TÚ · `LISTA:` 20/05/2026 · `SALE:` 21/05/2026
**T034** · CHECK: pasar checklist style guide §6 a post S1 jueves · `OWNER:` TÚ · `LISTA:` 20/05/2026 · `SALE:` 21/05/2026 · `DEP:` T033
**T035** · Publicar post S1 jueves en LinkedIn · `OWNER:` TÚ · `LISTA:` 21/05/2026 09:00 · `SALE:` 21/05/2026 · `DEP:` T034

**T036** · Redactar post S1 viernes (Build-in-public — reducir etiquetas en ElevenLabs mejoró voces) · `OWNER:` TÚ · `LISTA:` 21/05/2026 · `SALE:` 22/05/2026
**T037** · Generar visual comparativa antes/después o fragmento guion para post S1 viernes · `OWNER:` TÚ · `LISTA:` 21/05/2026 · `SALE:` 22/05/2026 · `DEP:` T013
**T038** · CHECK: pasar checklist style guide §6 a post S1 viernes · `OWNER:` TÚ · `LISTA:` 21/05/2026 · `SALE:` 22/05/2026 · `DEP:` T036
**T039** · Publicar post S1 viernes en LinkedIn · `OWNER:` TÚ · `LISTA:` 22/05/2026 09:00 · `SALE:` 22/05/2026 · `DEP:` T038

### Comunidad y métricas S1

**T040** · Responder comentarios y DMs S1 (revisión diaria, 15-20 min) · `OWNER:` TÚ · `LISTA:` diario S1 · `SALE:` —
**T041** · CHECK lunes 25/05: revisar métricas LinkedIn S1 (impresiones, engagement, DMs) · `OWNER:` TÚ · `LISTA:` 25/05/2026 · `SALE:` —

---

## SEMANA 2 — 25 a 29 mayo 2026 (Fase 0 · Reclutamiento prelist)

### Producción de contenido S2

**T042** · Redactar post S2 lunes 🔴 (RECLUTAMIENTO PRELIST — sin nombrar el podcast todavía, CTA específica) · `OWNER:` TÚ · `LISTA:` 24/05/2026 · `SALE:` 25/05/2026
**T043** · Preparar visual opcional para post S2 lunes (foto setup o waveform sin info) · `OWNER:` TÚ · `LISTA:` 24/05/2026 · `SALE:` 25/05/2026
**T044** · CHECK: revisión doble del post S2 lunes (es pivote, merece segunda lectura con 24h de margen) · `OWNER:` TÚ · `LISTA:` 24/05/2026 · `SALE:` 25/05/2026 · `DEP:` T042
**T045** · Enviar DM previo a 10-15 contactos cercanos (T025) avisando que mañana publico el post de reclutamiento, pedir que comenten en la primera hora · `OWNER:` TÚ · `LISTA:` 24/05/2026 · `SALE:` 25/05/2026 · `DEP:` T025
**T046** · Publicar post S2 lunes en LinkedIn 09:00 🔴 · `OWNER:` TÚ · `LISTA:` 25/05/2026 09:00 · `SALE:` 25/05/2026 · `DEP:` T044
**T047** · Responder DMs entrantes de reclutamiento durante las primeras 4h tras publicar (máxima atención) · `OWNER:` TÚ · `LISTA:` 25/05/2026 13:00 · `SALE:` 25/05/2026 · `DEP:` T046

**T048** · Redactar post S2 miércoles (Build-in-public voces con system prompt distinto) · `OWNER:` TÚ · `LISTA:` 26/05/2026 · `SALE:` 27/05/2026
**T049** · Generar diagrama de flujo guion → turnos → generación para post S2 miércoles · `OWNER:` TÚ · `LISTA:` 26/05/2026 · `SALE:` 27/05/2026 · `DEP:` T009
**T050** · CHECK: pasar checklist style guide §6 a post S2 miércoles · `OWNER:` TÚ · `LISTA:` 26/05/2026 · `SALE:` 27/05/2026 · `DEP:` T048
**T051** · Publicar post S2 miércoles en LinkedIn · `OWNER:` TÚ · `LISTA:` 27/05/2026 09:00 · `SALE:` 27/05/2026 · `DEP:` T050

**T052** · Redactar post S2 jueves (Hot take 33% — escalar IA es método, no tecnología) · `OWNER:` TÚ · `LISTA:` 27/05/2026 · `SALE:` 28/05/2026
**T053** · Generar infografía simple "33%" (opcional) para post S2 jueves · `OWNER:` TÚ · `LISTA:` 27/05/2026 · `SALE:` 28/05/2026 · `DEP:` T010
**T054** · CHECK: pasar checklist style guide §6 a post S2 jueves · `OWNER:` TÚ · `LISTA:` 27/05/2026 · `SALE:` 28/05/2026 · `DEP:` T052
**T055** · Publicar post S2 jueves en LinkedIn · `OWNER:` TÚ · `LISTA:` 28/05/2026 09:00 · `SALE:` 28/05/2026 · `DEP:` T054

**T056** · Redactar post S2 viernes (Personal UOC 2011 — máster de videojuegos, preferencia por el sistema sobre el output) · `OWNER:` TÚ · `LISTA:` 28/05/2026 · `SALE:` 29/05/2026
**T057** · CHECK: pasar checklist style guide §6 a post S2 viernes · `OWNER:` TÚ · `LISTA:` 28/05/2026 · `SALE:` 29/05/2026 · `DEP:` T056
**T058** · Publicar post S2 viernes en LinkedIn · `OWNER:` TÚ · `LISTA:` 29/05/2026 09:00 · `SALE:` 29/05/2026 · `DEP:` T057

### Gestión de la prelist S2

**T059** · Recibir y registrar respuestas de reclutamiento de prelist (LinkedIn DMs + comentarios) · `OWNER:` TÚ · `LISTA:` continuo · `SALE:` —
**T060** · Enviar enlace privado del Módulo 0 + formulario de feedback a cada persona que se apunta · `OWNER:` TÚ · `LISTA:` continuo (24h máx desde su DM) · `SALE:` — · `DEP:` T022, T023, T024
**T061** · CHECK viernes 29/05: contar prelist confirmada. ¿Estamos cerca de 30? Si <10, activar plan de respaldo (DMs directos extra) · `OWNER:` TÚ · `LISTA:` 29/05/2026 · `SALE:` —

---

## SEMANA 3 — 1 a 5 junio 2026 (Fase 0 · Validación + anuncio fecha)

### Producción de contenido S3

**T062** · Redactar post S3 lunes (Hot take ANI vs AGI — toda la IA de 2025 es estrecha) · `OWNER:` TÚ · `LISTA:` 31/05/2026 · `SALE:` 01/06/2026
**T063** · CHECK: pasar checklist style guide §6 a post S3 lunes · `OWNER:` TÚ · `LISTA:` 31/05/2026 · `SALE:` 01/06/2026 · `DEP:` T062
**T064** · Publicar post S3 lunes en LinkedIn · `OWNER:` TÚ · `LISTA:` 01/06/2026 09:00 · `SALE:` 01/06/2026 · `DEP:` T063

**T065** · Redactar post S3 miércoles (Build-in-public feedback de la prelist — recoger feedback real, no inventar) · `OWNER:` TÚ · `LISTA:` 02/06/2026 · `SALE:` 03/06/2026 · `DEP:` T059
**T066** · Preparar captura anonimizada de mensaje de feedback (opcional) · `OWNER:` TÚ · `LISTA:` 02/06/2026 · `SALE:` 03/06/2026
**T067** · CHECK: pasar checklist style guide §6 a post S3 miércoles · `OWNER:` TÚ · `LISTA:` 02/06/2026 · `SALE:` 03/06/2026 · `DEP:` T065
**T068** · Publicar post S3 miércoles en LinkedIn · `OWNER:` TÚ · `LISTA:` 03/06/2026 09:00 · `SALE:` 03/06/2026 · `DEP:` T067

**T069** · Redactar post S3 jueves (Reflexión consultoría — proyectos fracasan más por falta de feedback temprano que por errores técnicos) · `OWNER:` TÚ · `LISTA:` 03/06/2026 · `SALE:` 04/06/2026
**T070** · CHECK: pasar checklist style guide §6 a post S3 jueves · `OWNER:` TÚ · `LISTA:` 03/06/2026 · `SALE:` 04/06/2026 · `DEP:` T069
**T071** · Publicar post S3 jueves en LinkedIn · `OWNER:` TÚ · `LISTA:` 04/06/2026 09:00 · `SALE:` 04/06/2026 · `DEP:` T070

**T072** · Redactar post S3 viernes 🔴 (ANUNCIO NOMBRE + FECHA — MaquinarIA Pesada, martes 09/06 8:00) · `OWNER:` TÚ · `LISTA:` 04/06/2026 · `SALE:` 05/06/2026
**T073** · Diseñar infografía estática 1080×1350 del anuncio (fondo #0D0D0D, "MAQUINARIA PESADA" monumental, fecha en monospace, lista 6 T del M0, logo) · `OWNER:` TÚ · `LISTA:` 04/06/2026 · `SALE:` 05/06/2026 · `DEP:` T010
**T074** · CHECK: revisión doble del post S3 viernes (pivote) + squint test de la infografía · `OWNER:` TÚ · `LISTA:` 04/06/2026 · `SALE:` 05/06/2026 · `DEP:` T072, T073
**T075** · Publicar post S3 viernes en LinkedIn 09:00 🔴 · `OWNER:` TÚ · `LISTA:` 05/06/2026 09:00 · `SALE:` 05/06/2026 · `DEP:` T074

### Cierre de Fase 0 y preparación del drop S4

**T076** · CHECK viernes 05/06: cerrar la prelist. Compilar feedback recibido. Identificar 3-5 hallazgos potentes para post de S6 si aplica · `OWNER:` TÚ · `LISTA:` 05/06/2026 · `SALE:` — · `DEP:` T059
**T077** · Subir los 6 T del M0 a Spotify for Podcasters (programados para 09/06 8:00) · `OWNER:` TÚ · `LISTA:` 05/06/2026 · `SALE:` 09/06/2026 08:00 · `DEP:` T004, T015, T019
**T078** · CHECK: verificar que los 6 T del M0 están correctamente programados en Spotify (título, descripción, miniatura del bloque, fecha y hora) · `OWNER:` TÚ · `LISTA:` 06/06/2026 · `SALE:` — · `DEP:` T077
**T079** · Preparar archivos de los 6 T del M0 para subida manual a iVoox el 09/06 (no permite programación fiable según calendario v2) · `OWNER:` TÚ · `LISTA:` 06/06/2026 · `SALE:` 09/06/2026 · `DEP:` T004, T016, T020
**T080** · Lista de 5-10 contactos cercanos para DM previo al drop, pidiendo que comenten en la primera hora del 09/06 · `OWNER:` TÚ · `LISTA:` 07/06/2026 · `SALE:` —

---

## SEMANA 4 — 8 a 12 junio 2026 (Fase 1 · DROP PÚBLICO Módulo 0)

### Drop del Módulo 0 (martes 09/06)

**T081** · Redactar post S4 lunes (Build-in-public pre-drop — qué rompió 3 veces el pipeline esta semana) · `OWNER:` TÚ · `LISTA:` 07/06/2026 · `SALE:` 08/06/2026
**T082** · Preparar captura de log/JSON para post S4 lunes · `OWNER:` TÚ · `LISTA:` 07/06/2026 · `SALE:` 08/06/2026 · `DEP:` T013
**T083** · CHECK: pasar checklist style guide §6 a post S4 lunes · `OWNER:` TÚ · `LISTA:` 07/06/2026 · `SALE:` 08/06/2026 · `DEP:` T081
**T084** · Publicar post S4 lunes en LinkedIn · `OWNER:` TÚ · `LISTA:` 08/06/2026 09:00 · `SALE:` 08/06/2026 · `DEP:` T083

**T085** · Enviar DM previo a contactos de la lista T080 avisando del drop de mañana, pidiendo comentar en primera hora · `OWNER:` TÚ · `LISTA:` 08/06/2026 · `SALE:` 09/06/2026 · `DEP:` T080

**T086** · 09/06 08:00 — Publicación automática de los 6 T en Spotify (verificar que se ha disparado) · `OWNER:` TÚ · `LISTA:` 09/06/2026 08:00 · `SALE:` 09/06/2026 08:00 · `DEP:` T077
**T087** · 09/06 08:15 — Subida manual de los 6 T a iVoox · `OWNER:` TÚ · `LISTA:` 09/06/2026 08:15 · `SALE:` 09/06/2026 08:15 · `DEP:` T079
**T088** · CHECK: verificar que los 6 T son accesibles públicamente en Spotify e iVoox a las 08:30 · `OWNER:` TÚ · `LISTA:` 09/06/2026 08:30 · `SALE:` — · `DEP:` T086, T087
**T089** · CHECK: verificar (durante la mañana) que Apple Podcasts y Amazon Music recogen los episodios vía RSS · `OWNER:` TÚ · `LISTA:` 09/06/2026 12:00 · `SALE:` — · `DEP:` T086

**T090** · Redactar post S4 martes 🔴 (ANUNCIO DEL DROP — está vivo, 6 episodios del Módulo 0) · `OWNER:` TÚ · `LISTA:` 08/06/2026 · `SALE:` 09/06/2026
**T091** · Diseñar infografía-índice del Módulo 0 (1080×1350, "MÓDULO 0 — INTRODUCCIÓN ESTRATÉGICA" + 6 títulos T en monospace) · `OWNER:` TÚ · `LISTA:` 08/06/2026 · `SALE:` 09/06/2026 · `DEP:` T010
**T092** · CHECK: revisión doble del post S4 martes (pivote) + squint test de la infografía · `OWNER:` TÚ · `LISTA:` 08/06/2026 · `SALE:` 09/06/2026 · `DEP:` T090, T091
**T093** · Publicar post S4 martes en LinkedIn 09:00 🔴 · `OWNER:` TÚ · `LISTA:` 09/06/2026 09:00 · `SALE:` 09/06/2026 · `DEP:` T092
**T094** · Añadir enlaces a Spotify e iVoox en el primer comentario del post S4 martes (NO YouTube) · `OWNER:` TÚ · `LISTA:` 09/06/2026 09:05 · `SALE:` 09/06/2026 · `DEP:` T093
**T095** · Atención intensiva a comentarios y DMs durante las primeras 4h del drop · `OWNER:` TÚ · `LISTA:` 09/06/2026 13:00 · `SALE:` 09/06/2026 · `DEP:` T093

**T096** · Redactar post S4 jueves (Recap T6 — ciclo de adopción, 88%/33%) · `OWNER:` TÚ · `LISTA:` 10/06/2026 · `SALE:` 11/06/2026
**T097** · Diseñar quotable estático 1080×1080 del dato 88%/33% con atribución "M0.T6" · `OWNER:` TÚ · `LISTA:` 10/06/2026 · `SALE:` 11/06/2026 · `DEP:` T011
**T098** · CHECK: pasar checklist style guide §6 a post S4 jueves · `OWNER:` TÚ · `LISTA:` 10/06/2026 · `SALE:` 11/06/2026 · `DEP:` T096
**T099** · Publicar post S4 jueves en LinkedIn · `OWNER:` TÚ · `LISTA:` 11/06/2026 09:00 · `SALE:` 11/06/2026 · `DEP:` T098
**T100** · Añadir enlace a Spotify e iVoox del T6 en primer comentario · `OWNER:` TÚ · `LISTA:` 11/06/2026 09:05 · `SALE:` 11/06/2026 · `DEP:` T099

**T101** · Redactar copy del post S4 viernes 🔴 (carrusel ANATOMÍA DEL SISTEMA — copy 100-150 palabras) · `OWNER:` TÚ · `LISTA:` 10/06/2026 · `SALE:` 12/06/2026
**T102** · Diseñar slide 1 del carrusel anatomía (portada/hook) · `OWNER:` TÚ · `LISTA:` 09/06/2026 · `SALE:` 12/06/2026 · `DEP:` T012
**T103** · Diseñar slide 2 del carrusel (input PDF del temario) · `OWNER:` TÚ · `LISTA:` 09/06/2026 · `SALE:` 12/06/2026 · `DEP:` T012
**T104** · Diseñar slide 3 del carrusel (extracción y estructura del temario) · `OWNER:` TÚ · `LISTA:` 10/06/2026 · `SALE:` 12/06/2026 · `DEP:` T012
**T105** · Diseñar slide 4 del carrusel (generación de guion con Claude Code) · `OWNER:` TÚ · `LISTA:` 10/06/2026 · `SALE:` 12/06/2026 · `DEP:` T012
**T106** · Diseñar slide 5 del carrusel (asignación de turnos entre voces) · `OWNER:` TÚ · `LISTA:` 11/06/2026 · `SALE:` 12/06/2026 · `DEP:` T012
**T107** · Diseñar slide 6 del carrusel (generación de audio en ElevenLabs) · `OWNER:` TÚ · `LISTA:` 11/06/2026 · `SALE:` 12/06/2026 · `DEP:` T012
**T108** · Diseñar slide 7 del carrusel (edición + metadata) · `OWNER:` TÚ · `LISTA:` 11/06/2026 · `SALE:` 12/06/2026 · `DEP:` T012
**T109** · Diseñar slide 8 del carrusel (cierre + CTA suave a Spotify/iVoox) · `OWNER:` TÚ · `LISTA:` 11/06/2026 · `SALE:` 12/06/2026 · `DEP:` T012
**T110** · CHECK: revisión doble del carrusel completo + squint test slide por slide · `OWNER:` TÚ · `LISTA:` 11/06/2026 · `SALE:` 12/06/2026 · `DEP:` T102-T109
**T111** · CHECK: pasar checklist style guide §6 al copy del post S4 viernes · `OWNER:` TÚ · `LISTA:` 11/06/2026 · `SALE:` 12/06/2026 · `DEP:` T101
**T112** · Publicar post S4 viernes en LinkedIn con carrusel 🔴 · `OWNER:` TÚ · `LISTA:` 12/06/2026 09:00 · `SALE:` 12/06/2026 · `DEP:` T110, T111

### Comunidad y métricas S4

**T113** · Responder comentarios y DMs S4 (revisión mañana y tarde, especialmente martes 09/06 y viernes 12/06) · `OWNER:` TÚ · `LISTA:` diario S4 · `SALE:` —
**T114** · CHECK domingo 14/06: revisar métricas LinkedIn S4 (engagement del drop, DMs preguntando por el sistema, escuchas Spotify e iVoox 24h post-drop) · `OWNER:` TÚ · `LISTA:` 14/06/2026 · `SALE:` —

---

## SEMANA 5 — 15 a 19 junio 2026 (Fase 1 · Mantener tracción · T en consumo)

### Producción de contenido S5

**T115** · Redactar post S5 lunes (Recap T2 — discriminativa vs generativa) · `OWNER:` TÚ · `LISTA:` 14/06/2026 · `SALE:` 15/06/2026
**T116** · Diseñar quotable o infografía simple para post S5 lunes · `OWNER:` TÚ · `LISTA:` 14/06/2026 · `SALE:` 15/06/2026 · `DEP:` T011
**T117** · CHECK: pasar checklist style guide §6 a post S5 lunes · `OWNER:` TÚ · `LISTA:` 14/06/2026 · `SALE:` 15/06/2026 · `DEP:` T115
**T118** · Publicar post S5 lunes en LinkedIn · `OWNER:` TÚ · `LISTA:` 15/06/2026 09:00 · `SALE:` 15/06/2026 · `DEP:` T117
**T119** · Añadir enlace a Spotify e iVoox del T2 en primer comentario · `OWNER:` TÚ · `LISTA:` 15/06/2026 09:05 · `SALE:` 15/06/2026 · `DEP:` T118

**T120** · Redactar post S5 martes (Build-in-public — preparando M0 resumen para drop del 23/06) · `OWNER:` TÚ · `LISTA:` 15/06/2026 · `SALE:` 16/06/2026
**T121** · Preparar captura simple del proceso de generación del M para post S5 martes · `OWNER:` TÚ · `LISTA:` 15/06/2026 · `SALE:` 16/06/2026 · `DEP:` T013
**T122** · CHECK: pasar checklist style guide §6 a post S5 martes · `OWNER:` TÚ · `LISTA:` 15/06/2026 · `SALE:` 16/06/2026 · `DEP:` T120
**T123** · Publicar post S5 martes en LinkedIn · `OWNER:` TÚ · `LISTA:` 16/06/2026 09:00 · `SALE:` 16/06/2026 · `DEP:` T122

**T124** · Redactar post S5 jueves (Hot take "casos de uso" — empresas piden casos como en restaurante) · `OWNER:` TÚ · `LISTA:` 17/06/2026 · `SALE:` 18/06/2026
**T125** · CHECK: pasar checklist style guide §6 a post S5 jueves · `OWNER:` TÚ · `LISTA:` 17/06/2026 · `SALE:` 18/06/2026 · `DEP:` T124
**T126** · Publicar post S5 jueves en LinkedIn · `OWNER:` TÚ · `LISTA:` 18/06/2026 09:00 · `SALE:` 18/06/2026 · `DEP:` T125

**T127** · DECISIÓN viernes mañana: ¿post S5 viernes es Recap T3 (Opción A) o Personal Vallecas+saxo (Opción B)? Decidir según engagement de la semana · `OWNER:` TÚ · `LISTA:` 19/06/2026 09:00 · `SALE:` 19/06/2026
**T128** · Redactar post S5 viernes (según decisión T127) · `OWNER:` TÚ · `LISTA:` 18/06/2026 (borrador opción más probable) · `SALE:` 19/06/2026 · `DEP:` T127
**T129** · Diseñar visual (quotable si Opción A · foto personal si Opción B) · `OWNER:` TÚ · `LISTA:` 18/06/2026 · `SALE:` 19/06/2026 · `DEP:` T127
**T130** · CHECK: pasar checklist style guide §6 a post S5 viernes · `OWNER:` TÚ · `LISTA:` 19/06/2026 · `SALE:` 19/06/2026 · `DEP:` T128
**T131** · Publicar post S5 viernes en LinkedIn · `OWNER:` TÚ · `LISTA:` 19/06/2026 09:00 · `SALE:` 19/06/2026 · `DEP:` T130

### Preparación drop M0 (S6)

**T132** · CHECK M0 listo, escuchado y validado · `OWNER:` TÚ · `LISTA:` 19/06/2026 · `SALE:` — · `DEP:` T007
**T133** · Subir M0 a Spotify for Podcasters programado para 23/06 08:00 · `OWNER:` TÚ · `LISTA:` 19/06/2026 · `SALE:` 23/06/2026 08:00 · `DEP:` T005
**T134** · CHECK: verificar programación correcta del M0 en Spotify · `OWNER:` TÚ · `LISTA:` 20/06/2026 · `SALE:` — · `DEP:` T133
**T135** · Preparar archivo del M0 para subida manual a iVoox el 23/06 · `OWNER:` TÚ · `LISTA:` 21/06/2026 · `SALE:` 23/06/2026 · `DEP:` T005

### Comunidad y métricas S5

**T136** · Responder comentarios y DMs S5 (revisión diaria) · `OWNER:` TÚ · `LISTA:` diario S5 · `SALE:` —
**T137** · CHECK lunes 22/06: revisar métricas semanales LinkedIn S5 + escuchas acumuladas del M0 en Spotify e iVoox · `OWNER:` TÚ · `LISTA:` 22/06/2026 · `SALE:` —

---

## SEMANA 6 — 22 a 26 junio 2026 (Fase 1 · DROP del M0 resumen)

### Drop del M0 (martes 23/06)

**T138** · Redactar post S6 lunes (Build-in-public — M0 resumen listo, sale mañana) · `OWNER:` TÚ · `LISTA:` 21/06/2026 · `SALE:` 22/06/2026
**T139** · Preparar visual proceso/estructura del guion del M0 para post S6 lunes · `OWNER:` TÚ · `LISTA:` 21/06/2026 · `SALE:` 22/06/2026 · `DEP:` T013
**T140** · CHECK: pasar checklist style guide §6 a post S6 lunes · `OWNER:` TÚ · `LISTA:` 21/06/2026 · `SALE:` 22/06/2026 · `DEP:` T138
**T141** · Publicar post S6 lunes en LinkedIn · `OWNER:` TÚ · `LISTA:` 22/06/2026 09:00 · `SALE:` 22/06/2026 · `DEP:` T140

**T142** · 23/06 08:00 — CHECK: publicación automática del M0 en Spotify se ha disparado · `OWNER:` TÚ · `LISTA:` 23/06/2026 08:00 · `SALE:` 23/06/2026 08:00 · `DEP:` T133
**T143** · 23/06 08:15 — Subida manual del M0 a iVoox · `OWNER:` TÚ · `LISTA:` 23/06/2026 08:15 · `SALE:` 23/06/2026 08:15 · `DEP:` T135
**T144** · CHECK: verificar que el M0 es accesible en Spotify e iVoox a las 08:30 · `OWNER:` TÚ · `LISTA:` 23/06/2026 08:30 · `SALE:` — · `DEP:` T142, T143
**T145** · CHECK 12:00: verificar Apple Podcasts y Amazon Music vía RSS · `OWNER:` TÚ · `LISTA:` 23/06/2026 12:00 · `SALE:` — · `DEP:` T142

**T146** · Redactar post S6 martes 🔴 (ANUNCIO M0 — 17 minutos para el mapa completo antes del Módulo 1) · `OWNER:` TÚ · `LISTA:` 21/06/2026 · `SALE:` 23/06/2026
**T147** · Diseñar infografía estática 1080×1350 del M0 ("M0 — RESUMEN" + 6 T listados + tag APLICACION_PRACTICA destacado) · `OWNER:` TÚ · `LISTA:` 21/06/2026 · `SALE:` 23/06/2026 · `DEP:` T010
**T148** · CHECK: revisión doble del post S6 martes (pivote) · `OWNER:` TÚ · `LISTA:` 22/06/2026 · `SALE:` 23/06/2026 · `DEP:` T146, T147
**T149** · Publicar post S6 martes en LinkedIn 09:00 🔴 · `OWNER:` TÚ · `LISTA:` 23/06/2026 09:00 · `SALE:` 23/06/2026 · `DEP:` T148
**T150** · Añadir enlaces a Spotify e iVoox del M0 en primer comentario · `OWNER:` TÚ · `LISTA:` 23/06/2026 09:05 · `SALE:` 23/06/2026 · `DEP:` T149
**T151** · Atención intensiva a comentarios y DMs durante las primeras 4h del drop M0 · `OWNER:` TÚ · `LISTA:` 23/06/2026 13:00 · `SALE:` 23/06/2026 · `DEP:` T149

**T152** · Redactar post S6 jueves (Recap T1 — jerarquía IA-ML-DL-LLM) · `OWNER:` TÚ · `LISTA:` 24/06/2026 · `SALE:` 25/06/2026
**T153** · Diseñar quotable o infografía simple de jerarquía anidada para post S6 jueves · `OWNER:` TÚ · `LISTA:` 24/06/2026 · `SALE:` 25/06/2026 · `DEP:` T011
**T154** · CHECK: pasar checklist style guide §6 a post S6 jueves · `OWNER:` TÚ · `LISTA:` 24/06/2026 · `SALE:` 25/06/2026 · `DEP:` T152
**T155** · Publicar post S6 jueves en LinkedIn · `OWNER:` TÚ · `LISTA:` 25/06/2026 09:00 · `SALE:` 25/06/2026 · `DEP:` T154
**T156** · Añadir enlace a Spotify e iVoox del T1 en primer comentario · `OWNER:` TÚ · `LISTA:` 25/06/2026 09:05 · `SALE:` 25/06/2026 · `DEP:` T155

**T157** · Redactar post S6 viernes (Hot take factor humano — proyectos fracasan más por gestión del cambio) · `OWNER:` TÚ · `LISTA:` 25/06/2026 · `SALE:` 26/06/2026
**T158** · CHECK: pasar checklist style guide §6 a post S6 viernes · `OWNER:` TÚ · `LISTA:` 25/06/2026 · `SALE:` 26/06/2026 · `DEP:` T157
**T159** · Publicar post S6 viernes en LinkedIn · `OWNER:` TÚ · `LISTA:` 26/06/2026 09:00 · `SALE:` 26/06/2026 · `DEP:` T158

### Comunidad y métricas S6

**T160** · Responder comentarios y DMs S6 · `OWNER:` TÚ · `LISTA:` diario S6 · `SALE:` —
**T161** · CHECK domingo 28/06: revisar métricas LinkedIn S6 (especialmente del drop M0) + escuchas acumuladas M0 · `OWNER:` TÚ · `LISTA:` 28/06/2026 · `SALE:` —

---

## SEMANA 7 — 29 junio a 3 julio 2026 (Cierre Módulo 0 + transición M1)

### Producción de contenido S7

**T162** · Redactar post S7 lunes (Recap T4 — capacidades y limitaciones, alucinaciones) · `OWNER:` TÚ · `LISTA:` 28/06/2026 · `SALE:` 29/06/2026
**T163** · Diseñar quotable para post S7 lunes · `OWNER:` TÚ · `LISTA:` 28/06/2026 · `SALE:` 29/06/2026 · `DEP:` T011
**T164** · CHECK: pasar checklist style guide §6 a post S7 lunes · `OWNER:` TÚ · `LISTA:` 28/06/2026 · `SALE:` 29/06/2026 · `DEP:` T162
**T165** · Publicar post S7 lunes en LinkedIn · `OWNER:` TÚ · `LISTA:` 29/06/2026 09:00 · `SALE:` 29/06/2026 · `DEP:` T164
**T166** · Añadir enlace a Spotify e iVoox del T4 en primer comentario · `OWNER:` TÚ · `LISTA:` 29/06/2026 09:05 · `SALE:` 29/06/2026 · `DEP:` T165

**T167** · Redactar post S7 miércoles (Build-in-public preparando M1 — 12 T del módulo Fundamentos del razonamiento) · `OWNER:` TÚ · `LISTA:` 30/06/2026 · `SALE:` 01/07/2026
**T168** · Preparar visual estructura temario M1 para post S7 miércoles · `OWNER:` TÚ · `LISTA:` 30/06/2026 · `SALE:` 01/07/2026 · `DEP:` T013
**T169** · CHECK: pasar checklist style guide §6 a post S7 miércoles · `OWNER:` TÚ · `LISTA:` 30/06/2026 · `SALE:` 01/07/2026 · `DEP:` T167
**T170** · Publicar post S7 miércoles en LinkedIn · `OWNER:` TÚ · `LISTA:` 01/07/2026 09:00 · `SALE:` 01/07/2026 · `DEP:` T169

**T171** · Redactar post S7 jueves (Recap T5 — casos de uso por sector, huecos del mapa) · `OWNER:` TÚ · `LISTA:` 01/07/2026 · `SALE:` 02/07/2026
**T172** · Diseñar quotable para post S7 jueves · `OWNER:` TÚ · `LISTA:` 01/07/2026 · `SALE:` 02/07/2026 · `DEP:` T011
**T173** · CHECK: pasar checklist style guide §6 a post S7 jueves · `OWNER:` TÚ · `LISTA:` 01/07/2026 · `SALE:` 02/07/2026 · `DEP:` T171
**T174** · Publicar post S7 jueves en LinkedIn · `OWNER:` TÚ · `LISTA:` 02/07/2026 09:00 · `SALE:` 02/07/2026 · `DEP:` T173
**T175** · Añadir enlace a Spotify e iVoox del T5 en primer comentario · `OWNER:` TÚ · `LISTA:` 02/07/2026 09:05 · `SALE:` 02/07/2026 · `DEP:` T174

**T176** · DECISIÓN viernes mañana: ¿post S7 viernes es Cierre del módulo (Opción A) o Personal Vallecas+saxo (Opción B)? · `OWNER:` TÚ · `LISTA:` 03/07/2026 09:00 · `SALE:` 03/07/2026
**T177** · Redactar post S7 viernes (según decisión T176) · `OWNER:` TÚ · `LISTA:` 02/07/2026 · `SALE:` 03/07/2026 · `DEP:` T176
**T178** · Diseñar visual mínimo (foto personal si Opción B) · `OWNER:` TÚ · `LISTA:` 02/07/2026 · `SALE:` 03/07/2026 · `DEP:` T176
**T179** · CHECK: pasar checklist style guide §6 a post S7 viernes · `OWNER:` TÚ · `LISTA:` 02/07/2026 · `SALE:` 03/07/2026 · `DEP:` T177
**T180** · Publicar post S7 viernes en LinkedIn · `OWNER:` TÚ · `LISTA:` 03/07/2026 09:00 · `SALE:` 03/07/2026 · `DEP:` T179

### Cierre Módulo 0 y preparación M1

**T181** · Balance del Módulo 0: revisar métricas totales de escuchas, engagement LinkedIn, DMs cualitativos, feedback prelist · `OWNER:` TÚ · `LISTA:` 05/07/2026 · `SALE:` — · `DEP:` T076
**T182** · Generación de los 12 T del Módulo 1 (audio final) · `OWNER:` MIXTO · `LISTA:` 05/07/2026 · `SALE:` 07/07/2026 · `DEP:` T001-T003
**T183** · CHECK: escucha completa de los 12 T del M1 (validación calidad, ritmo, contenido) · `OWNER:` TÚ · `LISTA:` 06/07/2026 · `SALE:` — · `DEP:` T182
**T184** · Subir los 12 T del M1 a Spotify for Podcasters programados para 07/07 08:00 · `OWNER:` TÚ · `LISTA:` 06/07/2026 · `SALE:` 07/07/2026 08:00 · `DEP:` T182, T183
**T185** · CHECK: verificar programación correcta de los 12 T del M1 en Spotify (títulos, descripciones, fecha) · `OWNER:` TÚ · `LISTA:` 06/07/2026 · `SALE:` — · `DEP:` T184
**T186** · Preparar archivos de los 12 T del M1 para subida manual a iVoox el 07/07 · `OWNER:` TÚ · `LISTA:` 06/07/2026 · `SALE:` 07/07/2026 · `DEP:` T182

### Comunidad y métricas S7

**T187** · Responder comentarios y DMs S7 · `OWNER:` TÚ · `LISTA:` diario S7 · `SALE:` —

---

## SEMANA 8 — 6 a 10 julio 2026 (Fase 1 · DROP Módulo 1)

### Drop del Módulo 1 (martes 07/07)

**T188** · Redactar post S8 lunes (Build-in-public pre-drop M1 — generar 12 T es distinto a generar 6) · `OWNER:` TÚ · `LISTA:` 05/07/2026 · `SALE:` 06/07/2026
**T189** · Preparar visual relacionado con M1 (estructura temario o captura del proceso) · `OWNER:` TÚ · `LISTA:` 05/07/2026 · `SALE:` 06/07/2026 · `DEP:` T013
**T190** · CHECK: pasar checklist style guide §6 a post S8 lunes · `OWNER:` TÚ · `LISTA:` 05/07/2026 · `SALE:` 06/07/2026 · `DEP:` T188
**T191** · Publicar post S8 lunes en LinkedIn · `OWNER:` TÚ · `LISTA:` 06/07/2026 09:00 · `SALE:` 06/07/2026 · `DEP:` T190

**T192** · Lista de 5-10 contactos para DM previo al drop M1 (pedir comentar en primera hora) · `OWNER:` TÚ · `LISTA:` 06/07/2026 · `SALE:` —
**T193** · Enviar DM previo a contactos T192 avisando del drop M1 · `OWNER:` TÚ · `LISTA:` 06/07/2026 · `SALE:` 07/07/2026 · `DEP:` T192

**T194** · 07/07 08:00 — CHECK: publicación automática de los 12 T del M1 en Spotify · `OWNER:` TÚ · `LISTA:` 07/07/2026 08:00 · `SALE:` 07/07/2026 08:00 · `DEP:` T184
**T195** · 07/07 08:15 — Subida manual de los 12 T del M1 a iVoox · `OWNER:` TÚ · `LISTA:` 07/07/2026 08:15 · `SALE:` 07/07/2026 08:15 · `DEP:` T186
**T196** · CHECK: verificar accesibilidad de los 12 T del M1 en Spotify e iVoox a las 08:30 · `OWNER:` TÚ · `LISTA:` 07/07/2026 08:30 · `SALE:` — · `DEP:` T194, T195
**T197** · CHECK 12:00: verificar Apple Podcasts y Amazon Music vía RSS · `OWNER:` TÚ · `LISTA:` 07/07/2026 12:00 · `SALE:` — · `DEP:` T194

**T198** · Redactar post S8 martes 🔴 (ANUNCIO DROP M1 — Módulo 1: Fundamentos del razonamiento, 12 episodios) · `OWNER:` TÚ · `LISTA:` 05/07/2026 · `SALE:` 07/07/2026
**T199** · Diseñar infografía-índice del M1 (1080×1350, "MÓDULO 1 — FUNDAMENTOS DEL RAZONAMIENTO" + 12 títulos T en monospace) · `OWNER:` TÚ · `LISTA:` 06/07/2026 · `SALE:` 07/07/2026 · `DEP:` T010
**T200** · CHECK: revisión doble post S8 martes + squint test infografía · `OWNER:` TÚ · `LISTA:` 06/07/2026 · `SALE:` 07/07/2026 · `DEP:` T198, T199
**T201** · Publicar post S8 martes en LinkedIn 09:00 🔴 · `OWNER:` TÚ · `LISTA:` 07/07/2026 09:00 · `SALE:` 07/07/2026 · `DEP:` T200
**T202** · Añadir enlaces a Spotify e iVoox del M1 (índice del módulo) en primer comentario · `OWNER:` TÚ · `LISTA:` 07/07/2026 09:05 · `SALE:` 07/07/2026 · `DEP:` T201
**T203** · Atención intensiva a comentarios y DMs durante las primeras 4h · `OWNER:` TÚ · `LISTA:` 07/07/2026 13:00 · `SALE:` 07/07/2026 · `DEP:` T201

**T204** · Redactar post S8 jueves (Recap de un T del M1 — a decidir el T más linkeable según los 12 disponibles, ej. T12 Razonamiento de modelos si conecta con la economía del razonamiento) · `OWNER:` TÚ · `LISTA:` 08/07/2026 · `SALE:` 09/07/2026
**T205** · Diseñar quotable o infografía para post S8 jueves · `OWNER:` TÚ · `LISTA:` 08/07/2026 · `SALE:` 09/07/2026 · `DEP:` T011
**T206** · CHECK: pasar checklist style guide §6 a post S8 jueves · `OWNER:` TÚ · `LISTA:` 08/07/2026 · `SALE:` 09/07/2026 · `DEP:` T204
**T207** · Publicar post S8 jueves en LinkedIn · `OWNER:` TÚ · `LISTA:` 09/07/2026 09:00 · `SALE:` 09/07/2026 · `DEP:` T206
**T208** · Añadir enlace a Spotify e iVoox del T del M1 elegido en primer comentario · `OWNER:` TÚ · `LISTA:` 09/07/2026 09:05 · `SALE:` 09/07/2026 · `DEP:` T207

**T209** · DECISIÓN: ¿post S8 viernes es Build-in-public del M1 o Hot take técnica? (la cadencia del M1 con 6 semanas permite holgura, no hay obligación de recap el viernes) · `OWNER:` TÚ · `LISTA:` 09/07/2026 · `SALE:` 10/07/2026
**T210** · Redactar post S8 viernes según T209 · `OWNER:` TÚ · `LISTA:` 09/07/2026 · `SALE:` 10/07/2026 · `DEP:` T209
**T211** · Visual asociado al post S8 viernes · `OWNER:` TÚ · `LISTA:` 09/07/2026 · `SALE:` 10/07/2026 · `DEP:` T209
**T212** · CHECK: pasar checklist style guide §6 a post S8 viernes · `OWNER:` TÚ · `LISTA:` 09/07/2026 · `SALE:` 10/07/2026 · `DEP:` T210
**T213** · Publicar post S8 viernes en LinkedIn · `OWNER:` TÚ · `LISTA:` 10/07/2026 09:00 · `SALE:` 10/07/2026 · `DEP:` T212

### Comunidad y métricas S8

**T214** · Responder comentarios y DMs S8 (especial atención martes 07/07 por drop M1) · `OWNER:` TÚ · `LISTA:` diario S8 · `SALE:` —
**T215** · CHECK domingo 12/07: revisar métricas drop M1 (¿es mejor que el M0? ¿peor? ¿por qué?) · `OWNER:` TÚ · `LISTA:` 12/07/2026 · `SALE:` —

---

## SEMANA 9 — 13 a 17 julio 2026 (Fase 1 · M1 en consumo · Semana 2 del ciclo M1)

### Producción de contenido S9

**T216** · Redactar post S9 lunes (Recap de un segundo T del M1 — elegir según el feedback de la semana anterior, posible: T2 IA simbólica, T3 IA conexionista, o T7 Representación del conocimiento) · `OWNER:` TÚ · `LISTA:` 12/07/2026 · `SALE:` 13/07/2026
**T217** · Diseñar quotable para post S9 lunes · `OWNER:` TÚ · `LISTA:` 12/07/2026 · `SALE:` 13/07/2026 · `DEP:` T011
**T218** · CHECK: pasar checklist style guide §6 a post S9 lunes · `OWNER:` TÚ · `LISTA:` 12/07/2026 · `SALE:` 13/07/2026 · `DEP:` T216
**T219** · Publicar post S9 lunes en LinkedIn · `OWNER:` TÚ · `LISTA:` 13/07/2026 09:00 · `SALE:` 13/07/2026 · `DEP:` T218
**T220** · Añadir enlace a Spotify e iVoox del T elegido en primer comentario · `OWNER:` TÚ · `LISTA:` 13/07/2026 09:05 · `SALE:` 13/07/2026 · `DEP:` T219

**T221** · Redactar post S9 martes (Build-in-public — algo concreto del proceso de M1, ej. cómo cambia el guion con 12 T vs 6 T) · `OWNER:` TÚ · `LISTA:` 13/07/2026 · `SALE:` 14/07/2026
**T222** · Preparar captura para post S9 martes · `OWNER:` TÚ · `LISTA:` 13/07/2026 · `SALE:` 14/07/2026 · `DEP:` T013
**T223** · CHECK: pasar checklist style guide §6 a post S9 martes · `OWNER:` TÚ · `LISTA:` 13/07/2026 · `SALE:` 14/07/2026 · `DEP:` T221
**T224** · Publicar post S9 martes en LinkedIn · `OWNER:` TÚ · `LISTA:` 14/07/2026 09:00 · `SALE:` 14/07/2026 · `DEP:` T223

**T225** · Redactar post S9 jueves (Hot take técnica del M1 — algo que el M1 cubre y contradice creencia popular, ej. "los LLM no razonan, predicen el siguiente token") · `OWNER:` TÚ · `LISTA:` 15/07/2026 · `SALE:` 16/07/2026
**T226** · CHECK: pasar checklist style guide §6 a post S9 jueves · `OWNER:` TÚ · `LISTA:` 15/07/2026 · `SALE:` 16/07/2026 · `DEP:` T225
**T227** · Publicar post S9 jueves en LinkedIn · `OWNER:` TÚ · `LISTA:` 16/07/2026 09:00 · `SALE:` 16/07/2026 · `DEP:` T226

**T228** · DECISIÓN: ¿post S9 viernes es Recap de un tercer T del M1 o Infografía didáctica (carrusel)? · `OWNER:` TÚ · `LISTA:` 16/07/2026 · `SALE:` 17/07/2026
**T229** · Redactar post S9 viernes según T228 · `OWNER:` TÚ · `LISTA:` 16/07/2026 · `SALE:` 17/07/2026 · `DEP:` T228
**T230** · Diseñar visual asociado · `OWNER:` TÚ · `LISTA:` 16/07/2026 · `SALE:` 17/07/2026 · `DEP:` T228
**T231** · CHECK: pasar checklist style guide §6 a post S9 viernes · `OWNER:` TÚ · `LISTA:` 16/07/2026 · `SALE:` 17/07/2026 · `DEP:` T229
**T232** · Publicar post S9 viernes en LinkedIn · `OWNER:` TÚ · `LISTA:` 17/07/2026 09:00 · `SALE:` 17/07/2026 · `DEP:` T231

### Preparación drop M1 resumen (semana 10 — fuera del scope de este listado, pero arranca aquí)

**T233** · Generación del M1 resumen + bloque APLICACION_PRACTICA (audio final) · `OWNER:` MIXTO · `LISTA:` 17/07/2026 · `SALE:` 21/07/2026 · `DEP:` T182
**T234** · CHECK: escucha completa del M1 resumen · `OWNER:` TÚ · `LISTA:` 19/07/2026 · `SALE:` — · `DEP:` T233

### Comunidad y métricas S9

**T235** · Responder comentarios y DMs S9 · `OWNER:` TÚ · `LISTA:` diario S9 · `SALE:` —
**T236** · CHECK domingo 19/07: balance global de las 9 primeras semanas. Métricas, DMs cualitativos, ajustes necesarios para el resto del M1 y siguientes módulos · `OWNER:` TÚ · `LISTA:` 19/07/2026 · `SALE:` —
