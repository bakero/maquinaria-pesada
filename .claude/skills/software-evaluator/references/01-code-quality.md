# Área 01 — Calidad de Código

## Qué evaluar

### 1.1 Complejidad ciclomática
```bash
# Detectar funciones muy largas (>50 líneas)
find . -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" \
  | grep -v node_modules | grep -v dist \
  | xargs awk 'BEGIN{f=""} /^(function|const|async function|def |fn )/{f=NR} {if(NR-f>50 && f>0){print FILENAME":"f" - función larga ("NR-f" líneas)"; f=0}}'

# Detectar archivos muy largos (>300 líneas)
find . -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.py" \
  | grep -v node_modules | grep -v dist \
  | xargs wc -l 2>/dev/null | awk '$1 > 300 {print}' | sort -rn | head -20

# Detectar funciones con muchos parámetros (>5)
grep -rn "function.*(.*, .*, .*, .*, .*, " src/ --include="*.ts" --include="*.js" 2>/dev/null | head -20
```

### 1.2 Duplicación de código
```bash
# Detectar bloques duplicados (líneas idénticas repetidas)
find . -name "*.ts" -o -name "*.tsx" -o -name "*.js" \
  | grep -v node_modules | grep -v dist \
  | xargs sort | uniq -d | head -30

# Detectar imports duplicados o patrones repetidos
grep -rn "console.log\|TODO\|FIXME\|HACK\|XXX" src/ --include="*.ts" --include="*.js" 2>/dev/null | wc -l
```

### 1.3 Tipado y consistencia
```bash
# Verificar si existe TypeScript configurado
cat tsconfig.json 2>/dev/null
cat jsconfig.json 2>/dev/null

# Detectar uso de 'any' en TypeScript
grep -rn ": any\|as any\|<any>" src/ --include="*.ts" --include="*.tsx" 2>/dev/null | wc -l

# Detectar @ts-ignore y @ts-nocheck
grep -rn "@ts-ignore\|@ts-nocheck\|eslint-disable" src/ --include="*.ts" --include="*.tsx" --include="*.js" 2>/dev/null | wc -l
```

### 1.4 Linting y formateo
```bash
# Verificar configuración de linting
cat .eslintrc* 2>/dev/null || cat eslint.config.* 2>/dev/null
cat .prettierrc* 2>/dev/null
cat biome.json 2>/dev/null

# Ejecutar lint y contar errores
npx eslint src/ --format=compact 2>/dev/null | tail -5
```

### 1.5 Código muerto
```bash
# Detectar exports sin referencias (requiere ts-prune si disponible)
npx ts-prune 2>/dev/null | head -30

# Detectar variables declaradas pero no usadas
grep -rn "const\|let\|var" src/ --include="*.ts" --include="*.js" 2>/dev/null | grep -v "export\|return\|=>" | head -20

# Archivos sin imports desde otros archivos
find src/ -name "*.ts" -o -name "*.tsx" | while read f; do
  base=$(basename "$f")
  if ! grep -r "from.*$base\|require.*$base\|import.*$base" src/ --include="*.ts" --include="*.tsx" --include="*.js" > /dev/null 2>&1; then
    echo "Sin referencias: $f"
  fi
done 2>/dev/null | head -20
```

### 1.6 Manejo de errores
```bash
# Detectar catch vacíos
grep -rn "catch.*{}" src/ --include="*.ts" --include="*.js" 2>/dev/null | head -20
grep -rn "catch.*{\s*}" src/ --include="*.ts" --include="*.js" 2>/dev/null | head -20

# Detectar promesas sin manejo de error
grep -rn "\.then(" src/ --include="*.ts" --include="*.js" 2>/dev/null | grep -v "\.catch\|\.finally" | head -20

# Detectar async sin try/catch
grep -rn "async " src/ --include="*.ts" --include="*.js" 2>/dev/null | head -5
```

### 1.7 Convenciones de nombrado
```bash
# Detectar inconsistencias en nombrado (mezcla camelCase / snake_case)
grep -rn "const [a-z_]*_[a-z]" src/ --include="*.ts" --include="*.js" 2>/dev/null | head -10
```

## Criterios de puntuación

| Puntuación | Criterio |
|------------|---------|
| 8-10 🟢 | Linting activo, sin errores graves, archivos <200 líneas, sin 'any' masivo, errores manejados |
| 4-7 🟡 | Algunos archivos largos, algún 'any', linting con warnings, algunos catch vacíos |
| 0-3 🔴 | Sin linting, archivos >500 líneas, 'any' masivo, catch vacíos, código muerto extenso |

## Métricas a registrar en evaluation-data.json
- `total_lines_of_code`
- `files_over_300_lines`
- `any_count` (TypeScript)
- `ts_ignore_count`
- `eslint_errors`
- `eslint_warnings`
- `catch_empty_count`
- `todo_fixme_count`
- `dead_exports_count`
