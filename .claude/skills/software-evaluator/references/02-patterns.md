# Área 02 — Patrones de Programación

## Qué evaluar

### 2.1 Estructura y arquitectura del proyecto
```bash
# Ver estructura de carpetas
find . -maxdepth 4 -type d | grep -v node_modules | grep -v .git | grep -v dist | grep -v .next | sort

# Detectar si hay separación de capas (MVC, Clean Architecture, etc.)
ls src/ 2>/dev/null
ls apps/ packages/ 2>/dev/null

# Detectar monorepo
cat pnpm-workspace.yaml 2>/dev/null
cat turbo.json 2>/dev/null
cat nx.json 2>/dev/null
cat lerna.json 2>/dev/null
```

### 2.2 Patrones en frontend
```bash
# Detectar componentes, hooks, stores, services
find src/ -type d -name "components" -o -name "hooks" -o -name "stores" -o -name "services" \
  -o -name "utils" -o -name "lib" -o -name "context" 2>/dev/null

# Detectar si hay gestión de estado
grep -rn "zustand\|redux\|jotai\|recoil\|pinia\|vuex\|useState.*\[" src/ --include="*.ts" --include="*.tsx" 2>/dev/null | head -5

# Detectar uso de Context API vs estado global
grep -rn "createContext\|useContext" src/ --include="*.ts" --include="*.tsx" 2>/dev/null | wc -l

# Lógica de negocio en componentes (señal de acoplamiento)
grep -rn "fetch(\|axios\.\|supabase\." src/components/ --include="*.ts" --include="*.tsx" 2>/dev/null | wc -l
```

### 2.3 Patrones en backend
```bash
# Detectar estructura de módulos
find . -path "*/api/*" -o -path "*/routes/*" -o -path "*/controllers/*" \
  -o -path "*/services/*" -o -path "*/repositories/*" -o -path "*/middleware/*" \
  | grep -v node_modules | grep -v dist | head -30

# Detectar si hay separación de responsabilidades
find . -name "*.controller.*" -o -name "*.service.*" -o -name "*.repository.*" \
  -o -name "*.handler.*" -o -name "*.router.*" \
  | grep -v node_modules | head -20

# Detectar validación de inputs
grep -rn "zod\|joi\|yup\|class-validator\|valibot" --include="*.ts" --include="*.js" -r . | grep -v node_modules | wc -l

# Detectar ORM o query builder
grep -rn "prisma\|drizzle\|typeorm\|sequelize\|knex\|mikro-orm" --include="*.ts" --include="*.js" -r . | grep -v node_modules | head -5
```

### 2.4 Separación de responsabilidades
```bash
# Detectar lógica de negocio en rutas (antipatrón)
grep -rn "router\.\(get\|post\|put\|delete\)" . --include="*.ts" --include="*.js" | grep -v node_modules \
  | while read line; do
    file=$(echo $line | cut -d: -f1)
    lines=$(wc -l < "$file" 2>/dev/null)
    if [ "$lines" -gt 80 ]; then echo "Ruta con mucha lógica: $file ($lines líneas)"; fi
  done 2>/dev/null | head -10

# Detectar acceso directo a DB desde frontend
grep -rn "supabase\." src/ --include="*.tsx" --include="*.ts" 2>/dev/null \
  | grep -v "hooks\|services\|api\|lib" | head -20
```

### 2.5 Reutilización y DRY
```bash
# Detectar funciones utilitarias existentes
find . -name "utils.*" -o -name "helpers.*" -o -name "common.*" \
  | grep -v node_modules | grep -v dist | head -20

# Detectar patrones repetidos de fetch/API
grep -rn "fetch(\|axios\." src/ --include="*.ts" --include="*.tsx" 2>/dev/null | wc -l
```

### 2.6 Consistencia de patrones
```bash
# Detectar mezcla de estilos de componentes (class + function)
grep -rn "class.*extends.*Component" src/ --include="*.tsx" --include="*.jsx" 2>/dev/null | wc -l
grep -rn "function\|const.*=.*(" src/ --include="*.tsx" --include="*.jsx" 2>/dev/null | wc -l

# Detectar mezcla de async/await con .then()
grep -rn "\.then(" src/ --include="*.ts" --include="*.tsx" 2>/dev/null | wc -l
grep -rn "await " src/ --include="*.ts" --include="*.tsx" 2>/dev/null | wc -l
```

## Criterios de puntuación

| Puntuación | Criterio |
|------------|---------|
| 8-10 🟢 | Arquitectura clara, separación de capas, validación de inputs, patrones consistentes |
| 4-7 🟡 | Estructura parcial, algo de lógica en componentes, validación básica |
| 0-3 🔴 | Sin arquitectura clara, lógica de negocio mezclada, sin validación, patrones inconsistentes |

## Métricas a registrar
- `has_layer_separation` (boolean)
- `business_logic_in_components_count`
- `validation_library_present` (boolean)
- `direct_db_calls_from_frontend_count`
- `async_await_consistency_ratio`
- `monorepo` (boolean)
