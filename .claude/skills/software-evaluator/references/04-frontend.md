# Área 04 — Componentes Frontend

## Qué evaluar

### 4.1 Inventario de componentes
```bash
# Contar componentes existentes
find src/ -name "*.tsx" -o -name "*.jsx" -o -name "*.vue" -o -name "*.svelte" \
  | grep -v node_modules | grep -v dist | grep -v "*.test.*" | grep -v "*.spec.*" | wc -l

# Ver si existe sistema de componentes
find . -type d -name "ui" -o -name "components" -o -name "design-system" \
  | grep -v node_modules | grep -v dist

# Componentes en carpeta compartida vs ad hoc
find src/ -path "*/components/ui/*" -o -path "*/ui/*" | grep -v node_modules | wc -l
find src/ -path "*/components/*" | grep -v node_modules | grep -v "/ui/" | wc -l

# Detectar si usan Shadcn, Radix, MUI, Ant Design, etc.
grep -rn "shadcn\|radix-ui\|@mui\|antd\|chakra\|@headlessui\|daisyui" package.json 2>/dev/null
```

### 4.2 Reutilización de componentes
```bash
# Detectar componentes duplicados (mismo nombre en distintas carpetas)
find src/ -name "Button.*" -o -name "Input.*" -o -name "Modal.*" -o -name "Table.*" \
  | grep -v node_modules | grep -v ".test." | grep -v ".spec."

# Detectar componentes muy grandes (>200 líneas = señal de bajo nivel de abstracción)
find src/ -name "*.tsx" -o -name "*.jsx" | grep -v node_modules | grep -v dist \
  | xargs wc -l 2>/dev/null | awk '$1 > 200 {print}' | sort -rn | head -15
```

### 4.3 Gestión del estado
```bash
# Estado local vs global
grep -rn "useState" src/ --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l
grep -rn "useReducer" src/ --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l
grep -rn "useStore\|useAtom\|useSelector\|usePinia" src/ --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l

# Detectar prop drilling profundo (señal de falta de estado global)
grep -rn "props\." src/ --include="*.tsx" 2>/dev/null | wc -l
```

### 4.4 Routing y navegación
```bash
# Detectar router utilizado
grep -rn "react-router\|next/navigation\|@tanstack/router\|vue-router\|nuxt\|wouter" \
  package.json 2>/dev/null

# Ver estructura de rutas
find src/ -name "routes.*" -o -name "router.*" -o -name "pages" -type d \
  | grep -v node_modules | head -10
find src/app -name "page.tsx" -o -name "layout.tsx" 2>/dev/null | head -20
find src/pages -name "*.tsx" -o -name "*.jsx" 2>/dev/null | head -20

# Rutas protegidas (auth guards)
grep -rn "PrivateRoute\|ProtectedRoute\|AuthGuard\|RequireAuth\|middleware" src/ \
  --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l
```

### 4.5 Estilos y design system
```bash
# Detectar sistema de estilos
cat tailwind.config.* 2>/dev/null | head -20
grep -rn "styled-components\|emotion\|@stitches\|vanilla-extract\|css-modules" \
  package.json 2>/dev/null

# Detectar tokens de diseño
find . -name "tokens.*" -o -name "theme.*" -o -name "design-tokens.*" \
  | grep -v node_modules | grep -v dist | head -10

# Detectar estilos inline (antipatrón)
grep -rn "style={{" src/ --include="*.tsx" --include="*.jsx" 2>/dev/null | wc -l
```

### 4.6 Accesibilidad y SEO
```bash
# Detectar atributos de accesibilidad
grep -rn "aria-\|role=" src/ --include="*.tsx" --include="*.jsx" 2>/dev/null | wc -l

# Detectar imágenes sin alt
grep -rn "<img" src/ --include="*.tsx" --include="*.jsx" 2>/dev/null | grep -v "alt=" | wc -l

# Detectar si hay meta tags para SEO
grep -rn "Head\|Helmet\|metadata\|<meta" src/ --include="*.tsx" 2>/dev/null | wc -l
```

### 4.7 Rendimiento del frontend
```bash
# Detectar lazy loading
grep -rn "lazy(\|Suspense\|dynamic(\|import(" src/ --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l

# Detectar uso de memo y callbacks
grep -rn "useMemo\|useCallback\|React.memo" src/ --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l

# Detectar renders innecesarios (useEffect sin dependencias)
grep -rn "useEffect(" src/ --include="*.tsx" 2>/dev/null | wc -l
grep -rn "useEffect(.*\[\])" src/ --include="*.tsx" 2>/dev/null | wc -l
```

## Criterios de puntuación

| Puntuación | Criterio |
|------------|---------|
| 8-10 🟢 | Sistema de componentes, rutas protegidas, estado global claro, tokens de diseño |
| 4-7 🟡 | Algunos componentes reutilizables, routing básico, algo de duplicación |
| 0-3 🔴 | Sin sistema de componentes, duplicación masiva, lógica mezclada con UI, sin rutas protegidas |

## Métricas a registrar
- `total_component_files`
- `shared_components_count`
- `ad_hoc_components_count`
- `large_components_count` (>200 líneas)
- `protected_routes_present` (boolean)
- `design_system_library` (nombre o null)
- `inline_styles_count`
- `lazy_loading_usage` (boolean)
- `accessibility_attrs_count`
- `images_without_alt_count`
