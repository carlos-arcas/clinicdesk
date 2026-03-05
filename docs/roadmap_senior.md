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

- El core gate fallaba porque `pytest-qt` entraba por autoload de plugins (entrypoints), aunque el selector fuera `-m "not ui"`, y terminaba importando Qt en runners sin `libEGL`.
- Decisión técnica: ejecutar el runner de core con `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` y `PYTEST_ADDOPTS=""` dentro del gate para aislar tests no-UI de plugins externos.
- Ejecución actual: core usa `pytest -m "not ui"` sin autoload; UI usa `QT_QPA_PLATFORM=offscreen` + `xvfb-run` en jobs `ui_smoke`/`uiqt` con dependencias gráficas instaladas.
