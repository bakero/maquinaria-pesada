# Área 09 — Dependencias

## Qué evaluar

### 9.1 Inventario de dependencias
```bash
# Ver dependencias directas
cat package.json 2>/dev/null | python3 -c "
import json,sys
data=json.load(sys.stdin)
deps=data.get('dependencies',{})
devDeps=data.get('devDependencies',{})
print(f'Dependencias de producción: {len(deps)}')
print(f'Dependencias de desarrollo: {len(devDeps)}')
print(f'Total: {len(deps)+len(devDeps)}')
"

# Ver versiones de dependencias clave
cat package.json 2>/dev/null | python3 -c "
import json,sys
data=json.load(sys.stdin)
keys=['react','next','vue','nuxt','vite','typescript','node','express','fastify','hono','prisma','drizzle','supabase']
all_deps={**data.get('dependencies',{}),**data.get('devDependencies',{})}
for k in keys:
  if k in all_deps: print(f'{k}: {all_deps[k]}')
"
```

### 9.2 Vulnerabilidades de seguridad
```bash
npm audit --json 2>/dev/null | python3 -c "
import json,sys
try:
  data=json.load(sys.stdin)
  vulns=data.get('vulnerabilities',{})
  by_severity={'critical':[],'high':[],'moderate':[],'low':[]}
  for name,v in vulns.items():
    sev=v.get('severity','unknown')
    if sev in by_severity: by_severity[sev].append(name)
  for sev,pkgs in by_severity.items():
    if pkgs: print(f'{sev.upper()} ({len(pkgs)}): {', '.join(pkgs[:5])}')
except Exception as e: print(f'Error: {e}')
" 2>/dev/null
```

### 9.3 Dependencias desactualizadas
```bash
# Ver dependencias con actualizaciones disponibles
npm outdated 2>/dev/null | head -30

# Contar dependencias desactualizadas
npm outdated 2>/dev/null | tail -n +2 | wc -l
```

### 9.4 Dependencias no utilizadas
```bash
# Detectar posibles dependencias no usadas (con depcheck si disponible)
npx depcheck --json 2>/dev/null | python3 -c "
import json,sys
try:
  data=json.load(sys.stdin)
  unused=data.get('dependencies',[])
  missing=data.get('missing',{})
  print(f'No utilizadas: {len(unused)} - {unused[:10]}')
  print(f'Faltantes (usadas pero no en package.json): {list(missing.keys())[:5]}')
except: print('depcheck no disponible')
" 2>/dev/null
```

### 9.5 Licencias
```bash
# Verificar licencias de dependencias
npx license-checker --summary 2>/dev/null | head -20

# Detectar licencias problemáticas (GPL, AGPL)
npx license-checker --json 2>/dev/null | python3 -c "
import json,sys
try:
  data=json.load(sys.stdin)
  problematic=[k for k,v in data.items() if any(l in str(v.get('licenses','')) for l in ['GPL','AGPL','LGPL','CC-BY-SA'])]
  print(f'Licencias potencialmente problemáticas: {len(problematic)}')
  for p in problematic[:5]: print(f'  {p}')
except: pass
" 2>/dev/null
```

### 9.6 Tamaño del bundle
```bash
# Ver si hay análisis de bundle configurado
grep -rn "bundle-analyzer\|bundlesize\|webpack-bundle" package.json 2>/dev/null

# Detectar dependencias pesadas
cat package.json 2>/dev/null | python3 -c "
import json,sys
data=json.load(sys.stdin)
heavy=['moment','lodash','antd','@mui/material','chart.js','three','@aws-sdk']
all_deps={**data.get('dependencies',{}),**data.get('devDependencies',{})}
for h in heavy:
  if h in all_deps: print(f'Dep pesada: {h} {all_deps[h]}')
"
```

## Criterios de puntuación
| Puntuación | Criterio |
|------------|---------|
| 8-10 🟢 | Sin vulnerabilidades críticas/altas, <20% desactualizadas, sin dependencias no usadas |
| 4-7 🟡 | Algunas vulnerabilidades moderadas, algunas desactualizadas, pocas no usadas |
| 0-3 🔴 | Vulnerabilidades críticas, >50% desactualizadas, muchas sin usar |

## Métricas a registrar
- `prod_deps_count`
- `dev_deps_count`
- `critical_vulns_count`
- `high_vulns_count`
- `moderate_vulns_count`
- `outdated_deps_count`
- `unused_deps_count`
- `problematic_licenses_count`
