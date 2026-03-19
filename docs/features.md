# Checklist funcional

Fuente estructurada: `docs/features.json`.

## Ruta crítica principal
- FTR-002
- FTR-003
- FTR-004
- FTR-005
- FTR-006

## Estado actual
| ID | Función | Prioridad | Estado | Evidencias | Observaciones |
| --- | --- | --- | --- | --- | --- |
| FTR-002 | Se puede consultar healthcheck del servicio HTTP opcional | Alta | Verificada | `clinicdesk/web/healthz.py`, `tests/test_healthz.py` | Mantiene contrato mínimo de disponibilidad para despliegues auxiliares. |
| FTR-003 | Se puede autenticar usuario y bloquear tras intentos fallidos | Alta | Verificada | `clinicdesk/app/security/auth.py`, `tests/test_auth_service.py` | Servicio de autenticación cubierto unitariamente. |
| FTR-004 | Se puede crear y consultar citas clínicas | Alta | Parcial | `clinicdesk/app/application/usecases/crear_cita.py`, `tests/test_citas.py`, `tests/ui/test_pacientes_viewmodel_puro.py` | Core validado; falta evidencia E2E integral del ciclo completo en UI. |
| FTR-005 | Se puede ejecutar pipeline ML de riesgo de citas | Alta | Parcial | `tests/test_ml_training.py`, `tests/test_train_calibration_integration.py`, `tests/test_drift_report.py` | Core analítico cubierto; falta un escenario E2E extremo a extremo. |
| FTR-006 | Se puede exportar KPIs y resultados en CSV | Alta | Verificada | `clinicdesk/app/application/usecases/export_kpis_csv.py`, `tests/test_export_kpis_csv.py` | Exportación contractual validada. |
| FTR-007 | Se puede exportar auditoría de accesos con controles | Media | Verificada | `clinicdesk/app/application/usecases/exportar_auditoria_csv.py`, `tests/test_exportar_auditoria_csv_usecase.py` | RBAC y sanitización cubiertos. |
| FTR-008 | Se puede rotar claves criptográficas de campos sensibles | Media | Parcial | `scripts/security_cli.py`, `tests/test_security_cli.py` | CLI y guardrails cubiertos; falta escenario operacional completo automatizado. |
