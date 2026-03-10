# Checklist funcional verificable de ClinicDesk

Este documento describe funciones **reales** identificadas en el repositorio y su estado de verificación actual.

Fuente estructurada (fuente de verdad): `docs/features.json`.

## Ruta crítica principal del producto

1. **FTR-001** — Se puede lanzar la demo operativa.
2. **FTR-002** — Se puede consultar healthcheck del servicio web.
3. **FTR-003** — Se puede autenticar usuario y bloquear tras intentos fallidos.
4. **FTR-004** — Se puede crear y consultar citas clínicas.
5. **FTR-005** — Se puede ejecutar pipeline ML de riesgo de citas.
6. **FTR-006** — Se puede exportar KPIs y resultados en CSV.

## Inventario funcional (estado global)

| ID | Función | Prioridad | Estado global | Evidencia actual | Observaciones / bloqueos |
|---|---|---|---|---|---|
| FTR-001 | Se puede lanzar la demo operativa | Alta | Parcial | `scripts/run_demo.py, tests/test_run_demo.py` | La orquestación y manejo de fallos está probada; no hay evidencia de E2E GUI real pasando en CI para este flujo completo. |
| FTR-002 | Se puede consultar healthcheck del servicio web | Alta | Verificada | `clinicdesk/web/healthz.py, tests/test_healthz.py` | Cobertura de contrato HTTP básico presente; falta evidencia de hardening adicional (auth/rate-limit) para marcar validaciones como Verificada. |
| FTR-003 | Se puede autenticar usuario y bloquear tras intentos fallidos | Alta | Verificada | `clinicdesk/app/security/auth.py, tests/test_auth_service.py` | El contrato del servicio de autenticación está cubierto unitariamente; no se confirmó flujo integral con pantalla de login en esta iteración. |
| FTR-004 | Se puede crear y consultar citas clínicas | Alta | Parcial | `clinicdesk/app/application/usecases/crear_cita.py, tests/test_citas.py, tests/ui/test_pacientes_viewmodel_puro.py` | Hay cobertura robusta de caso de uso y queries; la verificación UI existe en componentes aislados, sin E2E extremo a extremo confirmado para el ciclo completo de agenda. |
| FTR-005 | Se puede ejecutar pipeline ML de riesgo de citas | Alta | Parcial | `tests/test_ml_training.py, tests/test_train_calibration_integration.py, tests/test_drift_report.py` | Core analítico con buena cobertura; no hay evidencia en este corte de un escenario E2E automatizado que recorra UI + pipeline completo. |
| FTR-006 | Se puede exportar KPIs y resultados en CSV | Alta | Verificada | `clinicdesk/app/application/usecases/export_kpis_csv.py, tests/test_export_kpis_csv.py` | Contrato de exportación probado; pendiente verificar consumo E2E con herramienta externa de reporting en entorno automatizado. |
| FTR-007 | Se puede exportar auditoría de accesos con controles | Media | Verificada | `clinicdesk/app/application/usecases/exportar_auditoria_csv.py, tests/test_exportar_auditoria_csv_usecase.py` | Reglas de autorización y sanitización están cubiertas; falta test de flujo completo desde punto de acceso final de usuario. |
| FTR-008 | Se puede rotar claves criptográficas de campos sensibles | Media | Parcial | `scripts/security_cli.py, tests/test_security_cli.py` | Cobertura fuerte de contrato CLI y no exposición de PII; no hay escenario E2E operacional de rotación dentro de despliegue real automatizado. |
| FTR-009 | WEB_LORE_V1 en Next.js como slice extremo a extremo | Alta | No implementada | `N/A (estructura Next.js/Django no presente en este repositorio)` | Bloqueada en esta rama: no existen rutas frontend/ ni web/apps/lore; el repositorio activo es una app de escritorio Python + API demo, por lo que no se puede implementar el slice solicitado sin cambiar de código base. |

## Estados permitidos

- Verificada
- Parcial
- No verificada
- No implementada
