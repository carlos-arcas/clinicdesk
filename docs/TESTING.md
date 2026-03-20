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
- flujo ML honesto: smoke desktop de `PagePrediccionOperativa` disparando entrenamiento mínimo sin infraestructura externa, verificando previsualización y explicación observable;
- integración fuerte del facade real con dataset efímero y una marca temporal anclada por test para entrenamiento, previsualización y explicación sin red, Docker ni servicios externos.

Notas de estabilidad:
- todos estos tests usan SQLite temporal controlada por fixtures de `pytest`;
- la siembra ML usa una marca temporal anclada en fixture (`obtener_fecha_base_prediccion()`) para mantener coherencia entre histórico y agenda futura sin depender del reloj real;
- las esperas UI usan `qtbot.waitUntil(...)` en lugar de `sleep` arbitrario.

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
