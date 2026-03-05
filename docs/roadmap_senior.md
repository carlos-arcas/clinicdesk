# Roadmap Senior

## UI/deuda/arquitectura

- `clinicdesk/app/domain/farmacia.py`: **antes 213 LOC**, **después 21 LOC** como fachada de compatibilidad.
- `clinicdesk/app/domain/entities.py`: se mantiene como fachada de API pública (30 LOC), ahora reexportando entidades desde `domain/entidades`.

## Módulos nuevos y motivo

- `clinicdesk/app/domain/entidades/entidades_farmacia_stock.py`: separa entidades de stock (medicamentos/materiales/movimientos) para cohesión y menor acoplamiento.
- `clinicdesk/app/domain/entidades/entidades_recetas.py`: separa entidades de recetas y dispensaciones para bounded context claro y mejor testabilidad.
- `clinicdesk/app/domain/entidades/__init__.py`: punto único de re-export explícito con `__all__` estable.

## Refactor atómico `PagePacientes` (baseline/evidencia)

- Baseline medido: `wc -l clinicdesk/app/pages/pacientes/page.py` => **489 LOC**.
- Resultado tras split UI/render/acciones/workers/preferencias: `clinicdesk/app/pages/pacientes/page.py` => **326 LOC**.
- Módulos nuevos:
  - `clinicdesk/app/pages/pacientes/contratos_ui.py` (**21 LOC**)
  - `clinicdesk/app/pages/pacientes/ui_builder.py` (**74 LOC**)
  - `clinicdesk/app/pages/pacientes/render_pacientes.py` (**89 LOC**)
  - `clinicdesk/app/pages/pacientes/acciones_pacientes.py` (**169 LOC**)
  - `clinicdesk/app/pages/pacientes/preferencias_pacientes.py` (**33 LOC**)
  - `clinicdesk/app/pages/pacientes/window_feedback.py` (**21 LOC**)
  - `clinicdesk/app/pages/pacientes/workers_pacientes.py` (**54 LOC**)

## Refactor atómico `PageConfirmaciones` (baseline/evidencia)

- Baseline medido: `wc -l clinicdesk/app/pages/confirmaciones/page.py` => **460 LOC**.
- Resultado tras extraer filtros/selección/navegación/acciones rápidas/telemetría: `clinicdesk/app/pages/confirmaciones/page.py` => **328 LOC**.
- Helpers compartidos de feedback de ventana:
  - `clinicdesk/app/ui/ux/window_feedback.py` (nuevo módulo común)
  - `clinicdesk/app/pages/pacientes/window_feedback.py` queda como re-export para compatibilidad.

## CI fixes (pytest/UI)

- El core gate se rompía porque `pytest-qt` se cargaba por **autoload de entrypoints** (no por `pytest.ini`), incluso usando `-m "not ui"`, y en CI sin stack gráfico terminaba en error de `libEGL`.
- Decisión técnica aplicada: ejecutar core con autoload apagado (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `PYTEST_ADDOPTS=""`) y cobertura explícita vía `python -m coverage run -m pytest`, más generación de `docs/coverage.xml` y `docs/coverage.json`.
- Ejecución actual separada: core corre `pytest -m "not ui"` aislado de plugins externos; UI corre headless (`QT_QPA_PLATFORM=offscreen` + `xvfb-run`) en jobs `ui_smoke`/`uiqt` con `libegl1` y librerías XCB mínimas.

## Coverage fail-fast en quality gate

- Qué fallaba: en entornos sin `coverage`, `python -m scripts.gate_pr` terminaba con `ModuleNotFoundError` y salida poco accionable.
- Decisión técnica: validación fail-fast de dependencia (`importlib.util.find_spec("coverage")`) y pin explícito de `coverage` en dependencias dev.
- Ejecución actual: el core sigue exigiendo cobertura (no se omite el check) y, si falta `coverage`, el gate falla controlado con `rc=2`, mensaje de instalación y sin stacktrace ruidoso.

## Secrets scan fallback (gate PR estable)

- Problema detectado: en entornos restringidos `gitleaks` puede no estar en `PATH` y el `gate_pr` fallaba por dependencia externa no disponible.
- Solución aplicada: `secrets_scan_check` mantiene `gitleaks` cuando existe y activa un fallback Python conservador cuando no existe, manteniendo el check bloqueante.
- Garantía de seguridad: reportes/logs solo incluyen metadatos y snippets redactados (`[REDACTED]` + hash corto), sin exponer secretos en claro.
