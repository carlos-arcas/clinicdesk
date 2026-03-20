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
| FTR-003 | Se puede autenticar usuario y bloquear tras intentos fallidos | Alta | Verificada | `clinicdesk/app/security/auth.py`, `tests/test_auth_service.py`, `tests/test_login_dialog_ui.py`, `tests/test_session_controller.py`, `tests/test_main_auth_flow.py` | La autenticación desktop ya cubre servicio, diálogo y transición post-login; además ahora existe una prueba headless controlada del wiring real extraído desde `clinicdesk/app/main.py` que recorre apertura de sesión, visibilidad de ventana principal, logout, reapertura satisfactoria, cancelación de relogin y error de transición con feedback. `e2e` se mantiene en parcial porque todavía no se automatiza `main()` hasta `app.exec()` y salida completa del loop real. |
| FTR-004 | Se puede crear y consultar citas clínicas | Alta | Verificada | `clinicdesk/app/application/usecases/crear_cita.py`, `tests/test_citas.py`, `tests/ui/test_pacientes_viewmodel_puro.py`, `tests/ui/test_ruta_critica_desktop_smoke.py` | La ruta crítica desktop ya tiene smoke PySide6 con DB temporal que crea una cita por la vía UI soportada y la verifica en el listado. |
| FTR-005 | Se puede ejecutar pipeline ML de riesgo de citas | Alta | Parcial | `tests/test_ml_training.py`, `tests/test_train_calibration_integration.py`, `tests/test_drift_report.py`, `tests/ui/test_ruta_critica_desktop_smoke.py`, `tests/test_prediccion_operativa_facade_integracion.py` | La evidencia desktop sube de nivel: ahora existe una ruta headless que entra por `MainWindow`, navega desde gestión al módulo ML y ejecuta el entrenamiento mediante el `QThread` real de la pantalla, validando feedback visible, previsualización y explicación observable. Sigue pendiente un E2E total con arranque/loop principal real y un recorrido cross-módulo más amplio. |
| FTR-006 | Se puede exportar KPIs y resultados en CSV | Alta | Verificada | `clinicdesk/app/application/usecases/export_kpis_csv.py`, `scripts/ml_cli.py`, `tests/test_export_kpis_csv.py`, `tests/test_export_kpis_csv_e2e.py` | La exportación CSV ya no queda solo en el caso de uso: una prueba E2E/controlada recorre el wiring real vía CLI con SQLite y stores temporales, ejecuta `seed-demo`, `build-features`, `train`, `score`, drift opcional y `export kpis`, y valida por contenido los cuatro artefactos contractuales más el error explícito ante requests inconsistentes. |
| FTR-007 | Se puede exportar auditoría de accesos con controles | Media | Verificada | `clinicdesk/app/application/usecases/exportar_auditoria_csv.py`, `tests/test_exportar_auditoria_csv_usecase.py` | RBAC y sanitización cubiertos. |
| FTR-008 | Se puede rotar claves criptográficas de campos sensibles | Media | Parcial | `scripts/security_cli.py`, `tests/test_security_cli.py` | CLI y guardrails cubiertos; falta escenario operacional completo automatizado. |
