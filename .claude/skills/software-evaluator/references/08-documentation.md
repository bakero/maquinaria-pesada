# Área 08 — Documentación

## Qué evaluar

### 8.1 README y documentación de entrada
```bash
# Ver README principal
wc -l README.md 2>/dev/null
cat README.md 2>/dev/null | head -50

# Detectar secciones clave en README
grep -in "instalación\|install\|setup\|uso\|usage\|contribuir\|contributing\|architecture\|estructura" README.md 2>/dev/null

# Ver si hay READMEs en subdirectorios importantes
find . -name "README*" | grep -v node_modules | grep -v dist | grep -v ".git"
```

### 8.2 Documentación de arquitectura
```bash
# Ver si existe documentación de arquitectura
find . -path "*/docs/*" | grep -v node_modules | head -30
ls docs/ 2>/dev/null
ls docs/architecture/ 2>/dev/null

# Detectar archivos de decisiones (ADRs)
find . -name "*.adr*" -o -path "*/decisions/*" -o -path "*/adr/*" \
  | grep -v node_modules | head -10

# Ver si existe mapa de pantallas / funcionalidades
find docs/ -name "*.md" 2>/dev/null | head -20
```

### 8.3 Documentación inline (código)
```bash
# Detectar JSDoc / TSDoc
grep -rn "/\*\*" src/ --include="*.ts" --include="*.tsx" --include="*.js" 2>/dev/null | wc -l

# Ratio comentarios / código
total_lines=$(find src/ -name "*.ts" -o -name "*.tsx" | grep -v node_modules | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
comment_lines=$(grep -rn "\/\/\|\/\*" src/ --include="*.ts" --include="*.tsx" 2>/dev/null | wc -l)
echo "Líneas totales: $total_lines | Líneas con comentarios: $comment_lines"

# Detectar funciones sin documentación (>10 líneas sin comentario)
grep -rn "^export function\|^export const\|^export async function" src/ \
  --include="*.ts" --include="*.tsx" 2>/dev/null | wc -l
```

### 8.4 Documentación de API
```bash
# Detectar si hay documentación de API
find . -name "openapi*" -o -name "swagger*" -o -name "api.md" \
  | grep -v node_modules | head -10

# Detectar Postman / Insomnia collections
find . -name "*.postman*" -o -name "*.insomnia*" | grep -v node_modules | head -5

# Ver si hay tipos bien documentados en TypeScript
grep -rn "interface\|type " src/ --include="*.ts" 2>/dev/null | grep -v "node_modules" | wc -l
```

### 8.5 Documentación de entornos y configuración
```bash
# Ver .env.example
cat .env.example 2>/dev/null

# Detectar CHANGELOG
cat CHANGELOG.md 2>/dev/null | head -30
ls CHANGELOG* 2>/dev/null

# Detectar CONTRIBUTING guide
cat CONTRIBUTING.md 2>/dev/null | head -20
```

### 8.6 Plan de migración documentado
```bash
# Ver si existe el plan maestro en el repo
find docs/ -name "migration*" -o -name "plan*" | grep -v node_modules | head -5
ls docs/architecture/ 2>/dev/null
cat docs/architecture/migration-plan.md 2>/dev/null | head -30
```

## Criterios de puntuación
| Puntuación | Criterio |
|------------|---------|
| 8-10 🟢 | README completo, arquitectura documentada, ADRs, JSDoc en funciones públicas, .env.example |
| 4-7 🟡 | README básico, algo de documentación, sin ADRs, pocos comentarios |
| 0-3 🔴 | Sin README útil, sin arquitectura documentada, sin comentarios, sin .env.example |

## Métricas a registrar
- `readme_lines`
- `has_architecture_docs` (boolean)
- `has_adrs` (boolean)
- `jsdoc_count`
- `has_api_docs` (boolean)
- `has_env_example` (boolean)
- `has_changelog` (boolean)
- `has_migration_plan` (boolean)
- `docs_files_count`
