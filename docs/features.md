# Checklist funcional

Fuente estructurada: `docs/features.json`.

## Ruta crítica principal
- FTR-003
- FTR-004
- FTR-005
- FTR-006

## Estado actual
| ID | Función | Prioridad | Estado | Evidencias | Observaciones |
| --- | --- | --- | --- | --- | --- |
| FTR-003 | Se puede autenticar usuario y bloquear tras intentos fallidos | Alta | Verificada | `clinicdesk/app/security/auth.py`, `tests/test_auth_service.py`, `tests/test_login_dialog_ui.py`, `tests/test_session_controller.py` | La UI desktop PySide6 ya cubre first-run, login válido, bloqueo determinista y demo permitido/prohibido; la transición post-login está validada con pruebas fuertes del controlador. El tramo E2E sube solo a parcial porque todavía no hay recorrido completo con `main()` y logout extremo a extremo. |
| FTR-004 | Se puede crear y consultar citas clínicas | Alta | Verificada | `clinicdesk/app/application/usecases/crear_cita.py`, `tests/test_citas.py`, `tests/ui/test_pacientes_viewmodel_puro.py`, `tests/ui/test_ruta_critica_desktop_smoke.py` | La ruta crítica desktop ya tiene smoke PySide6 con DB temporal que crea una cita por la vía UI soportada y la verifica en el listado. |
| FTR-005 | Se puede ejecutar pipeline ML de riesgo de citas | Alta | Parcial | `tests/test_ml_training.py`, `tests/test_train_calibration_integration.py`, `tests/test_drift_report.py`, `tests/ui/test_ruta_critica_desktop_smoke.py`, `tests/test_prediccion_operativa_facade_integracion.py` | Se cubre el entrenamiento mínimo desde la pantalla desktop y el facade real sobre datos efímeros; sigue pendiente un E2E total con navegación completa y background real. |
| FTR-006 | Se puede exportar KPIs y resultados en CSV | Alta | Verificada | `clinicdesk/app/application/usecases/export_kpis_csv.py`, `tests/test_export_kpis_csv.py` | Exportación contractual validada. |
| FTR-007 | Se puede exportar auditoría de accesos con controles | Media | Verificada | `clinicdesk/app/application/usecases/exportar_auditoria_csv.py`, `tests/test_exportar_auditoria_csv_usecase.py` | RBAC y sanitización cubiertos. |
| FTR-008 | Se puede rotar claves criptográficas de campos sensibles | Media | Parcial | `scripts/security_cli.py`, `tests/test_security_cli.py` | CLI y guardrails cubiertos; falta escenario operacional completo automatizado. |
