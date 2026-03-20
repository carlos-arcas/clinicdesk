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

Qué cubren:
- arranque controlado de `QApplication`, resolución lazy del registro de páginas y navegación mínima hacia `citas` y `prediccion_operativa`;
- flujo smoke de citas: abrir `PageCitas`, comprobar estado vacío estable, crear una cita por la ruta UI soportada y verificarla en listado con SQLite temporal;
- flujo ML desktop reforzado: `MainWindow` real, navegación desde `gestión` hasta `prediccion_operativa`, disparo del entrenamiento por el wiring real `QThread`/relay de la pantalla, feedback visible de inicio/fin, previsualización con datos reales y explicación observable sin sleeps arbitrarios;
- smoke focal de `PagePrediccionOperativa` para mantener cobertura rápida del entrenamiento mínimo y de la explicación utilizable en aislamiento controlado;
- integración fuerte del facade real con dataset efímero y una marca temporal fija por test para entrenamiento, previsualización y explicación sin red, Docker ni servicios externos.

Notas de estabilidad:
- todos estos tests usan SQLite temporal controlada por fixtures de `pytest`;
- la siembra ML usa una marca temporal fija por test (`obtener_fecha_base_prediccion()`) para mantener coherencia entre histórico y agenda futura sin depender del reloj real;
- las esperas UI usan `qtbot.waitUntil(...)` en lugar de `sleep` arbitrario.

Alcance honesto para `FTR-005`:
- **smoke desktop**: cubre el flujo headless realista hasta `MainWindow` + navegación al módulo ML + background Qt de la pantalla + salida observable en tabla y diálogo;
- **integración fuerte**: cubre facade real, dataset y explicaciones sin lanzar la aplicación completa;
- **todavía no es E2E total**: no ejecuta `clinicdesk/app/main.py` hasta cierre completo del loop ni verifica un recorrido operacional de extremo a extremo más amplio entre varios módulos.

### Autenticación desktop PySide6
```bash
QT_QPA_PLATFORM=offscreen pytest -q tests/test_auth_service.py tests/test_login_dialog_ui.py tests/test_session_controller.py tests/test_main_auth_flow.py
```

Qué cubren:
- `tests/test_login_dialog_ui.py`: contrato observable de `LoginDialog` para first-run, creación inicial válida/inválida, login correcto con `Accepted` + `LoginOutcome`, bloqueo tras intentos fallidos con reloj inyectado, y demo mode permitido/prohibido;
- `tests/test_session_controller.py`: transición post-login de `ControladorSesionAutenticada`, incluyendo creación de ventana principal, visibilidad real, retención de referencia, secuencia de `setQuitOnLastWindowClosed(...)` y fallos controlados cuando la factory devuelve `None`, la ventana no queda visible o la factory explota;
- `tests/test_main_auth_flow.py`: tramo extremo a extremo controlado del wiring real extraído desde `clinicdesk/app/main.py`, cubriendo apertura de sesión, visibilidad de ventana principal, logout, reapertura satisfactoria, cancelación de relogin con cierre limpio de top-level widgets y error post-login con feedback sin cierre silencioso;
- `tests/test_auth_service.py`: contrato base de hashing, verificación y bloqueo del servicio de autenticación sobre SQLite efímera.

Alcance honesto:
- **E2E/controlado**: el nuevo test usa `QApplication` real, `ControladorSesionAutenticada` real, callbacks reales de logout y SQLite temporal para recorrer el mismo wiring que usa `main.py` sin sleeps arbitrarios;
- **integración aún fuera**: no ejecuta el `entrypoint` completo hasta `app.exec()` ni valida la salida final del proceso Qt, así que `FTR-003.e2e` permanece en **Parcial**;
- **sin humo**: el coverage nuevo cierra el hueco real de logout/reapertura dentro del ciclo autenticado, pero no se vende como E2E total del proceso completo.

## Qué protege el gate
- Lint y formato.
- Typecheck incremental.
- Tests rápidos y cobertura mínima del core.
- Guardrails estructurales, secretos, PII y contratos documentales.
- Verificación de entrypoints y documentación funcional mínima.

## Regla operativa
Antes de abrir PR hay que ejecutar `python -m scripts.gate_pr`. Si falla, se corrige y se repite el ciclo hasta dejarlo en verde.
