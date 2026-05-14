# Área 06 — Seguridad   ⚠️ ÁREA CRÍTICA — Peso × 2

## IMPORTANTE
Si se detectan secrets reales, NO mostrarlos en el informe.
Indicar solo: "Se han detectado N secrets en X archivos. Ver lista privada."
Guardar la lista de archivos en un archivo local SEPARADO no commiteado:
`/tmp/security-findings-<EVAL_ID>.txt`

## Qué evaluar

### 6.1 Secrets y credenciales — PRIORIDAD ABSOLUTA
```bash
# Detectar secrets hardcodeados
grep -rn "api_key\|apikey\|API_KEY\|secret\|SECRET\|password\|PASSWORD\|token\|TOKEN" \
  src/ --include="*.ts" --include="*.tsx" --include="*.js" \
  | grep -v "process.env\|import.meta.env\|getenv\|os.environ\|placeholder\|example\|test\|mock\|dummy" \
  | grep -v ".env.example" \
  | wc -l

# Detectar JWT tokens hardcodeados (prefijo eyJ)
grep -rn "eyJhbGci\|eyJzdWIi\|eyJ" src/ --include="*.ts" --include="*.tsx" --include="*.js" \
  2>/dev/null | grep -v node_modules | wc -l

# Detectar .env files commiteados (no deberían estar en git)
git ls-files | grep "^\.env$\|^\.env\." 2>/dev/null | grep -v ".example\|.template\|.sample"

# Detectar si .gitignore tiene los .env excluidos
cat .gitignore 2>/dev/null | grep "\.env"

# Detectar service_role keys de Supabase en código
grep -rn "service_role" src/ --include="*.ts" --include="*.tsx" --include="*.js" \
  2>/dev/null | grep -v node_modules | head -5
```

### 6.2 Autenticación y autorización
```bash
# Detectar rutas de API sin middleware de auth
find . -path "*/api/*" -name "*.ts" -o -path "*/routes/*" -name "*.ts" \
  | grep -v node_modules | while read f; do
    if ! grep -q "auth\|session\|middleware\|verify\|guard\|requireAuth\|isAuthenticated" "$f" 2>/dev/null; then
      echo "Sin auth: $f"
    fi
  done | head -20

# Detectar si hay validación de JWT
grep -rn "verifyJWT\|verify.*token\|jwt.verify\|jwtVerify\|auth.getUser\|getSession" \
  . --include="*.ts" --include="*.js" | grep -v node_modules | head -10

# Detectar roles y permisos
grep -rn "role\|permission\|can(\|hasPermission\|isAdmin\|isOwner" \
  src/ --include="*.ts" --include="*.tsx" 2>/dev/null | wc -l
```

### 6.3 Validación de inputs
```bash
# Detectar si se validan inputs en backend antes de usar
grep -rn "req\.body\|req\.params\|req\.query" . --include="*.ts" --include="*.js" \
  | grep -v node_modules | while read line; do
    file=$(echo "$line" | cut -d: -f1)
    linenum=$(echo "$line" | cut -d: -f2)
    # Buscar validación cercana
    if ! grep -n "zod\|joi\|yup\|validate\|schema\|parse" "$file" 2>/dev/null | awk -F: '$1 <= "'$linenum'" + 5 && $1 >= "'$linenum'" - 5' | grep -q .; then
      echo "Input sin validar: $file:$linenum"
    fi
  done 2>/dev/null | head -15
```

### 6.4 Inyección SQL y XSS
```bash
# Detectar queries SQL dinámicas sin parameterizar
grep -rn "query(\`\|query(\"" . --include="*.ts" --include="*.js" \
  | grep -v node_modules | grep "\${\|'+\|concat" | head -10

# Detectar dangerouslySetInnerHTML (riesgo XSS)
grep -rn "dangerouslySetInnerHTML\|innerHTML\|document.write" src/ \
  --include="*.tsx" --include="*.jsx" --include="*.ts" 2>/dev/null | head -10

# Detectar eval() usage
grep -rn "eval(\|new Function(" src/ --include="*.ts" --include="*.tsx" --include="*.js" \
  2>/dev/null | grep -v node_modules | head -5
```

### 6.5 Headers de seguridad
```bash
# Detectar configuración de headers HTTP de seguridad
grep -rn "Content-Security-Policy\|X-Frame-Options\|X-Content-Type\|HSTS\|cors" \
  . --include="*.ts" --include="*.js" | grep -v node_modules | head -10

# Detectar configuración CORS
grep -rn "cors(\|corsOptions\|allowedOrigins" . --include="*.ts" --include="*.js" \
  | grep -v node_modules | head -10

# Detectar si hay Next.js headers configurados
cat next.config.* 2>/dev/null | grep -A5 "headers"
```

### 6.6 Dependencias con vulnerabilidades
```bash
# Audit de dependencias npm
npm audit --json 2>/dev/null | python3 -c "
import json,sys
try:
  data=json.load(sys.stdin)
  vulns=data.get('vulnerabilities',{})
  critical=sum(1 for v in vulns.values() if v.get('severity')=='critical')
  high=sum(1 for v in vulns.values() if v.get('severity')=='high')
  moderate=sum(1 for v in vulns.values() if v.get('severity')=='moderate')
  print(f'Críticas: {critical}, Altas: {high}, Moderadas: {moderate}')
except: print('No se pudo leer el audit')
" 2>/dev/null

# Listar vulnerabilidades críticas y altas
npm audit 2>/dev/null | grep -E "critical|high" | head -20
```

### 6.7 Variables de entorno y configuración
```bash
# Verificar que las variables de entorno están documentadas
cat .env.example 2>/dev/null | wc -l
diff <(cat .env.example 2>/dev/null | grep -v "^#" | cut -d= -f1 | sort) \
     <(cat .env.local 2>/dev/null | grep -v "^#" | cut -d= -f1 | sort) 2>/dev/null

# Detectar variables de entorno con prefijo public que contienen secrets
grep -rn "NEXT_PUBLIC_.*KEY\|NEXT_PUBLIC_.*SECRET\|VITE_.*SECRET\|VITE_.*PASSWORD" \
  .env* --include=".env*" 2>/dev/null | grep -v example | head -10
```

### 6.8 HTTPS y cookies
```bash
# Detectar configuración de cookies seguras
grep -rn "httpOnly\|secure:\|sameSite\|SameSite" . --include="*.ts" --include="*.js" \
  | grep -v node_modules | head -10

# Detectar si se usa HTTPS en config
grep -rn "http://\|localhost" . --include="*.ts" --include="*.env*" \
  | grep -v node_modules | grep -v test | grep -v example | head -10
```

## Criterios de puntuación

| Puntuación | Criterio |
|------------|---------|
| 8-10 🟢 | Sin secrets, RLS activo, validación de inputs, headers de seguridad, sin vulnerabilidades críticas |
| 4-7 🟡 | Sin secrets en código pero configuración mejorable, algunos endpoints sin auth |
| 0-3 🔴 | Secrets hardcodeados, sin RLS, endpoints sin auth, vulnerabilidades críticas, service_role en frontend |

## Métricas a registrar
- `hardcoded_secrets_count`
- `env_files_in_git` (boolean)
- `unprotected_api_routes_count`
- `dangerously_set_inner_html_count`
- `npm_critical_vulns`
- `npm_high_vulns`
- `npm_moderate_vulns`
- `cors_configured` (boolean)
- `security_headers_configured` (boolean)
- `service_role_in_frontend` (boolean)
- `public_env_with_secrets` (boolean)
