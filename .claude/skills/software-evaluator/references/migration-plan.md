# Plan Maestro de Migración — Referencia embebida

Este archivo contiene el mapa completo de PRs del Plan Maestro.
Úsalo para vincular cada hallazgo de la evaluación con el PR que lo resuelve.

## Formato de referencia en informes
```
→ Plan Maestro: PR <número> — "<nombre>" (Bloque <1|2|3>)
```

---

## Sprint 0 — Arranque

| PR | Nombre | Qué resuelve |
|----|--------|-------------|
| S0 | Auditoría real del código | Incertidumbre sobre el estado real del código. Inventario completo. Validación de la estimación. |

---

## Bloque 1 — Estabilización y control (PRs 0–10)
**Objetivo:** Sistema entendible, seguro y testeable. Beta testers protegidos.

| PR | Nombre | Qué resuelve en la evaluación |
|----|--------|-------------------------------|
| PR 0 | Auditoría de secrets + dependencias npm | 🔴 Secrets hardcodeados · 🔴 .env en git · 🔴 Vulnerabilidades críticas npm · 🔴 service_role en frontend |
| PR 1 | CLAUDE.md + guardarraíles + docs legales iniciales | 🔴 Sin reglas de trabajo para la IA · 🔴 Sin documentación legal (RGPD/AI Act) |
| PR 2 | Auditoría técnica y funcional completa | 🟡 Sin mapa de funcionalidades · 🟡 Sin inventario de pantallas · 🟡 Sin documentación de arquitectura |
| PR 3 | Detección automática de funcionalidades | 🟡 Sin mapa de rutas frontend · 🟡 Sin inventario de componentes |
| PR 4 | Inventario pantallas / rutas / navegación | 🟡 Sin documentación de navegación y rutas |
| PR 5 | Inventario backend / Supabase | 🟡 Sin mapa de endpoints · 🟡 Sin clasificación de datos para RGPD |
| PR 6 | Estrategia de datos PRE + anonimización | 🔴 Sin entorno PRE · 🔴 Datos reales en entorno de desarrollo |
| PR 7 | Baseline Playwright + smoke tests | 🔴 Sin tests E2E · 🔴 Sin smoke tests · 🔴 Cobertura E2E < 70% |
| PR 8 | E2E flujos críticos + tests de autorización RLS | 🔴 Sin tests de auth · 🔴 Sin tests de acceso cruzado entre usuarios |
| PR 9 | CI GitHub Actions completo | 🔴 Sin pipeline CI · 🔴 Sin lint en CI · 🔴 Sin tests en CI · 🔴 Sin quality gate |
| PR 10 | Entornos develop/pre + ramas protegidas | 🔴 Sin branch protection · 🔴 Commits directos a main · 🔴 Sin rama develop |

---

## Bloque 2 — Operación, seguridad y despliegue controlado (PRs 11–23)
**Objetivo:** Sistema observable, operable, con calidad controlada y cumplimiento RGPD.

| PR | Nombre | Qué resuelve en la evaluación |
|----|--------|-------------------------------|
| PR 11 | Supabase PRE / PRO separados | 🔴 Base de datos PRE y PRO compartida · 🔴 Sin aislamiento de datos de prueba |
| PR 12 | Modelo feature_flags | 🟡 Sin control de activación de funcionalidades · 🟡 Deploy = release |
| PR 13 | Servicio feature-flags + consola admin mínima | 🟡 Sin consola de operación · 🟡 Sin control de flags en producción |
| PR 14 | Test Center en consola + Release Center | 🟡 Sin visibilidad del estado de tests por entorno |
| PR 15 | deployment_version + trazabilidad de versiones | 🔴 Sin trazabilidad de versiones desplegadas · 🔴 Sin correlación frontend/backend/DB |
| PR 16 | Logs centralizados frontend + backend (sin PII) | 🔴 Sin logging estructurado · 🔴 Solo console.log · 🔴 Sin correlation_id |
| PR 17 | Audit log de datos sensibles (RGPD) | 🔴 Sin audit_log de operaciones sobre datos personales (obligatorio RGPD) |
| PR 18 | Dashboard técnico / operativo | 🟡 Sin visibilidad operativa en tiempo real |
| PR 19 | SonarQube + módulo de deuda técnica en consola | 🟡 Sin medición de deuda técnica · 🟡 Sin quality gate automatizado |
| PR 20 | Plan RLS tabla por tabla | 🔴 Tablas sin RLS identificadas pero sin plan de activación |
| PR 21 | RLS primera tabla no crítica | 🔴 Tablas con datos personales sin RLS activo |
| PR 22 | Endpoints RGPD: data-export + borrado de usuario | 🔴 Sin derecho de acceso implementado · 🔴 Sin derecho al olvido (obligatorio RGPD) |
| PR 23 | Runbooks: rollback, incidencias, data breach response | 🔴 Sin protocolo de brecha de datos · 🟡 Sin runbooks operativos |

---

## Bloque 3 — Modularización y migración progresiva (PRs 24–29)
**Objetivo:** Arquitectura modular, preparada para microservicios.

| PR | Nombre | Qué resuelve en la evaluación |
|----|--------|-------------------------------|
| PR 24 | Inventario visual UI + tokens de diseño | 🟡 Sin sistema de componentes · 🟡 Sin tokens de diseño |
| PR 25 | Componentes base + primera pantalla migrada | 🟡 Componentes duplicados · 🟡 Sin librería de componentes compartidos |
| PR 26 | Primer módulo backend en shadow mode | 🟡 Sin separación de dominios en backend · 🟡 Sin módulos con ownership claro |
| PR 27 | Primer rollout progresivo controlado | 🟡 Sin despliegue gradual · 🟡 Sin validación progresiva de cambios |
| PR 28 | Primer microservicio extraído (notificaciones/exports) | 🟡 Monolito sin modularizar · 🟡 Sin separación de servicios independientes |
| PR 29 | Limpieza de código viejo + documentación final viva | 🟡 Dead code extenso · 🟡 Documentación no actualizada |

---

## Mapa rápido: hallazgo → PR

### Seguridad
| Hallazgo | PR |
|----------|----|
| Secrets hardcodeados | PR 0 |
| .env en git | PR 0 |
| Sin RLS | PR 20, 21 |
| service_role en frontend | PR 0, PR 5 |
| Sin validación de inputs | PR 2, PR 9 |
| Sin CORS configurado | PR 1, PR 9 |
| Sin derecho al olvido | PR 22 |
| Sin audit_log | PR 17 |

### Tests
| Hallazgo | PR |
|----------|----|
| Sin tests | PR 7, PR 8 |
| Sin E2E | PR 7 |
| Sin tests de auth | PR 8 |
| Tests no en CI | PR 9 |
| Cobertura < 50% | PR 7, PR 8 |

### CI/CD y entornos
| Hallazgo | PR |
|----------|----|
| Sin pipeline CI | PR 9 |
| Sin branch protection | PR 10 |
| Sin rama develop | PR 10 |
| Sin entorno PRE | PR 6, PR 11 |
| Commits directos a main | PR 10 |
| Sin trazabilidad versiones | PR 15 |

### Calidad de código
| Hallazgo | PR |
|----------|----|
| Sin linting | PR 9 |
| Archivos >300 líneas | PR 25, PR 26 |
| Dead code extenso | PR 29 |
| Sin deuda técnica medida | PR 19 |

### Documentación
| Hallazgo | PR |
|----------|----|
| Sin README útil | PR 2 |
| Sin documentación de arquitectura | PR 2, PR 3, PR 4, PR 5 |
| Sin .env.example | PR 0 |
| Sin runbooks | PR 23 |

### Base de datos
| Hallazgo | PR |
|----------|----|
| Sin migraciones | PR 5, PR 6 |
| Sin RLS | PR 20, PR 21 |
| Sin separación PRE/PRO | PR 6, PR 11 |
| Sin audit_log | PR 17 |
| Sin deployment_version | PR 15 |

### Observabilidad
| Hallazgo | PR |
|----------|----|
| Solo console.log | PR 16 |
| Sin Sentry/similar | PR 16 |
| Sin correlation_id | PR 16 |
| Sin health check | PR 16, PR 18 |
| Sin deployment_version | PR 15 |

---

## Mapa rápido: hallazgos de IA → PR

### Seguridad y arquitectura de IA
| Hallazgo | PR |
|----------|----|
| API key de IA expuesta en frontend | PR 0 (secrets) |
| Sin proxy propio — llamada directa a IA desde frontend | PR 1 (CLAUDE.md) + Sin PR asignado → considerar añadir |
| Datos sensibles enviados a IA sin base legal | PR 5 (inventario backend) + PR 22 (endpoints RGPD) |
| Prompts dispersos sin centralizar | PR 2 (auditoría funcional) |
| Sin gestión de errores en llamadas a IA | PR 9 (CI GitHub Actions) |
| Sin rate limiting en endpoints de IA | PR 13 (consola admin) |

### Legal y compliance de IA
| Hallazgo | PR |
|----------|----|
| Sin informar al usuario que interactúa con IA | PR 1 (docs legales iniciales) |
| Sin DPA con proveedor de IA | PR 1 (docs legales iniciales) |
| Sin base legal para tratamiento de datos con IA | PR 1 + PR 5 |
| IA no incluida en el RAT | PR 1 (data-processing-register.md) |
| Sin clasificación AI Act documentada | PR 2 (ai-act-classification.md) |
| Sin mecanismo de supervisión humana | Sin PR asignado → considerar añadir |
| Sin política de retención de conversaciones | PR 17 (audit log) + Sin PR asignado |
| Transferencia internacional sin documentar | PR 1 (docs legales) |

### Calidad de integración de IA
| Hallazgo | PR |
|----------|----|
| Sin pruebas sobre comportamiento de la IA | PR 7, PR 8 (tests) |
| Sin trazabilidad de qué modelo se usó en cada respuesta | PR 15 (deployment_version) |
| Prompts o respuestas de IA en logs con PII | PR 16 (logs sin PII) |
| Conversaciones de IA no auditadas | PR 17 (audit log) |
| Sin observabilidad de uso de IA (tokens, latencia, errores) | PR 18 (dashboard técnico) |
