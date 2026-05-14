# Área 03 — Tests

## Qué evaluar

### 3.1 Existencia y configuración de tests
```bash
# Detectar frameworks de test configurados
cat vitest.config.* 2>/dev/null
cat jest.config.* 2>/dev/null
cat playwright.config.* 2>/dev/null
cat cypress.config.* 2>/dev/null
grep -n "\"test\"\|\"vitest\"\|\"jest\"\|\"playwright\"\|\"cypress\"" package.json 2>/dev/null

# Contar archivos de test existentes
find . -name "*.test.ts" -o -name "*.test.tsx" -o -name "*.test.js" \
  -o -name "*.spec.ts" -o -name "*.spec.tsx" -o -name "*.spec.js" \
  -o -name "*.e2e.ts" -o -name "*.e2e.js" \
  | grep -v node_modules | wc -l

# Ver carpetas de test
find . -type d -name "__tests__" -o -name "tests" -o -name "test" -o -name "e2e" \
  | grep -v node_modules | grep -v dist
```

### 3.2 Tipos de tests presentes
```bash
# Tests unitarios
find . -name "*.test.ts" -o -name "*.test.tsx" -o -name "*.test.js" -o -name "*.spec.ts" \
  | grep -v node_modules | grep -v e2e | grep -v integration | wc -l

# Tests de integración
find . -name "*.integration.test.*" -o -name "*.integration.spec.*" \
  -o -path "*/integration/*" \
  | grep -v node_modules | wc -l

# Tests E2E
find . -name "*.e2e.*" -o -path "*/e2e/*" -o -path "*/playwright/*" -o -path "*/cypress/*" \
  | grep -v node_modules | wc -l

# Tests de autorización / seguridad
grep -rn "auth\|authorization\|permission\|RLS\|policy" . \
  --include="*.test.ts" --include="*.spec.ts" --include="*.test.js" 2>/dev/null | wc -l

# Smoke tests
grep -rn "smoke\|health\|ping" . \
  --include="*.test.ts" --include="*.spec.ts" --include="*.test.js" 2>/dev/null | wc -l
```

### 3.3 Cobertura de código
```bash
# Ejecutar cobertura si está configurada (sin modificar código)
npx vitest run --coverage 2>/dev/null | tail -20
npx jest --coverage --passWithNoTests 2>/dev/null | tail -20

# Leer último reporte de cobertura si existe
cat coverage/coverage-summary.json 2>/dev/null | python3 -c "
import json,sys
data=json.load(sys.stdin)
total=data.get('total',{})
print(f\"Líneas: {total.get('lines',{}).get('pct','?')}%\")
print(f\"Funciones: {total.get('functions',{}).get('pct','?')}%\")
print(f\"Ramas: {total.get('branches',{}).get('pct','?')}%\")
" 2>/dev/null
```

### 3.4 Calidad de los tests
```bash
# Detectar tests vacíos o con solo 'expect(true).toBe(true)'
grep -rn "expect(true)\|it.skip\|test.skip\|xit\|xtest\|xdescribe" . \
  --include="*.test.ts" --include="*.spec.ts" --include="*.test.js" 2>/dev/null | wc -l

# Detectar tests sin aserciones
grep -rn "it(\|test(" . --include="*.test.ts" --include="*.spec.ts" 2>/dev/null \
  | grep -v "expect\|assert" | head -10

# Detectar mocks excesivos (señal de acoplamiento)
grep -rn "jest.mock\|vi.mock\|stub\|sinon" . \
  --include="*.test.ts" --include="*.spec.ts" 2>/dev/null | wc -l
```

### 3.5 Flujos críticos de beta testers
```bash
# Detectar si login/auth tiene tests
grep -rn "login\|signin\|auth\|session" . \
  --include="*.test.ts" --include="*.spec.ts" --include="*.e2e.ts" 2>/dev/null | wc -l

# Detectar cobertura de rutas/endpoints principales
grep -rn "describe\|it(\|test(" . --include="*.test.ts" --include="*.spec.ts" 2>/dev/null \
  | head -30

# Playwright: ver tests E2E definidos
find . -name "*.spec.ts" -path "*/e2e/*" -o -name "*.spec.ts" -path "*/playwright/*" \
  | grep -v node_modules \
  | xargs grep -l "test\|expect" 2>/dev/null
```

### 3.6 Ejecución de tests en CI
```bash
# Ver si los tests están en el pipeline de CI
cat .github/workflows/*.yml 2>/dev/null | grep -A2 "test\|vitest\|jest\|playwright"
grep -rn "test\|coverage" .github/workflows/ 2>/dev/null | head -20
```

## Criterios de puntuación

| Puntuación | Criterio |
|------------|---------|
| 8-10 🟢 | Tests unitarios + integración + E2E, cobertura >60%, tests de auth, en CI |
| 4-7 🟡 | Algunos tests, cobertura 20-60%, sin E2E o sin integración |
| 0-3 🔴 | Sin tests o <20% cobertura, sin tests de auth, no en CI |

## Métricas a registrar
- `unit_test_files_count`
- `integration_test_files_count`
- `e2e_test_files_count`
- `auth_test_count`
- `coverage_lines_pct`
- `coverage_functions_pct`
- `coverage_branches_pct`
- `skipped_tests_count`
- `tests_in_ci` (boolean)
- `smoke_tests_present` (boolean)
