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
