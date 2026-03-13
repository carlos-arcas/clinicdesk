# Testing ClinicDesk (Windows)

## Preparar entorno

1. Crear entorno virtual:
   ```bat
   python -m venv .venv
   ```
2. Activar entorno:
   ```bat
   .venv\Scripts\activate
   ```
3. Instalar dependencias base:
   ```bat
   pip install -r requirements.txt
   ```
4. Instalar dependencias de desarrollo:
   ```bat
   pip install -r requirements-dev.txt
   ```

> `cryptography` es dependencia obligatoria para cifrado/migraciones de pacientes; no se considera opcional.

## Ejecutar tests

### Opción A — launcher (1 comando)
```bat
run_tests.bat
```

### Opción B — manual
```bat
python -m clinicdesk.tools.test_launcher
```

### Opción C — pytest directo
```bat
python -m pytest -q
```

## Notas
- Los tests usan una base de datos temporal en `tests/tmp/clinicdesk_test.sqlite`.
- No se toca `clinicdesk.sqlite` ni ninguna base de datos real.


## Gate de calidad (core)
Para PRs y CI, seguir [docs/ci_quality_gate.md](ci_quality_gate.md).

Comando recomendado de cobertura core:
```bat
python -m pytest --cov=clinicdesk/app/domain --cov=clinicdesk/app/application --cov=clinicdesk/app/infrastructure --cov-report=term-missing --cov-fail-under=85
```

## Subconjunto crítico recomendado (citas core)
Para validar rápido reglas clínicas y persistencia de citas antes del gate completo:

```bat
python -m pytest -q tests/test_citas.py tests/test_citas_crear_usecase_core.py tests/test_citas_repositorio_integracion.py tests/test_citas_listado_queries.py
```

Cobertura de este subconjunto:
- Reglas duras de `CrearCitaUseCase` (IDs/fechas/solapes/no existencia/inactividad).
- Reglas de warning y override (cuadrante y ausencias).
- Contratos de persistencia en SQLite temporal (`CitasRepository`).
- Consultas de listado con filtros clínicos y de calidad de datos (`CitasQueries`).


## Estrategia desktop/UI headless (realista)
- Tests **puros** (sin Qt): helpers, validadores, estado de formularios, estado de listados y restauración de contexto de tabla.
- Tests **UI headless críticos**: marcados con `ui` + `uiqt`, ejecutados con `QT_QPA_PLATFORM=offscreen` cuando la librería gráfica existe.
- Tests que dependen de runtime gráfico completo deben quedar fuera del subset crítico y documentarse explícitamente.

### Subset crítico portable (sin runtime gráfico)
Este subset no importa widgets Qt en tiempo de colección y puede correr en entornos restringidos (por ejemplo, contenedores sin `libGL`):

```bash
python -m pytest -q \
  tests/ui/test_formularios_validacion_pura.py \
  tests/ui/test_forms_estado.py \
  tests/ui/test_contexto_tabla_puro.py \
  tests/ui/test_estados_listado_puro.py
```

Contrato que blinda este subset:
- Validación/formato de formularios y prioridad del primer error.
- Dirty state, CTA habilitado/deshabilitado y anti doble submit via `ControladorEstadoFormulario`.
- Preservación/restauración de contexto de tabla sin depender de `QTableWidget` real.
- Resolución de estado de listado (loading/error/empty/content) y distinción de vacío real vs vacío por filtro.

### Subset UI mínimo (si PySide6 + libGL están disponibles)
```bash
QT_QPA_PLATFORM=offscreen python -m pytest -q -m "uiqt" \
  tests/ui/test_paciente_form_dialog.py \
  tests/ui/test_cita_form_dialog.py \
  tests/ui/test_estados_listado.py \
  tests/ui/test_contexto_tabla.py
```

Si falta runtime gráfico, estos tests deben quedar en skip explícito y el valor principal sigue cubierto por el subset portable.

### Cómo decidir test puro vs test Qt
- **Puro**: reglas de estado, validaciones, resolución de contratos UX, restauración de contexto y decisiones de CTA.
- **Qt**: smoke de wiring real (señales, foco, widgets, `QMessageBox`, apertura/cierre de diálogo).
- Regla práctica: si la aserción puede expresarse con DTOs/estructuras simples, debe ir a test puro.

### Fixtures reutilizables UI
- `tests/ui/conftest.py` expone builders/fixtures reutilizables para:
  - creación de `PacienteFormDialog` y `CitaFormDialog`,
  - completar campos mínimos válidos de cada formulario.
- Recomendación: reutilizar estas fixtures en nuevos smoke tests antes de crear helpers ad-hoc.
