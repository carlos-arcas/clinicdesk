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
