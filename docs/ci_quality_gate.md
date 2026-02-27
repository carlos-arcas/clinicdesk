# CI Quality Gate (Core)

## Objetivo
Asegurar calidad continua sin bloquear por UI. El gate bloqueante aplica al **core clínico bajo control en Paso 2** (flujo de citas end-to-end).

## Comando único (local y CI)
- `python scripts/quality_gate.py`

## Qué ejecuta el gate
1. **Lint/format opcional (solo si ya existe configuración)**
   - Detecta `pyproject.toml` con sección `[tool.ruff]`.
   - Si existe, ejecuta `ruff check .` y `ruff format --check .`.
2. **Tests bloqueantes**
   - Ejecuta `pytest` con `-m "not ui"`.
3. **Coverage SOLO core**
   - Calcula cobertura mediante trazado de ejecución sobre los módulos core definidos en el script.
4. **Umbral**
   - Falla si cobertura core `< 85%`.

## Definición de “core” (Paso 2)
Módulos incluidos en cobertura bloqueante:
- `clinicdesk/app/domain/enums.py`
- `clinicdesk/app/domain/exceptions.py`
- `clinicdesk/app/application/usecases/crear_cita.py`
- `clinicdesk/app/infrastructure/sqlite/repos_citas.py`
- `clinicdesk/app/queries/citas_queries.py`

Módulos excluidos del gate bloqueante en este paso:
- UI/presentation (`clinicdesk/app/ui`, `clinicdesk/app/pages`)
- scripts de soporte y tests
- resto de módulos legacy que se incorporarán gradualmente al gate en pasos siguientes.

## Notas de operación
- Los tests de UI deben declararse con marker `ui` para no bloquear este gate.
- El script devuelve `exit code != 0` si falla lint configurado, tests o cobertura.
