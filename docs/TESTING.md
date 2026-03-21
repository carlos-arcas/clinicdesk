# Pruebas

## Flujo operativo recomendado
1. Crea o repara el entorno del repo con `python scripts/setup.py`.
2. Activa el venv del repo (`source .venv/bin/activate` en Unix o `.venv\Scripts\activate` en Windows).
3. Ejecuta el doctor canónico: `python -m scripts.doctor_entorno_calidad`.
4. Si necesitas validar recuperabilidad sin red, usa: `python -m scripts.doctor_entorno_calidad --require-wheelhouse`.
5. Corrige el entorno según el comando exacto que indique el doctor.
6. Solo cuando el doctor quede alineado, ejecuta `python -m scripts.gate_pr`.

## Setup estándar
```bash
python scripts/setup.py
```

El setup ahora deja explícito, antes de instalar nada:
- qué Python lanzó el script;
- cuál es el `.venv` esperado del repo;
- si el Python activo es compatible con la versión mínima del repo (`pyproject.toml`);
- si `CLINICDESK_WHEELHOUSE` apunta a una ruta inválida, vacía o incompleta;
- si el bloqueo depende de proxy/red real y no es recuperable localmente.

Cuando termina bien, también imprime el comando exacto para activar el venv correcto.

## Doctor de entorno
```bash
python -m scripts.doctor_entorno_calidad
```

El doctor no instala nada. Informa de forma reproducible:
- herramienta bloqueante;
- versión esperada (desde `requirements-dev.txt`);
- versión instalada en el intérprete activo;
- path exacto del intérprete activo;
- Python mínimo esperado por el repo y Python esperado en `.venv`;
- si estás fuera del venv del repo o dentro de otro venv;
- comando exacto para activar el venv correcto;
- comando exacto para recrear `.venv` cuando quedó corrupto o usa otro Python;
- estado de `wheelhouse`, `PIP_INDEX_URL`, `UV_INDEX_URL` y proxies;
- si el problema parece estar en lock, intérprete o dependencias ausentes.

## Doctor offline-first
```bash
python -m scripts.doctor_entorno_calidad --require-wheelhouse
```

Úsalo cuando quieras saber si el entorno es recuperable **sin red**. Si falta wheelhouse, si `CLINICDESK_WHEELHOUSE` apunta a algo inválido o si el directorio no contiene wheels utilizables, el doctor falla de forma explícita y no intenta instalar nada.

## Fuente única de verdad del tooling
- Lock efectivo: `requirements-dev.txt`.
- Entrada editable: `requirements-dev.in`.
- Regeneración del lock: `python -m scripts.lock_deps`.
- Python mínimo del repo: `pyproject.toml` (`tool.mypy.python_version`).

No deben existir listas paralelas de versiones del toolchain. El doctor, Ruff y el gate leen la expectativa desde el lock y el diagnóstico del intérprete desde `pyproject.toml`.

## Correcciones típicas
### Estás fuera del venv correcto o usando otro intérprete
```bash
source .venv/bin/activate
python -m scripts.doctor_entorno_calidad
```

Si `.venv` quedó roto o fue creado con otro Python:
```bash
rm -rf .venv
python scripts/setup.py
```

### Falta tooling o la versión está desalineada
```bash
python -m pip install -r requirements-dev.txt
python -m scripts.doctor_entorno_calidad
```

### El lock no coincide con `requirements-dev.in`
```bash
python -m scripts.lock_deps
python -m scripts.doctor_entorno_calidad
```

### Red/proxy restringidos
- Si `setup.py` informa un error de proxy/red, el repo no “simula” un PASS.
- Revisa `HTTP_PROXY`, `HTTPS_PROXY`, `PIP_INDEX_URL` y `UV_INDEX_URL`.
- Si necesitas modo offline-first, prepara un wheelhouse fuera del repo y reutilízalo con `CLINICDESK_WHEELHOUSE`.

```bash
python -m scripts.dev.build_wheelhouse
CLINICDESK_WHEELHOUSE=/ruta/a/wheelhouse python scripts/setup.py
```

Si tampoco puedes construir ese wheelhouse por restricciones reales de red o proxy corporativo, el entorno local sigue bloqueado y esa recuperación **no depende del repo**: necesitas resolver la infraestructura externa.

## Significado exacto de `rc=20` en `gate_pr`
`python -m scripts.gate_pr` devuelve `rc=20` cuando el preflight del entorno detecta un **bloqueo operativo local**. Eso significa que el gate funcional **todavía no ejecutó** las validaciones del proyecto.

Interpretación:
- `rc=20`: fallo de entorno local. Revisa el doctor y el intérprete activo.
- otro código no-cero tras pasar preflight: fallo real del proyecto o del gate funcional.

## Cómo distinguir fallo de proyecto vs fallo de entorno
- **Fallo de entorno**: el doctor marca tooling ausente/desalineado, intérprete incorrecto, wheelhouse inválido o lock roto. `gate_pr` sale con `rc=20`.
- **Fallo de proyecto**: el doctor queda alineado y luego `gate_pr` falla en lint, typecheck, tests, cobertura, seguridad o docs.

## Recuperación local más rápida
1. `rm -rf .venv`
2. `python scripts/setup.py`
3. `source .venv/bin/activate`
4. `python -m scripts.doctor_entorno_calidad`
5. `python -m scripts.gate_pr`

## Validación focalizada del export KPI
```bash
pytest -q tests/test_export_kpis_csv.py tests/test_export_kpis_csv_e2e.py tests/test_export_kpis_csv_security.py
```

Úsalo cuando quieras revalidar solo el flujo contractual y de seguridad del export KPI: columnas permitidas por archivo, ausencia de PII/datos operativos en los CSV agregados y errores controlados de salida en la CLI real y en el caso de uso.

## Qué valida el gate
- preflight de entorno;
- lint y formato;
- typecheck;
- tests rápidos y cobertura;
- guardrails estructurales, seguridad y documentación.
