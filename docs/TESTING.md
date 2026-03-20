# Pruebas

## Preparar entorno
```bash
python scripts/setup.py
```

Si necesitas hacerlo a mano:

```bash
python -m venv .venv
. .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Comandos canónicos
- Suite rápida: `pytest -q`
- Gate rápido: `python -m scripts.gate_rapido`
- Gate completo: `python -m scripts.gate_pr`

## Subconjuntos útiles
### Core sin UI
```bash
pytest -q -m "not ui"
```

### Guardrails estructurales
```bash
pytest -q tests/guardrails
```

### UI headless
```bash
QT_QPA_PLATFORM=offscreen pytest -q -m "uiqt"
```

### Ruta crítica desktop
```bash
QT_QPA_PLATFORM=offscreen pytest -q tests/ui/test_ruta_critica_desktop_smoke.py
pytest -q tests/test_prediccion_operativa_facade_integracion.py
QT_QPA_PLATFORM=offscreen pytest -q tests/test_main_entrypoint_e2e.py
QT_QPA_PLATFORM=offscreen pytest -q tests/test_ml_cross_module_e2e.py
pytest -q tests/test_prediccion_operativa_security_policy.py tests/test_prediccion_operativa_security_static.py
QT_QPA_PLATFORM=offscreen pytest -q tests/test_prediccion_operativa_security.py
```

### Exportación KPI CSV E2E/controlada
```bash
pytest -q tests/test_export_kpis_csv.py tests/test_export_kpis_csv_e2e.py
```

Qué cubre:
- flujo contractual real vía `scripts/ml_cli.py` sin subprocess ni red, apoyado en el wiring soportado por producto;
- `seed-demo` sobre SQLite temporal + `build-features` hacia stores temporales para obtener datasets reproducibles;
- `train`, `score` y `export kpis` reales, más drift opcional con dos versiones de dataset;
- validación de contenido mínimo de `kpi_overview.csv`, `kpi_scores_by_bucket.csv`, `kpi_drift_by_feature.csv` y `kpi_training_metrics.csv`;
- escenario `trained` con drift, escenario `baseline` sin drift y error explícito cuando el request resulta inconsistente con el contrato real.

Notas de estabilidad:
- usa `tmp_path`, SQLite efímera y stores JSON temporales;
- fija rangos de fechas explícitos para no depender del reloj operativo;
- no usa `sleep` ni servicios externos.

### Exportación de auditoría E2E/controlada
```bash
QT_QPA_PLATFORM=offscreen pytest -q tests/test_exportar_auditoria_csv_usecase.py tests/test_auditoria_export_e2e.py
```

Qué cubre:
- `PageAuditoria` real cargada dentro de `MainWindow`, con filtros válidos y disparo por la ruta `_on_exportar()` → `run_premium_job(...)`;
- worker real `crear_worker_exportacion(...)` con escritura física del CSV en `tmp_path`, sin mocks masivos de negocio;
- validación de cabeceras exactas `COLUMNAS_EXPORTACION_AUDITORIA`, contenido mínimo contractual y redacción efectiva de PII en usuario/identificadores;
- feedback observable de éxito (`job.done`) y feedback controlado de error (`job.failed`) cuando la integridad de auditoría queda comprometida antes de exportar.

Notas de estabilidad:
- usa `QT_QPA_PLATFORM=offscreen`, SQLite temporal y diálogos de confirmación/guardado controlados por monkeypatch;
- no usa `sleep`, no escribe sobre bases persistentes del repo y mantiene el worker/job real de producto.

### Rotación de claves CLI E2E/controlada
```bash
pytest -q tests/test_security_cli.py tests/test_security_cli_e2e.py
```

Qué cubre:
- `generate-key` real, verificando salida no vacía, formato razonable y advertencia segura por `stderr`;
- `check-key` real con clave válida, inválida y ausente, comprobando `rc` y mensajes explícitos;
- `rotate-key --dry-run` sobre SQLite temporal real, con contadores coherentes y sin fugas de PII ni material de clave;
- `rotate-key --apply` con recifrado efectivo, lectura funcional posterior mediante `PacientesRepository` y auditoría `CRYPTO_ROTATE` saneada;
- errores contractuales por modo ausente, entorno inválido (`CLINICDESK_CRYPTO_KEY` / `CLINICDESK_CRYPTO_KEY_PREVIOUS`), columnas de cifrado ausentes y schema/DB inválidos con mensajes explícitos.

Notas de estabilidad:
- usa `security_cli.main([...])` directamente, sin subprocess, red, Docker ni servicios externos;
- opera con `tmp_path` y SQLite efímera, sin bases persistentes del repo;
- no usa `sleep`, mocks de negocio ni helpers privados como sujeto principal del test.

Qué cubren:
- arranque controlado de `QApplication`, resolución lazy del registro de páginas y navegación mínima hacia `citas` y `prediccion_operativa`;
- flujo smoke de citas: abrir `PageCitas`, comprobar estado vacío estable, crear una cita por la ruta UI soportada y verificarla en listado con SQLite temporal;
- flujo ML desktop reforzado: `MainWindow` real, navegación desde `gestión` hasta `prediccion_operativa`, disparo del entrenamiento por el wiring real `QThread`/relay de la pantalla, feedback visible de inicio/fin, previsualización con datos reales y explicación observable sin sleeps arbitrarios;
- harness E2E/controlado del entrypoint desktop: `main()` real con `LoginDialog` inyectado para prueba, entrada en `app.exec()`, ventana principal visible, navegación UI real a `prediccion_operativa`, entrenamiento mínimo observable, explicación visible y salida controlada del loop Qt con cierre limpio de top-level widgets;
- prueba cross-módulo desktop: `MainWindow` real, navegación ida/vuelta entre `gestión` y `prediccion_operativa`, entrenamiento operativo mínimo, verificación de salud/estimaciones consumidas por Gestión y limpieza de background al abandonar el módulo;
- hardening de seguridad en `prediccion_operativa`: política centralizada de autorización para `Action.ML_ENTRENAR`, bloqueo observable de entrenamiento/reintento para `READONLY`, decisión explícita de mantener lectura/explanación y verificación de que la telemetría del denial path no añade PII funcional nueva;
- smoke focal de `PagePrediccionOperativa` para mantener cobertura rápida del entrenamiento mínimo y de la explicación utilizable en aislamiento controlado;
- integración fuerte del facade real con dataset efímero y una marca temporal fija por test para entrenamiento, previsualización y explicación sin red, Docker ni servicios externos.

Notas de estabilidad:
- todos estos tests usan SQLite temporal controlada por fixtures de `pytest`;
- la siembra ML usa una marca temporal fija por test (`obtener_fecha_base_prediccion()`) para mantener coherencia entre histórico y agenda futura sin depender del reloj real;
- las esperas UI usan `qtbot.waitUntil(...)` en lugar de `sleep` arbitrario.

Alcance honesto para `FTR-005`:
- **entrypoint E2E/controlado**: cubre `main()` + `app.exec()` real + login aceptado + ventana principal visible + navegación UI a ML + entrenamiento observable + cierre limpio del loop;
- **smoke desktop**: sigue cubriendo el flujo headless realista hasta `MainWindow` + navegación al módulo ML + background Qt de la pantalla + salida observable en tabla y diálogo;
- **integración fuerte**: cubre facade real, dataset y explicaciones sin lanzar la aplicación completa;
- **Seguridad residual ya cerrada en la superficie soportada**: entrenamiento y reintento de `prediccion_operativa` quedan protegidos por RBAC explícito; la lectura/explicación se mantiene para perfiles de consulta sin abrir rutas de escritura nuevas.

### Autenticación desktop PySide6
```bash
QT_QPA_PLATFORM=offscreen pytest -q tests/test_auth_service.py tests/test_login_dialog_ui.py tests/test_session_controller.py tests/test_main_auth_flow.py tests/test_main_entrypoint_e2e.py
```

Qué cubren:
- `tests/test_login_dialog_ui.py`: contrato observable de `LoginDialog` para first-run, creación inicial válida/inválida, login correcto con `Accepted` + `LoginOutcome`, bloqueo tras intentos fallidos con reloj inyectado, y demo mode permitido/prohibido;
- `tests/test_session_controller.py`: transición post-login de `ControladorSesionAutenticada`, incluyendo creación de ventana principal, visibilidad real, retención de referencia, secuencia de `setQuitOnLastWindowClosed(...)` y fallos controlados cuando la factory devuelve `None`, la ventana no queda visible o la factory explota;
- `tests/test_main_auth_flow.py`: tramo extremo a extremo controlado del wiring real extraído desde `clinicdesk/app/main.py`, cubriendo apertura de sesión, visibilidad de ventana principal, logout, reapertura satisfactoria, cancelación de relogin con cierre limpio de top-level widgets y error post-login con feedback sin cierre silencioso;
- `tests/test_main_entrypoint_e2e.py`: harness E2E/controlado del entrypoint desktop completo, ejecutando `main()` real hasta `app.exec()`/salida limpia del loop, con login aceptado, `MainWindow` visible, navegación real a `prediccion_operativa`, entrenamiento mínimo con feedback observable y cierre sin hilos de entrenamiento activos;
- `tests/test_auth_service.py`: contrato base de hashing, verificación y bloqueo del servicio de autenticación sobre SQLite efímera.

Alcance honesto:
- **E2E/controlado**: los tests usan `QApplication` real, `ControladorSesionAutenticada` real, callbacks reales de logout y SQLite temporal para recorrer el mismo wiring que usa `main.py` sin sleeps arbitrarios;
- **entrypoint ya cubierto**: `tests/test_main_entrypoint_e2e.py` ejecuta el flujo principal hasta `app.exec()` y valida la salida limpia del loop Qt, cerrando el residual previo de `FTR-003.e2e`;
- **sin humo**: el harness nuevo no se vende como E2E total de toda la app; automatiza el entrypoint real y un tramo productivo concreto hacia ML, pero no sustituye futuros recorridos operacionales más amplios.

## Qué protege el gate
- Lint y formato.
- Typecheck incremental.
- Tests rápidos y cobertura mínima del core.
- Guardrails estructurales, secretos, PII y contratos documentales.
- Verificación de entrypoints y documentación funcional mínima.

## Regla operativa
Antes de abrir PR hay que ejecutar `python -m scripts.gate_pr`. Si falla, se corrige y se repite el ciclo hasta dejarlo en verde.
