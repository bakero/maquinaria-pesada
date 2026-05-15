"""In-app help registry.

Each page declares help content here. The help dialog is invoked from
``cockpit.ui_components.help_button`` next to the page header.

The shape is simple data so we can render uniformly. Add new entries by
appending to ``HELP``; don't import this from non-UI code.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HelpSection:
    title: str
    body: str  # markdown


@dataclass(frozen=True)
class HelpPage:
    page_id: str
    title: str
    summary: str           # one-paragraph elevator pitch
    sections: list[HelpSection] = field(default_factory=list)
    related: list[tuple[str, str]] = field(default_factory=list)
    # (label, target_path) — used to render quick navigation links


HELP: dict[str, HelpPage] = {
    "home": HelpPage(
        page_id="home",
        title="Cómo funciona el cockpit",
        summary=(
            "El cockpit es el centro de control de MaquinarIA Pesada. "
            "Desde aquí lanzas pipelines, inspeccionas contenido producido, "
            "controlas el gasto de IA y conversas con Claude. Las páginas "
            "están agrupadas en seis secciones lógicas en la barra lateral."
        ),
        sections=[
            HelpSection(
                "Flujo típico de trabajo",
                "1. **Master** — ver el estado global del curso (M0-M14).  \n"
                "2. **Módulo** — entrar a un módulo concreto y ver sus episodios.  \n"
                "3. **Episodio** — abrir un episodio, ver guion/PDF/audio.  \n"
                "4. Si falta contenido → lanzar el pipeline desde la propia "
                "página del episodio (no hace falta ir al lanzador genérico).  \n"
                "5. Si hay errores → botón **Arreglar con Claude** abre una "
                "sesión IA con el contexto del episodio.",
            ),
            HelpSection(
                "Sandbox de IA",
                "Las sesiones de Claude lanzadas desde la app solo pueden "
                "modificar contenido generado (`Guiones/`, `episodios/`, "
                "`escaletas/`, etc.) y el mapa de componentes. **Nunca** "
                "tocan el código del cockpit ni los pipelines top-level. "
                "Esto está enforced en `cockpit/core/sandbox.py`.",
            ),
            HelpSection(
                "Cómo encuentro algo concreto",
                "- **¿Qué episodios faltan?** → Master.  \n"
                "- **¿Por qué falló esa generación?** → Episodio → tab Logs.  \n"
                "- **¿Cuánto he gastado en IA?** → Coste IA → Economics.  \n"
                "- **¿Qué pipelines hay?** → Lanzar pipeline o Conectores.  \n"
                "- **Configurar claves API** → Sistema → API Keys.",
            ),
        ],
        related=[
            ("Master", "pages/0_🎓_Master.py"),
            ("Lanzar pipeline", "pages/3_📝_Generar_Prompt.py"),
            ("API Keys", "pages/6_🔑_API_Keys.py"),
        ],
    ),
    "master": HelpPage(
        page_id="master",
        title="Master · estado por módulo",
        summary=(
            "Vista global del curso. Cada módulo M0-M14 muestra un semáforo "
            "(🟢 listo / 🟡 en curso / ⚪ sin empezar) y un porcentaje de "
            "completitud. Un módulo está «listo» cuando todos sus episodios "
            "(M principal + temas Tₙ) tienen los 4 contenidos: guion, PDF, "
            "escaleta y audio."
        ),
        sections=[
            HelpSection(
                "Acciones disponibles",
                "- **Abrir →** entra al detalle del módulo (lista de episodios).  \n"
                "- **▶ Producir pendientes** (si configurado) lanza "
                "`produce_pending.py` para ese módulo, que genera los "
                "guiones faltantes en lote.",
            ),
            HelpSection(
                "Cómo se calcula el progreso",
                "Para cada episodio cuenta cuántos de los 4 contenidos están "
                "presentes en disco (PDF, guion, escaleta, audio). El "
                "progreso del módulo es la media de progresos de sus "
                "episodios.",
            ),
        ],
        related=[
            ("Estado", "pages/1_📊_Estado.py"),
            ("Lanzar pipeline", "pages/3_📝_Generar_Prompt.py"),
        ],
    ),
    "modulo": HelpPage(
        page_id="modulo",
        title="Módulo · listado de episodios",
        summary=(
            "Detalle de un módulo Mₙ con todos sus episodios. Cada episodio "
            "muestra pills de los contenidos producidos y un indicador de "
            "errores. Las acciones contextuales aparecen junto a cada "
            "episodio según su estado."
        ),
        sections=[
            HelpSection(
                "Tipos de episodio",
                "- **M (Módulo)**: episodio largo (≈ 30 min) que cubre el "
                "tema completo del módulo. Generado con `generar_guion.py`.  \n"
                "- **Tₖ (Tema)**: episodios cortos (≈ 12-15 min) por sub-tema. "
                "Generados con `generar_guion_t.py`.",
            ),
            HelpSection(
                "Pills de contenido",
                "- 🟢 verde = contenido presente.  \n"
                "- ⚪ gris = contenido faltante.  \n"
                "El orden esperado es: PDF → Guion → Escaleta → Audio.",
            ),
        ],
        related=[
            ("Master", "pages/0_🎓_Master.py"),
            ("Lanzar pipeline", "pages/3_📝_Generar_Prompt.py"),
        ],
    ),
    "episodio": HelpPage(
        page_id="episodio",
        title="Episodio · control completo",
        summary=(
            "Centro de operaciones de un episodio. Aquí ves su guion, PDF "
            "fuente, escaleta, audio y logs en pestañas separadas, además de "
            "las verificaciones automáticas. La **action bar** superior "
            "muestra solo las acciones disponibles según el estado actual."
        ),
        sections=[
            HelpSection(
                "Action bar contextual",
                "Las acciones aparecen según lo que falta:  \n"
                "- **▶ Generar guion** — si no hay guion en disco.  \n"
                "- **▶ Generar audio** — si hay guion pero no hay audio.  \n"
                "- **✅ Validar** — si hay audio (ejecuta `validar_episodio.py`).  \n"
                "- **🛠️ Arreglar con Claude** — si hay errores de verificación.  \n"
                "- **⬇️ Descargar** — desde cada pestaña.",
            ),
            HelpSection(
                "Pestañas",
                "- **📝 Guion** — texto plano con highlight markdown.  \n"
                "- **📕 PDF** — visor inline + descarga.  \n"
                "- **🗂️ Escaleta** — guion estructurado en bloques.  \n"
                "- **🎧 Audio** — player + tamaño.  \n"
                "- **📜 Logs** — todos los logs de producción.  \n"
                "- **✅ Verificaciones** — chequeos automáticos con ✅/⚠️/❌.",
            ),
            HelpSection(
                "Sesión Claude para arreglar errores",
                "El botón **🛠️ Arreglar con Claude** abre un modal con: el "
                "listado de errores, el estado de archivos, los logs "
                "relevantes y un bloque de mejora con prompt pre-rellenado. "
                "Lanza una sesión Claude (sandbox aplicado) que propone un "
                "fix. Si requiere regenerar, indica el comando exacto.",
            ),
        ],
        related=[
            ("Módulo", "pages/13_🎬_Modulo.py"),
            ("Logs", "pages/5_📜_Logs.py"),
        ],
    ),
    "estado": HelpPage(
        page_id="estado",
        title="Estado de producción",
        summary=(
            "Tabla cruzada Módulo × Tipo-de-contenido. Cada celda es ✅ si "
            "el contenido existe en disco y ❌ si no. Pulsar una celda abre "
            "el resumen de la última ejecución (logs, errores, warnings) "
            "para ese módulo/categoría."
        ),
        sections=[
            HelpSection(
                "Diferencia con Master",
                "**Master** muestra una vista sintética por módulo (semáforo + %). "
                "**Estado** muestra el detalle por tipo de contenido — útil "
                "cuando solo falta el audio o solo el vídeo y necesitas ver "
                "exactamente dónde.",
            ),
        ],
        related=[
            ("Master", "pages/0_🎓_Master.py"),
            ("Logs", "pages/5_📜_Logs.py"),
        ],
    ),
    "lanzador": HelpPage(
        page_id="lanzador",
        title="Lanzar pipeline",
        summary=(
            "Selecciona un pipeline registrado, rellena el formulario y "
            "lánzalo desde el cockpit con logs en vivo. Puedes generar el "
            "comando equivalente para Codex (copy-paste) si prefieres "
            "ejecutarlo manualmente en otra terminal."
        ),
        sections=[
            HelpSection(
                "Pipelines disponibles",
                "El selector lista todos los pipelines registrados en "
                "`cockpit/connectors/pipelines/`. Cada uno declara sus "
                "flags y su script. Para añadir uno nuevo, crea un fichero "
                "en esa carpeta heredando de `PipelineConnector`.",
            ),
            HelpSection(
                "Ejecución vs. comando para Codex",
                "El bloque **Generar comando** crea el comando bash con "
                "todos los flags, listo para pegar en Codex u otra terminal.  \n"
                "El bloque **Ejecutar** lanza el pipeline desde aquí con "
                "streaming de stdout. Necesita las API keys configuradas.",
            ),
            HelpSection(
                "Pre-fill desde otras páginas",
                "Otras páginas (Episodio, Módulo) lanzan pipelines con los "
                "valores pre-rellenados — no hace falta entrar a esta página. "
                "Esta vista es para casos avanzados o pipelines sin contexto "
                "de episodio.",
            ),
        ],
        related=[
            ("Conectores", "pages/2_🔌_Conectores.py"),
            ("Episodio", "pages/14_📼_Episodio.py"),
        ],
    ),
    "fuentes": HelpPage(
        page_id="fuentes",
        title="Fuentes",
        summary=(
            "Explora los PDFs fuente del repo agrupados en `auxiliares/`, "
            "`resumenes/` y `temas/`. Los resúmenes alimentan los guiones M "
            "(módulos completos); los PDFs de `temas/` alimentan los "
            "guiones T (sub-temas)."
        ),
    ),
    "logs": HelpPage(
        page_id="logs",
        title="Logs",
        summary=(
            "Listado de logs de producción del repo. Pulsa para ver el "
            "contenido. Los logs incluyen comandos ejecutados, salidas de "
            "TTS/ElevenLabs, errores y trazas de Claude."
        ),
    ),
    "api_keys": HelpPage(
        page_id="api_keys",
        title="API Keys",
        summary=(
            "Estado de las claves API requeridas por los servicios: "
            "Anthropic (Claude), OpenAI (debate dual), ElevenLabs (TTS), "
            "Kling (vídeo). Las claves se cargan desde `.env`. Esta página "
            "**no** muestra ni edita las claves — solo indica presencia."
        ),
    ),
    "tokens": HelpPage(
        page_id="tokens",
        title="Coste IA · Tokens",
        summary=(
            "Cuántos tokens has consumido por modelo. Los datos vienen de "
            "`logs/ai_usage.jsonl`, que se llena automáticamente por cada "
            "llamada IA que pase por `cockpit/core/ai_client.py`."
        ),
    ),
    "economics": HelpPage(
        page_id="economics",
        title="Coste IA · Economics",
        summary=(
            "Vista económica: gasto histórico, gasto por episodio, "
            "tendencias. Los datos vienen de `logs/economics.json`."
        ),
    ),
    "optimizar": HelpPage(
        page_id="optimizar",
        title="Optimizar coste IA",
        summary=(
            "Advisor automático que detecta patrones costosos (Opus para "
            "tareas que Sonnet resuelve, contexto inflado, llamadas "
            "redundantes) y propone sustituciones que ahorran factura sin "
            "perder calidad."
        ),
    ),
    "previsualizar": HelpPage(
        page_id="previsualizar",
        title="Previsualizar episodio",
        summary=(
            "Player de audio + guion sincronizado. Para escuchar un episodio "
            "junto a su guion en una sola pantalla, sin distracciones."
        ),
    ),
    "asistente": HelpPage(
        page_id="asistente",
        title="Asistente Claude",
        summary=(
            "Conversación libre con Claude para preguntar sobre el sistema, "
            "pedir diagnósticos o ayuda con tareas. Las acciones que "
            "modifican ficheros respetan el sandbox."
        ),
    ),
    "conectores": HelpPage(
        page_id="conectores",
        title="Conectores",
        summary=(
            "Mapa completo de servicios, pipelines y fuentes registrados en "
            "`cockpit/connectors/`. Sirve como referencia técnica de la "
            "arquitectura. Para usar un pipeline, ve a **Lanzar pipeline** o "
            "lánzalo desde la página del Episodio."
        ),
    ),
    "mapa": HelpPage(
        page_id="mapa",
        title="Mapa de componentes",
        summary=(
            "Grafo del sistema: módulos, ficheros, dependencias. Útil para "
            "entender la arquitectura de un vistazo. El mapa vive en "
            "`cockpit/components_map.json` y puede ser editado por Claude."
        ),
    ),
    "pizarra": HelpPage(
        page_id="pizarra",
        title="Pizarra",
        summary=(
            "Notas libres en markdown. Para anotar ideas, decisiones, "
            "TODOs. Se guardan en `pizarra/` del repo."
        ),
    ),
    "rendimiento": HelpPage(
        page_id="rendimiento",
        title="Rendimiento · difusión",
        summary=(
            "KPIs de difusión: escuchas en Spotify, iVoox, vistas en "
            "LinkedIn. Datos extraídos de los analytics connectors."
        ),
    ),
}


def get(page_id: str) -> HelpPage | None:
    return HELP.get(page_id)
