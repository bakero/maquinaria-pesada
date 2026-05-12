# Analytics: Spotify, iVoox y LinkedIn

Guía operativa para activar los tres conectores de la página
**📊 Rendimiento** del cockpit. Cada plataforma tiene su propia vía de
autenticación; aquí queda documentado el paso a paso.

Código: `cockpit/connectors/analytics/{base,spotify,ivoox,linkedin}.py`.
UI: `cockpit/pages/16_📊_Rendimiento.py`.
Cache: `logs/analytics/<source>.json` (no commitear).

## Variables `.env` (resumen)

```env
# Spotify (cookies del dashboard de creadores)
SPOTIFY_SP_DC=...
SPOTIFY_SP_KEY=...
SPOTIFY_PODCAST_ID=...

# iVoox
IVOOX_RSS_URL=https://www.ivoox.com/<slug>_fg_f<ID>_filtro_1.xml

# LinkedIn (app developer.linkedin.com + Community Management API)
LINKEDIN_CLIENT_ID=...
LINKEDIN_CLIENT_SECRET=...
LINKEDIN_ORG_URN=urn:li:organization:1234567
```

Los tokens OAuth de LinkedIn se persisten en `logs/analytics/linkedin_tokens.json`
tras completar el flujo desde la UI.

---

## 1. Spotify for Creators

No hay API oficial de analytics. Usamos el cliente no oficial
[`spotifyconnector`](https://github.com/openpodcast/spotify-connector) que
consume el mismo backend privado que usa el dashboard
(`generic.wg.spotify.com/podcasters/v0`).

### Obtener `sp_dc` y `sp_key`

1. Inicia sesión en https://podcasters.spotify.com/ con tu cuenta de creador.
2. Abre DevTools → **Application** → **Cookies → `https://spotify.com`**
   (el dominio raíz, no el del dashboard).
3. Copia los valores de las cookies:
   - `sp_dc` (~160 chars).
   - `sp_key` (UUID, 36 chars).
4. `podcast_id` está en la URL al seleccionar el show:
   `https://podcasters.spotify.com/pod/show/<podcast_id>/...`.

Validez ≈ 1 año. Si el conector empieza a fallar con 401, repetir el login y
regenerar las cookies.

### Métricas expuestas

- `metadata`, `followers`, `streams`, `listeners`, `aggregate` (demografía),
  `episodes`, `performance` (retention curve por episodio).

### Paquetes pip

```
spotifyconnector>=0.8.2
spotipy>=2.26.0   # opcional, solo metadatos públicos
```

---

## 2. iVoox

iVoox **no tiene API pública**. Soportamos dos vías legítimas:

### 2.1 RSS público (recomendado)

URL del RSS: en la página del podcast → **Compartir → Suscripción → Por RSS**;
o desde la zona de creadores → **Editar programa → Feed RSS**.

`feedparser` parsea metadatos (título, episodios, duración, URLs, fechas).
El RSS **no** expone escuchas/retención.

### 2.2 CSV de la Zona de Creadores

Desde `https://www.ivoox.com/ajustes` (planes Essential+) exporta
estadísticas a CSV manualmente. Súbelo en la UI; el método
`IvooxAnalytics.load_stats_csv(path)` lo normaliza a DataFrame.

### Lo que NO hacemos

- No descargamos MP3 ni scrapeamos páginas internas (contra ToS).
- No automatizamos login al panel (frágil + posible bloqueo).
- `robots.txt` desautoriza explícitamente `ClaudeBot`, `anthropic-ai`,
  `Claude-Web`. Por respeto al editor, identificamos `User-Agent` con contacto.

### Paquetes pip

```
feedparser>=6.0.11
podcastparser>=0.6.10
requests>=2.32.3
pandas>=2.2
```

---

## 3. LinkedIn

API oficial vía **Community Management API** + **Marketing Developer
Platform**. Requiere app aprobada (Development Tier para empezar; Standard
Tier requiere persona jurídica y screencast de uso).

### 3.1 Crear app

1. https://developer.linkedin.com/ → **My Apps → Create app**.
2. Asocia la app a una **LinkedIn Page** de la que seas ADMIN.
3. En pestaña **Auth**: anota `Client ID` y `Client Secret`.
4. Añade Redirect URIs (p.ej. `http://localhost:8501/oauth/callback`).
5. En pestaña **Products**: solicita **Community Management API** y/o
   **Marketing Developer Platform**. La aprobación tarda días/semanas.

### 3.2 Flujo OAuth (desde la UI)

1. Definir `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_ORG_URN`
   en `.env`. El URN se obtiene del admin de la página
   (`urn:li:organization:<id>`).
2. Abrir página `📊 Rendimiento` → sección LinkedIn.
3. Click en **Autorizar app en LinkedIn** (abre `oauth/v2/authorization`).
4. Tras consentir, LinkedIn redirige al `redirect_uri` con `?code=...`.
   Copiar el `code` y pegarlo en el campo de la UI.
5. Click **Intercambiar code → token**. El token (60d) + refresh (365d) se
   guardan en `logs/analytics/linkedin_tokens.json`.
6. El conector refresca el access token automáticamente si faltan <7 días
   para caducar y hay refresh disponible.

### 3.3 Endpoints usados

Header `LinkedIn-Version: 202604`, base `https://api.linkedin.com/rest`.

| Endpoint | Métricas |
|---|---|
| `/organizationalEntityShareStatistics` | impressions, clicks, likes, comments, shares, engagement (lifetime + por post) |
| `/organizationPageStatistics` | page views, clicks, demografía (país, función, industria) |
| `/organizationalEntityFollowerStatistics` | followers orgánicos/pagados, demografía |
| `/posts` | listado de publicaciones del autor |

Scopes mínimos: `r_organization_social`, `rw_organization_admin`,
`r_organization_admin`.

### 3.4 Alternativa: Ayrshare

Si la aprobación de Community Management se atasca, hay agregador SaaS
[Ayrshare](https://www.ayrshare.com/) (~$149/mes Premium) ya aprobado por
LinkedIn. Paquete `pip install social-post-api`. No incluido en este
conector por defecto.

### Paquetes pip

```
requests>=2.32.3
requests-oauthlib>=2.0.0
```

---

## Aspectos legales

- **Spotify**: usar cookies propias contra endpoint privado del propio show
  está en zona gris pero es la práctica común. ToS prohíbe redistribución
  de datos; aquí solo se muestran al propio creador.
- **iVoox**: ToS prohíbe scraping. Permitido explícitamente: RSS y widgets.
  Esta integración se limita a esos canales + CSV oficial.
- **LinkedIn**: el scraping (`linkedin-api` no oficial) viola ToS y arriesga
  bloqueo de cuenta (caso *hiQ vs LinkedIn*). Esta integración usa solo
  Member/Marketing API oficiales.

---

## Caché y rate limits

| Source | TTL caché | Rate limit observado |
|---|---|---|
| Spotify | 1 h | Sin doc oficial; self-throttle 1 req/s recomendado |
| iVoox (RSS) | 6 h | Sin límite formal; respetar `User-Agent` |
| LinkedIn (Dev Tier) | 1 h | 500/app/día · 100/miembro/día |

El método `AnalyticsConnector.save_cache()` persiste en
`logs/analytics/<source>.json` con timestamp. `load_cache()` devuelve `None`
si el TTL ha expirado.
