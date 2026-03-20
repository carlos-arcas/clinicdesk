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
QT_QPA_PLATFORM=offscreen pytest -q tests/test_login_dialog_ui.py tests/test_session_controller.py tests/test_auth_service.py
```

Qué cubren:
- `tests/test_login_dialog_ui.py`: contrato observable de `LoginDialog` para first-run, creación inicial válida/ inválida, login correcto con `Accepted` + `LoginOutcome`, bloqueo tras intentos fallidos con reloj inyectado, y demo mode permitido/prohibido;
- `tests/test_session_controller.py`: transición post-login de `ControladorSesionAutenticada`, incluyendo creación de ventana principal, visibilidad real, retención de referencia, secuencia de `setQuitOnLastWindowClosed(...)` y fallos controlados cuando la factory devuelve `None`, la ventana no queda visible o la factory explota;
- `tests/test_auth_service.py`: contrato base de hashing, verificación y bloqueo del servicio de autenticación sobre SQLite efímera.

Alcance honesto:
- **UI/smoke desktop**: `LoginDialog` real, widgets reales y feedback observable vía `QMessageBox` interceptado en tests headless;
- **integración fuerte**: `AuthService` + `LoginDialog` y `ControladorSesionAutenticada` se prueban con dobles mínimos y SQLite temporal, sin lanzar `main()` completo ni un loop infinito;
- **no cubre todavía un E2E completo** con `clinicdesk/app/main.py`, logout real y reapertura de sesión dentro del mismo ciclo extremo a extremo.

## Qué protege el gate
- Lint y formato.
- Typecheck incremental.
- Tests rápidos y cobertura mínima del core.
- Guardrails estructurales, secretos, PII y contratos documentales.
- Verificación de entrypoints y documentación funcional mínima.

## Regla operativa
Antes de abrir PR hay que ejecutar `python -m scripts.gate_pr`. Si falla, se corrige y se repite el ciclo hasta dejarlo en verde.
