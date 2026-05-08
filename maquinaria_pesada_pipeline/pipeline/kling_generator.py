"""
Generador de escenas con Kling 1.6 Pro via fal.ai.

Por que Kling y no Luma:
  - Mantiene mucho mejor la consistencia facial cuando se usa una imagen
    como frame0 (image-to-video). Luma alucinaba al segundo presentador
    (en planos de Yago aparecia una mujer que no era Maria).
  - Soporta clips de 5s y 10s nativos.

Coste aproximado (fal.ai 2026):
  - Kling 1.6 Pro 5s:  ~$0.45/clip
  - Kling 1.6 Pro 10s: ~$0.90/clip

API:
  Endpoint: https://queue.fal.run/fal-ai/kling-video/v1.6/pro/image-to-video
  Auth:     Authorization: Key <FAL_KEY>
  Body:     {prompt, image_url, duration ("5"|"10"), aspect_ratio ("16:9"),
             negative_prompt, cfg_scale}

Devuelve un job en cola; hay que poner-poll hasta status=COMPLETED y
luego descargar response.video.url.

Uso:
    from pipeline.kling_generator import KlingGenerator
    g = KlingGenerator(library)
    g.generate_concept(slug="studio_maria_speaking_v1",
                       prompt="...", image_url="...",
                       duration=10, category="estudio")
"""

import os
import time
from pathlib import Path

from .logger import get_logger
from .scene_library import SceneLibrary, _slugify

KLING_QUEUE = "https://queue.fal.run/fal-ai/kling-video/v1.6/pro/image-to-video"

# Negative prompt comun para evitar problemas tipicos en planos de podcast
DEFAULT_NEGATIVE = (
    "blurry, low quality, distorted face, extra fingers, extra limbs, "
    "mutated hands, deformed, additional people, second person appearing, "
    "duplicate person, cartoon, anime, watermark, logo, text overlay, "
    "subtitle, brand name, CAT logo, lip sync error, mouth not matching, "
    "frozen face, robotic motion"
)


class KlingGenerator:
    def __init__(self, library: SceneLibrary,
                 api_key: str | None = None,
                 default_aspect: str = "16:9"):
        self.library = library
        self.api_key = api_key or os.getenv("FAL_KEY") or os.getenv("KLING_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "FAL_KEY no definida. Anadela a .env: FAL_KEY=fal_xxx... "
                "(obtener en https://fal.ai/dashboard/keys)"
            )
        self.default_aspect = default_aspect
        self.log = get_logger("kling_generator")
        self._http_session = None

    @property
    def http(self):
        if self._http_session is None:
            try:
                import requests
            except ImportError as exc:
                raise RuntimeError(
                    "Falta el paquete 'requests'. pip install requests"
                ) from exc
            s = requests.Session()
            s.headers.update({
                "Authorization": f"Key {self.api_key}",
                "Accept":        "application/json",
                "Content-Type":  "application/json",
            })
            self._http_session = s
        return self._http_session

    # ── API ─────────────────────────────────────────────────────────

    def _submit(self, prompt: str, image_url: str,
                duration: int = 10,
                aspect_ratio: str | None = None,
                negative_prompt: str | None = None,
                cfg_scale: float = 0.5) -> dict:
        """POST al endpoint de cola. Devuelve {request_id, status_url, response_url}."""
        if duration not in (5, 10):
            self.log.warning(f"  duration={duration} no soportado por Kling 1.6 Pro; "
                             f"forzando a 10s")
            duration = 10
        payload = {
            "prompt":          prompt,
            "image_url":       image_url,
            "duration":        str(duration),
            "aspect_ratio":    aspect_ratio or self.default_aspect,
            "negative_prompt": negative_prompt or DEFAULT_NEGATIVE,
            "cfg_scale":       cfg_scale,
        }
        r = self.http.post(KLING_QUEUE, json=payload, timeout=60)
        if r.status_code >= 400:
            self.log.error(f"  Kling/fal {r.status_code}: {r.text[:500]}")
        r.raise_for_status()
        return r.json()

    def _poll(self, status_url: str, max_seconds: int = 900,
              poll: int = 8) -> dict:
        """Espera a que el job termine. fal.ai suele tardar 60-180s en Kling Pro 10s."""
        elapsed = 0
        while elapsed < max_seconds:
            r = self.http.get(status_url, timeout=30)
            r.raise_for_status()
            data = r.json()
            status = (data.get("status") or "").upper()
            self.log.debug(f"  Kling status={status}")
            if status == "COMPLETED":
                return data
            if status in ("FAILED", "CANCELED", "ERROR"):
                raise RuntimeError(f"Kling job fallo: {data}")
            time.sleep(poll)
            elapsed += poll
        raise TimeoutError(f"Kling timeout tras {max_seconds}s")

    def _fetch_response(self, response_url: str) -> dict:
        """Cuando el job esta COMPLETED, recupera la respuesta con video.url."""
        r = self.http.get(response_url, timeout=30)
        r.raise_for_status()
        return r.json()

    def _download_video(self, url: str, dest: Path) -> Path:
        import requests
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, stream=True, timeout=180) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 15):
                    if chunk:
                        f.write(chunk)
        return dest

    # ── flujo de alto nivel ─────────────────────────────────────────

    def generate_concept(self, slug: str, prompt: str,
                         image_url: str,
                         duration: int = 10,
                         aspect_ratio: str | None = None,
                         category: str = "estudio",
                         modulo: str | None = None,
                         tags: list[str] | None = None,
                         description: str = "",
                         negative_prompt: str | None = None,
                         force: bool = False) -> dict:
        slug = _slugify(slug)
        existing = self.library.find(slug)
        if existing and not force:
            self.log.info(f"  Reutilizando escena cacheada: {slug}")
            return existing

        self.log.info(f"  Generando con Kling 1.6 Pro: {slug} ({duration}s)")
        self.log.info(f"    prompt: {prompt[:100]}{'...' if len(prompt)>100 else ''}")
        self.log.info(f"    image:  {image_url}")

        # 1) Submit
        sub = self._submit(prompt, image_url, duration, aspect_ratio,
                           negative_prompt=negative_prompt)
        status_url = sub.get("status_url")
        response_url = sub.get("response_url")
        if not status_url or not response_url:
            raise RuntimeError(f"Respuesta fal sin URLs: {sub}")

        # 2) Poll
        self._poll(status_url)

        # 3) Fetch resultado
        result = self._fetch_response(response_url)
        video_url = (result.get("video") or {}).get("url")
        if not video_url:
            raise RuntimeError(f"Resultado Kling sin video.url: {result}")

        # 4) Descargar
        dest = self.library.base / category / f"{slug}.mp4"
        self._download_video(video_url, dest)
        self.log.info(f"    descargado: {dest}")

        # 5) Registrar
        scene = self.library.register(
            slug=slug, path=dest,
            category=category, prompt=prompt,
            description=description,
            tags=tags or [], modulo=modulo,
            source="kling-1.6-pro",
        )
        return scene

    def generate_batch(self, items: list[dict],
                       delay_seconds: float = 3.0) -> dict:
        results = {"generated": [], "errors": [], "skipped": []}
        for it in items:
            slug = _slugify(it.get("slug") or "")
            if not slug or not it.get("prompt") or not it.get("image_url"):
                results["errors"].append({"slug": slug, "error": "faltan campos"})
                continue
            if self.library.find(slug) and not it.get("force"):
                results["skipped"].append(slug)
                continue
            try:
                self.generate_concept(
                    slug=slug,
                    prompt=it["prompt"],
                    image_url=it["image_url"],
                    duration=it.get("duration", 10),
                    aspect_ratio=it.get("aspect_ratio"),
                    category=it.get("category", "estudio"),
                    modulo=it.get("modulo"),
                    tags=it.get("tags") or [],
                    description=it.get("description") or "",
                    negative_prompt=it.get("negative_prompt"),
                    force=it.get("force", False),
                )
                results["generated"].append(slug)
            except Exception as exc:
                self.log.error(f"  Error en {slug}: {exc}")
                results["errors"].append({"slug": slug, "error": str(exc)})
            time.sleep(delay_seconds)
        return results
