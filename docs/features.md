# Checklist funcional verificable de ClinicDesk

Este documento describe funciones **reales** identificadas en el repositorio y su estado de verificación actual.

Fuente estructurada (fuente de verdad): `docs/features.json`.

## Ruta crítica principal del producto

1. **FTR-001** — Lanzar demo operativa.
2. **FTR-002** — Verificar salud del servicio web (`/healthz`).
3. **FTR-003** — Autenticar usuario y aplicar bloqueo por intentos fallidos.
4. **FTR-004** — Crear y consultar citas clínicas.
5. **FTR-005** — Ejecutar pipeline ML de riesgo.
6. **FTR-006** — Exportar resultados/KPIs a CSV.

## Inventario funcional (estado global)

| ID | Función | Prioridad | Estado global | Evidencia actual | Observaciones / bloqueos |
|---|---|---|---|---|---|
| FTR-001 | Se puede lanzar la demo operativa | Alta | Parcial | `scripts/run_demo.py`, `tests/test_run_demo.py` | La orquestación está probada, pero falta evidencia E2E GUI pasando para el flujo completo. |
| FTR-002 | Se puede consultar healthcheck del servicio web | Alta | Verificada | `clinicdesk/web/healthz.py`, `tests/test_healthz.py` | Contrato HTTP básico cubierto; validaciones de seguridad avanzadas quedan parciales. |
| FTR-003 | Se puede autenticar usuario y bloquear tras intentos fallidos | Alta | Verificada | `clinicdesk/app/security/auth.py`, `tests/test_auth_service.py` | Servicio validado por tests unitarios; no se confirmó en esta iteración una prueba E2E con UI. |
| FTR-004 | Se puede crear y consultar citas clínicas | Alta | Parcial | `clinicdesk/app/application/usecases/crear_cita.py`, `tests/test_citas.py` | Lógica de negocio verificada, cobertura UI parcial y sin flujo E2E integral confirmado. |
| FTR-005 | Se puede ejecutar pipeline ML de riesgo de citas | Alta | Parcial | `tests/test_ml_training.py`, `tests/test_train_calibration_integration.py`, `tests/test_drift_report.py` | Core analítico verificado; no hay evidencia de E2E completo con UI operativa. |
| FTR-006 | Se puede exportar KPIs y resultados en CSV | Alta | Verificada | `clinicdesk/app/application/usecases/export_kpis_csv.py`, `tests/test_export_kpis_csv.py` | Export contractual verificado; falta prueba E2E con consumo final externo automatizado. |
| FTR-007 | Se puede exportar auditoría de accesos con controles | Media | Verificada | `clinicdesk/app/application/usecases/exportar_auditoria_csv.py`, `tests/test_exportar_auditoria_csv_usecase.py` | RBAC/sanitización cubiertos; pendiente E2E desde punto de acceso final. |
| FTR-008 | Se puede rotar claves criptográficas de campos sensibles | Media | Parcial | `scripts/security_cli.py`, `tests/test_security_cli.py` | Flujo CLI y controles PII verificados; sin evidencia E2E de operación en despliegue real. |

## Estados permitidos

- Verificada
- Parcial
- No verificada
- No implementada
