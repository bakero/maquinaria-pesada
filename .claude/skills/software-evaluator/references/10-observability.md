# Área 10 — Observabilidad y Monitorización

## Qué evaluar

### 10.1 Logging en frontend
```bash
# Detectar sistema de logging en frontend
grep -rn "Sentry\|@sentry\|Highlight\|LogRocket\|Datadog\|Bugsnag\|Rollbar" \
  package.json src/ --include="*.ts" --include="*.tsx" 2>/dev/null | grep -v node_modules | head -10

# Detectar console.log (señal de falta de logging estructurado)
grep -rn "console\.log\|console\.error\|console\.warn" src/ \
  --include="*.ts" --include="*.tsx" --include="*.js" 2>/dev/null | grep -v node_modules | wc -l

# Detectar si hay captura de errores (Error Boundary)
grep -rn "ErrorBoundary\|componentDidCatch\|error.tsx\|error.jsx" src/ \
  --include="*.tsx" --include="*.jsx" --include="*.ts" 2>/dev/null | head -10
```

### 10.2 Logging en backend
```bash
# Detectar sistema de logging en backend
grep -rn "pino\|winston\|morgan\|bunyan\|@logtail\|Logtail" \
  package.json . --include="*.ts" --include="*.js" 2>/dev/null | grep -v node_modules | head -10

# Detectar si los logs incluyen campos estructurados clave
grep -rn "requestId\|correlationId\|correlation_id\|request_id" \
  . --include="*.ts" --include="*.js" 2>/dev/null | grep -v node_modules | head -5

grep -rn "userId\|user_id\|endpoint\|latency\|statusCode\|status_code" \
  . --include="*.ts" --include="*.js" 2>/dev/null | grep -v node_modules | head -10

# Detectar si se sanitizan los logs (sin PII)
grep -rn "sanitize\|redact\|mask\|omit.*password\|omit.*email" \
  . --include="*.ts" --include="*.js" 2>/dev/null | grep -v node_modules | head -5
```

### 10.3 Trazabilidad de versiones
```bash
# Detectar tabla deployment_version
grep -rn "deployment_version\|deploymentVersion" \
  supabase/ src/ --include="*.sql" --include="*.ts" 2>/dev/null | head -10

# Detectar si se registra el git commit al desplegar
grep -rn "VERCEL_GIT_COMMIT_SHA\|GITHUB_SHA\|GIT_COMMIT" \
  . --include="*.ts" --include="*.js" --include="*.env*" | grep -v node_modules | head -5

# Detectar audit_log
grep -rn "audit_log\|auditLog\|audit_trail" \
  supabase/ src/ --include="*.sql" --include="*.ts" 2>/dev/null | head -10
```

### 10.4 Alertas y monitorización
```bash
# Detectar si hay configuración de alertas
grep -rn "alert\|alerting\|notification.*error\|on_error" \
  .github/workflows/ . --include="*.yml" --include="*.yaml" 2>/dev/null | grep -v node_modules | head -10

# Detectar health checks
grep -rn "healthcheck\|health-check\|/health\|/ping\|/status" \
  . --include="*.ts" --include="*.js" 2>/dev/null | grep -v node_modules | head -10

# Detectar uptime monitoring
find . -name "*.yml" -o -name "*.yaml" | xargs grep -l "uptime\|monitor\|pingdom\|betterstack" 2>/dev/null
```

### 10.5 Métricas de rendimiento
```bash
# Detectar si se miden tiempos de respuesta
grep -rn "performance\|latency\|response_time\|responseTime\|Date.now\|perf_hooks" \
  . --include="*.ts" --include="*.js" 2>/dev/null | grep -v node_modules | head -10

# Detectar Web Vitals
grep -rn "web-vitals\|getCLS\|getFID\|getLCP\|getFCP\|getTTFB" \
  . --include="*.ts" --include="*.tsx" 2>/dev/null | head -5
```

## Criterios de puntuación
| Puntuación | Criterio |
|------------|---------|
| 8-10 🟢 | Sentry/similar activo, logging estructurado, sin PII en logs, deployment_version, audit_log, health check |
| 4-7 🟡 | Algunos logs, Sentry configurado parcialmente, sin audit_log |
| 0-3 🔴 | Solo console.log, sin monitorización, sin audit_log, sin trazabilidad de versiones |

## Métricas a registrar
- `frontend_monitoring_tool` (nombre o null)
- `backend_logging_tool` (nombre o null)
- `console_log_count`
- `has_correlation_id` (boolean)
- `has_error_boundary` (boolean)
- `has_deployment_version_table` (boolean)
- `has_audit_log` (boolean)
- `has_health_check` (boolean)
- `has_web_vitals` (boolean)
- `pii_in_logs_risk` (boolean)
