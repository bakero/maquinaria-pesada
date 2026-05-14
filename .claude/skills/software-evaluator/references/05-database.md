# Área 05 — Base de Datos

## Qué evaluar

### 5.1 Esquema y migraciones
```bash
# Ver migraciones existentes
find . -path "*/supabase/migrations/*" -o -path "*/migrations/*" -o -path "*/db/migrations/*" \
  | grep -v node_modules | sort | head -30

# Contar migraciones
find . -name "*.sql" -path "*/migrations/*" | grep -v node_modules | wc -l

# Ver última migración
find . -name "*.sql" -path "*/migrations/*" | grep -v node_modules | sort | tail -3

# Estado de migraciones con Supabase CLI
supabase migration list 2>/dev/null || echo "supabase CLI no disponible"

# Detectar si hay sistema de migraciones versionado
cat supabase/config.toml 2>/dev/null | head -20
ls supabase/ 2>/dev/null
```

### 5.2 Row Level Security (RLS) — CRÍTICO
```bash
# Ver políticas RLS en migraciones
grep -rn "enable row level security\|create policy\|alter table.*enable\|RLS" \
  supabase/migrations/ --include="*.sql" 2>/dev/null | head -30

# Contar tablas con RLS activado
grep -rn "enable row level security" supabase/migrations/ --include="*.sql" 2>/dev/null | wc -l

# Contar tablas referenciadas en código frontend (deben tener RLS)
grep -rn "\.from(" src/ --include="*.ts" --include="*.tsx" 2>/dev/null \
  | grep -v "node_modules" | grep -oP "\.from\('\K[^']+" | sort | uniq

# Verificar con Supabase CLI si RLS está activo
supabase db inspect --schema=public 2>/dev/null | grep -i "rls\|security" | head -20
```

### 5.3 Conexión real a Supabase (requiere HAS_SUPABASE_TOKEN)
```bash
# Solo ejecutar si HAS_SUPABASE_TOKEN=true

# Listar tablas y estado RLS
supabase db inspect 2>/dev/null

# Ver funciones y triggers
supabase functions list 2>/dev/null

# Estado del proyecto
supabase status 2>/dev/null

# Ver si hay entorno de staging separado
supabase projects list 2>/dev/null
```

### 5.4 Índices y rendimiento
```bash
# Detectar si hay índices definidos en migraciones
grep -rn "create index\|CREATE INDEX" supabase/migrations/ --include="*.sql" 2>/dev/null | head -20

# Detectar queries sin índice (columnas filtradas frecuentemente sin índice)
grep -rn "\.eq(\|\.filter(\|\.match(" src/ --include="*.ts" --include="*.tsx" 2>/dev/null \
  | grep -v node_modules | head -20
```

### 5.5 Backups y rollback
```bash
# Ver si hay scripts de backup
find . -name "*backup*" -o -name "*seed*" -o -name "*restore*" \
  | grep -v node_modules | grep -v dist | head -10

# Detectar patrón expand/contract en migraciones
grep -rn "rename\|drop column\|alter column" supabase/migrations/ --include="*.sql" 2>/dev/null | head -10

# Ver si hay seeds de datos
find . -path "*/supabase/seed*" -o -name "seed.sql" -o -name "seed.ts" \
  | grep -v node_modules | head -5
```

### 5.6 Tablas de auditoría y versionado
```bash
# Detectar tablas de audit
grep -rn "audit_log\|app_events\|deployment_version\|schema_version" \
  supabase/migrations/ --include="*.sql" 2>/dev/null | head -10

# Detectar triggers de auditoría
grep -rn "create trigger\|CREATE TRIGGER" supabase/migrations/ --include="*.sql" 2>/dev/null | head -10
```

### 5.7 Separación PRE / PRO
```bash
# Detectar si hay variables de entorno distintas para cada entorno
grep -rn "SUPABASE_URL\|NEXT_PUBLIC_SUPABASE" .env* 2>/dev/null | grep -v ".example"
cat .env.local 2>/dev/null | grep SUPABASE
cat .env.development 2>/dev/null | grep SUPABASE
cat .env.production 2>/dev/null | grep SUPABASE

# Detectar si hay proyecto Supabase de staging
supabase projects list 2>/dev/null | grep -i "staging\|pre\|dev\|test"
```

### 5.8 Datos sensibles en código
```bash
# Detectar service_role key en código fuente
grep -rn "service_role\|eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" src/ \
  --include="*.ts" --include="*.tsx" --include="*.js" 2>/dev/null | head -5

# Detectar acceso a Supabase admin desde frontend
grep -rn "createClient.*service_role\|supabaseAdmin" src/ \
  --include="*.tsx" --include="*.ts" 2>/dev/null | grep -v "api\|server\|backend" | head -10
```

## Criterios de puntuación

| Puntuación | Criterio |
|------------|---------|
| 8-10 🟢 | RLS activo, migraciones versionadas, tablas de audit, backup, entornos separados |
| 4-7 🟡 | Algunas migraciones, RLS parcial, sin audit log, entornos mezclados |
| 0-3 🔴 | Sin migraciones, sin RLS, service_role en frontend, sin backup, sin separación PRE/PRO |

## Métricas a registrar
- `migrations_count`
- `tables_with_rls_count`
- `tables_without_rls_count`
- `has_audit_log` (boolean)
- `has_deployment_version_table` (boolean)
- `pre_pro_separated` (boolean)
- `service_role_in_frontend` (boolean)
- `has_seed_data` (boolean)
- `indexes_count`
- `has_backup_strategy` (boolean)
