# Área 07 — CI/CD y Entornos

## Qué evaluar

### 7.1 Estructura de ramas
```bash
# Ver ramas existentes
git branch -a 2>/dev/null

# Verificar ramas esperadas
git branch -a 2>/dev/null | grep -E "main|master|develop|staging|pre|production"

# Ver rama actual
git branch --show-current 2>/dev/null

# Ver última actividad por rama
git for-each-ref --sort=-committerdate refs/heads/ --format='%(refname:short) %(committerdate:relative) %(subject)' 2>/dev/null | head -10

# Ver si hay ramas de IA (ai/*)
git branch -a 2>/dev/null | grep "ai/"
```

### 7.2 Pipeline CI/CD — análisis local
```bash
# Ver workflows de GitHub Actions
ls .github/workflows/ 2>/dev/null
cat .github/workflows/*.yml 2>/dev/null

# Detectar qué pasos tiene cada workflow
grep -rn "run:\|uses:" .github/workflows/ 2>/dev/null | head -40

# Detectar si hay lint, tests, build, deploy en CI
echo "=== Lint en CI ===" && grep -rn "lint" .github/workflows/ 2>/dev/null | head -5
echo "=== Tests en CI ===" && grep -rn "test\|vitest\|jest\|playwright" .github/workflows/ 2>/dev/null | head -5
echo "=== Build en CI ===" && grep -rn "build" .github/workflows/ 2>/dev/null | head -5
echo "=== Deploy en CI ===" && grep -rn "deploy\|vercel\|supabase" .github/workflows/ 2>/dev/null | head -5
echo "=== Checks de seguridad en CI ===" && grep -rn "audit\|sonar\|snyk\|trivy" .github/workflows/ 2>/dev/null | head -5

# Detectar si hay migration check en CI
grep -rn "migration\|supabase db" .github/workflows/ 2>/dev/null | head -5
```

### 7.3 GitHub — estado real (requiere HAS_GITHUB_TOKEN)
```bash
# Solo si HAS_GITHUB_TOKEN=true

# Ver estado de branch protection
gh api repos/{owner}/{repo}/branches/main/protection 2>/dev/null | python3 -c "
import json,sys
data=json.load(sys.stdin)
print('Required reviews:', data.get('required_pull_request_reviews',{}).get('required_approving_review_count','No configurado'))
print('Required status checks:', [s for s in data.get('required_status_checks',{}).get('contexts',[])])
print('Enforce admins:', data.get('enforce_admins',{}).get('enabled', False))
" 2>/dev/null

# Ver últimas ejecuciones de CI
gh run list --limit 10 2>/dev/null

# Estado del último run
gh run view $(gh run list --limit 1 --json databaseId --jq '.[0].databaseId') 2>/dev/null

# Ver PRs abiertos
gh pr list 2>/dev/null

# Ver PRs sin revisar
gh pr list --review-requested @me 2>/dev/null
```

### 7.4 Vercel — estado real (requiere HAS_VERCEL_TOKEN)
```bash
# Solo si HAS_VERCEL_TOKEN=true

# Ver deployments recientes
vercel list 2>/dev/null | head -20

# Ver entornos configurados
vercel env list 2>/dev/null

# Ver dominios
vercel domains list 2>/dev/null

# Detectar si hay Preview (develop) y Production (main) separados
vercel list 2>/dev/null | grep -E "Production|Preview|Development"

# Variables de entorno por entorno
vercel env list production 2>/dev/null | head -10
vercel env list preview 2>/dev/null | head -10
vercel env list development 2>/dev/null | head -10
```

### 7.5 Análisis local de configuración de entornos
```bash
# Detectar archivos .env por entorno
ls -la .env* 2>/dev/null

# Ver cuántas variables tiene cada env
wc -l .env* 2>/dev/null

# Detectar si hay separación de variables por entorno
cat .env.example 2>/dev/null

# Detectar configuración de Vercel local
cat vercel.json 2>/dev/null
cat .vercelignore 2>/dev/null
```

### 7.6 Versiones desplegadas y trazabilidad
```bash
# Detectar tabla deployment_version en migraciones
grep -rn "deployment_version\|deployed_at\|deploy_version" \
  supabase/migrations/ src/ --include="*.sql" --include="*.ts" 2>/dev/null | head -10

# Detectar si se registra el git commit en los deployments
grep -rn "VERCEL_GIT_COMMIT_SHA\|GITHUB_SHA\|git_commit\|gitCommit" \
  . --include="*.ts" --include="*.js" --include="*.env*" | grep -v node_modules | head -10

# Ver tags de versión en git
git tag 2>/dev/null | head -10
git log --oneline --decorate | head -10
```

### 7.7 Frecuencia y calidad de commits
```bash
# Ver frecuencia de commits por semana
git log --since="4 weeks ago" --oneline 2>/dev/null | wc -l

# Ver autores de commits
git shortlog -sn --since="4 weeks ago" 2>/dev/null | head -10

# Ver si los mensajes de commit son descriptivos
git log --oneline --since="2 weeks ago" 2>/dev/null | head -20

# Detectar commits directos a main (bypassing PR)
git log main --no-merges --since="4 weeks ago" --oneline 2>/dev/null | head -10
```

## Criterios de puntuación

| Puntuación | Criterio |
|------------|---------|
| 8-10 🟢 | Pipeline completo (lint+test+build+deploy), branch protection, entornos separados, trazabilidad de versiones |
| 4-7 🟡 | CI básico, algunas protecciones de rama, entornos parcialmente separados |
| 0-3 🔴 | Sin CI/CD, sin branch protection, sin entornos separados, commits directos a main |

## Métricas a registrar
- `has_main_branch` (boolean)
- `has_develop_branch` (boolean)
- `has_ai_branches` (boolean)
- `branch_protection_main` (boolean)
- `branch_protection_develop` (boolean)
- `ci_has_lint` (boolean)
- `ci_has_tests` (boolean)
- `ci_has_build` (boolean)
- `ci_has_deploy` (boolean)
- `ci_has_migration_check` (boolean)
- `ci_has_security_scan` (boolean)
- `vercel_envs_separated` (boolean)
- `deployment_version_table` (boolean)
- `commits_last_4_weeks`
- `direct_commits_to_main_count`
- `workflow_files_count`
