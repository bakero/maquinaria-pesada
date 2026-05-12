# AUDITORÍA DRAFT v5 · ¿Tiene toda la info? · ¿Maximiza el uso de clips?

> Resultado en 1 línea: **NO, hay 4 huecos de información** y **SÍ se cambia
> de video demasiadas veces** (50 cuts en 5min cuando con la mitad sobraba).

---

## PARTE 1 · INFORMACIÓN MISSING (lo que falta para render zero-ambigüedad)

### 1.1 Color por hex, no por nombre
v5 dice `amarillo` / `azul` / `rojo` / `gris`. El renderer necesita el HEX.
Dos elementos "amarillos" pueden ser distintos tonos.

**Fix v6:** sustituir nombre por hex explícito.
```
| 04.0s | stat_card "ADOPCIÓN 2026 · 88%" #F5C400 | MID_LEFT | ...
```

### 1.2 Datos internos de elementos compuestos
Algunos elementos no son "una etiqueta", son **estructuras**:

- `hierarchy_diagram` → lista de nodos jerárquicos (e.g. `[IA, ML, DL, LLMs]`)
- `timeline_visual` → eventos con año + descripción (`[(1956, "Dartmouth"), (1970, "1er invierno"), ...]`)
- `bar_chart` → barras con label y valor (`[(A, 80), (B, 60)]`)
- `two_column_compare` → 2 columnas con items independientes
- `recap_grid` → array de items

v5 mete todo en una etiqueta string (e.g. `"IA ⊃ ML ⊃ DL ⊃ LLMs"`) y deja que el renderer parsee. **Frágil**: pequeño cambio de separador rompe el parser.

**Fix v6:** sintaxis explícita con bloques `data:`:
```
| 04.0s | hierarchy_diagram | MID_CENTER | 660,290,600,460 | hasta fin |
data:
  title: "Taxonomía IA"
  items: ["IA", "ML", "DL", "LLMs"]
  color: "#4DB8FF"
```

### 1.3 Animación / transición de entrada
v5 nunca dice si un overlay aparece con `cut`, `fade-in`, `slide-in`,
`pop`. El compositor los hace aparecer "sin más" (cut implícito).

**Fix v6:** columna `entry` con default `cut`:
| Element | Pos | x,y,W,H | entry | exit |

### 1.4 Z-index cuando coexisten
Si dos overlays se superponen levemente (e.g. hierarchy_diagram con
stat_card), ¿cuál va encima? v5 lo deja al orden de definición.

**Fix v6:** anotar `z` cuando relevante (default = orden de aparición).

---

## PARTE 2 · CUTS DEMASIADOS (no se aprovechan los clips)

### Cuts actuales en v5

| Intervención | Duración | Cuts | Posibles | Problema |
|---|---|---|---|---|
| 1.1 Maria | 16.93s | **4** | 0-1 | Maria solo dura 21s → cabe entera en 1 clip |
| 1.2 Maria | 15.13s | **4** | 0-1 | Idem |
| 3.1 Yago | 16.02s | 3 | 1 | Yago solo 10s, necesita 2 clips, 1 cut |
| 3.2 Maria | 16.41s | **4** | 0-1 | 1 clip basta |
| 3.3 Yago | 15.24s | 2 | 1 | OK ya |
| 3.4 Maria | 0.78s | 1 | 1 | OK |
| 4.1 Maria | 40.25s | **5** | 1-2 | Necesita 2 clips (21+21=42), 1 cut |
| 4.2 Yago | 12.12s | 2 | 1 | OK ya |
| 4.3 Maria | 33.61s | **4** | 1-2 | 2 clips, 1 cut |
| 4.4 Yago | 23.06s | 3 | 2 | OK ya |
| 4.5 Maria | 28.14s | **4** | 1-2 | 2 clips, 1 cut |
| 5.1 Yago | 34.00s | 4 | 3 | OK casi |
| 5.2 Maria | 14.07s | 2 | 0-1 | 1 clip basta |
| 5.3 Yago | 29.70s | 5 | 2-3 | OK |

**Total v5: ~50 sub-segmentos · ~36 cuts**
**Total v6 propuesto: ~25 sub-segmentos · ~13 cuts** (mitad).

### Regla de cuts revisada

```
Intervención duración X · clip_max_dur = max duración del pool
  - X ≤ clip_max_dur:        1 clip (0 cuts)
  - X ≤ 2× clip_max_dur:     2 clips (1 cut, en período natural)
  - X ≤ 3× clip_max_dur:     3 clips (2 cuts)
  - etc.
```

Con clip_max_dur = 21s (Maria solo) o 10s (Yago / two-shots):
- Cualquier Maria <21s → 1 clip
- Cualquier Yago <10s → 1 clip
- Yago 10-20s → 2 clips
- Maria 21-42s → 2 clips
- Yago 20-30s → 3 clips
- Maria 42-63s → 3 clips

### Ventajas de menos cuts

1. **Más coherencia visual**: cada toma respira, no hay efecto MTV
2. **Mejor lip-sync futuro**: aplicar Sync.so a 1 clip es más barato que a 4
3. **Menos artefactos** en concat ffmpeg (cada cut es una posibilidad de mismatch)
4. **Story-telling más reposado** acorde con el tono divulgativo

### Cuándo SÍ cortar dentro de una intervención

- **Cambio de plano dramático**: pasar de TWO_SHOT a CLOSE_UP en momento clave (e.g. 4.1 cuando entra la pizarra, 4.5 al cerrar bloque)
- **Intervención excede duración del clip más largo del pool del speaker**
- **Pausa muy marcada que el director quiere subrayar** (raro, sólo en momentos cumbre)

---

## PARTE 3 · CAMBIOS PROPUESTOS PARA v6

| Cambio | Impacto |
|---|---|
| Hex en lugar de nombre de color | Render exacto |
| Bloque `data:` para elementos compuestos | Parser robusto |
| Columna `entry` con default `cut` | Animaciones explícitas |
| Reducción de cuts a ~13 (de 36) | Menos cambios de video, mejor uso |
| Cut **sólo** cuando duración exige | Aprovecha clip al máximo |
| 1 cut decorativo permitido por bloque pizarra para entrar plano cerrado | Story-telling |

---

## PARTE 4 · ¿DECIDES?

**Opción A**: Reescribo el draft completo v6 con todos los fixes (~30 min de mi parte).
**Opción B**: Aplico fixes incrementales sobre v5 (más rápido pero v5 queda parcheado).
**Opción C**: Te conformas con v5 y vamos al render con las imperfecciones. Ya hay info suficiente, solo quedan decisiones de calidad.

---

# EJEMPLO COMPACTO · INTERVENCIÓN 1.1 EN v6

```markdown
### 1.1 — María
- TC: 00:02.060 → 00:18.990 · DUR: 16.93s
- TONO: [ironico]
- TEXTO: "En 2026, el 88% de las empresas dice que ya usa inteligencia 
  artificial. El otro 12% dice que lo está evaluando. Básicamente, todo 
  el mundo está en el tema, igual que todo el mundo ha leído los 
  términos y condiciones de cada app que instala. Exactamente nadie."
- PLANO: TWO_SHOT_M_ACTIVE
- PIZARRA: SI (4.0s → fin · 12.9s)

CLIPS:
| seg | t scene | dur | slug | mode | clip secs | razon |
|-----|---------|-----|------|------|-----------|-------|
| 1   | 0.00→16.93 | 16.93 | studio_two_m_active_v1 | normal | 0.0–16.93 | UN solo clip cubre toda |
                                                                       (clip dura 10.4s, 
                                                                        loopear con stream_loop)

ALTERNATIVA preferida (si estructura permite Maria solo):
| 1   | 0.00→16.93 | 16.93 | studio_maria_solo_v1 | normal | 0.0–16.93 | Maria solo 21.2s, 
                                                                          cabe entera | 

PIP_CLIPS (cuando pizarra activa, t=4.0→16.93 = 12.93s):
| pip seg | clip | mode | secs |
|---------|------|------|------|
| 1 | studio_maria_solo_v2 | normal | 0.0–10.4 |
| 2 | studio_two_m_active_v2 | normal | 0.0–2.53 |

ON-SCREEN:
| t in | element | pos | x,y,W,H | entry | exit | data |
|------|---------|-----|---------|-------|------|------|
| 0.0  | name_tag | TR | 1640,40,220,80 | cut | hasta fin | text:"MARIA" color:#F5C400 |
| 4.0  | stat_card | ML | 60,280,460,280 | fade-in 0.5s | hasta fin | label:"ADOPCIÓN 2026" value:"88%" subtitle:"empresas usan IA" color:#F5C400 |
| 8.0  | stat_card | MR | 1280,280,460,280 | fade-in 0.5s | hasta fin | label:"EVALUANDO" value:"12%" subtitle:"siguen estudiándolo" color:#888888 |
| 14.0 | sticker | BL | 60,760,240,240 | pop | hasta fin | name:"exactamente_nadie_meme" |

ANTI-COLISIÓN OK: ML ↔ MR gap 760px · sticker BL ↔ PIP BR gap 1170px · todos < 950 evitan subs.
TRANSICIÓN OUT: corte seco en pausa tras "exactamente nadie".
```

CUTS en v6 para 1.1: **0** (de 4 en v5). El clip de Maria solo cubre toda la
intervención. La variedad la dan el PIP encadenado y los overlays.

---

**FIN AUDITORÍA**
