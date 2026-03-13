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
