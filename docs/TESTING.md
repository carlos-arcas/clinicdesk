# Pruebas

## Flujo operativo recomendado
1. Crea o repara el entorno del repo con `python scripts/setup.py`.
2. Usa siempre los comandos canónicos (`python -m scripts.doctor_entorno_calidad`, `python -m scripts.gate_rapido`, `python -m scripts.gate_pr`). Si `.venv` existe y es utilizable, el repo se reejecuta automáticamente con ese intérprete.
3. Ejecuta el doctor canónico: `python -m scripts.doctor_entorno_calidad`.
4. Si necesitas validar recuperabilidad sin red, usa: `python -m scripts.doctor_entorno_calidad --require-wheelhouse`.
5. Corrige el entorno según el comando exacto que indique el doctor o el bloqueo canónico.
6. Solo cuando el doctor quede alineado, ejecuta `python -m scripts.gate_pr`.

## Setup estándar
```bash
python scripts/setup.py
```

El setup ahora deja explícito, antes de instalar nada:
- qué Python lanzó el script;
- cuál es el `.venv` esperado del repo;
- si el Python activo es compatible con la versión mínima del repo (`pyproject.toml`);
- si `CLINICDESK_WHEELHOUSE` apunta a una ruta inválida, vacía o incompleta respecto al lock;
- si el bloqueo depende de proxy/red real y no es recuperable localmente.

Cuando `.venv` ya existe y es utilizable, `setup.py` se reejecuta automáticamente dentro de ese Python antes de instalar/verificar tooling. Si `.venv` no existe o está roto, el setup lo dice explícitamente y usa el Python lanzador solo para crear o reparar el entorno.

## Doctor de entorno
```bash
python -m scripts.doctor_entorno_calidad
```

El doctor no instala nada. Si `.venv` del repo existe y es ejecutable, se reejecuta automáticamente con ese intérprete y lo deja explícito en la salida. Si `.venv` falta o no es ejecutable, falla antes del diagnóstico funcional con una guía única y consistente. Informa de forma reproducible:
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

Úsalo cuando quieras saber si el entorno es recuperable **sin red**. Si falta wheelhouse, si `CLINICDESK_WHEELHOUSE` apunta a algo inválido, si el directorio está vacío o si los wheels no cubren todas las dependencias fijadas por `requirements-dev.txt` (incluyendo `requirements.txt` vía `-r`), el doctor falla de forma explícita y no intenta instalar nada.

## Fuente única de verdad del tooling
- Lock efectivo: `requirements-dev.txt`.
- Entrada editable: `requirements-dev.in`.
- Regeneración del lock: `python -m scripts.lock_deps`.
- Python mínimo del repo: `pyproject.toml` (`tool.mypy.python_version`).

No deben existir listas paralelas de versiones del toolchain. El doctor, Ruff y el gate leen la expectativa desde el lock y el diagnóstico del intérprete desde `pyproject.toml`.

## Correcciones típicas
### Estás fuera del venv correcto o usando otro intérprete
Los comandos canónicos intentan reejecutarse dentro de `.venv` automáticamente. Si eso no ocurre, el error significa que `.venv` falta o no es ejecutable.

```bash
python scripts/setup.py
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


## Criterio operativo del wheelhouse
Un wheelhouse se considera:
- **válido/utilizable**: existe como directorio, contiene archivos `.whl` y cubre todas las dependencias fijadas por `requirements-dev.txt` más los includes (`-r requirements.txt`).
- **incompleto**: hay wheels, pero falta al menos un paquete/version pinneado del lock; el doctor/setup listan ejemplos concretos faltantes.
- **vacío**: el directorio existe pero no aporta ningún `.whl`.
- **inválido**: la ruta existe pero no es directorio, o apunta a una ubicación no utilizable.

### Cómo comprobarlo
```bash
python -m scripts.doctor_entorno_calidad --require-wheelhouse
```

### Cómo construirlo
```bash
python -m scripts.dev.build_wheelhouse
```

Ese comando descarga el lock dev, deja los wheels en `wheelhouse/` (o en `CLINICDESK_WHEELHOUSE` si está definido) y falla si, al terminar, la cobertura del lock sigue siendo incompleta.

### Qué sigue dependiendo de infraestructura externa
- Construir el wheelhouse inicial requiere que `pip download` alcance el índice o proxy configurado.
- Si el lock incluye artefactos no disponibles para tu plataforma/intérprete, el repo lo reportará, pero no puede fabricarlos por sí solo.
- Sin red/proxy funcional **y** sin wheelhouse utilizable, `setup.py` seguirá fallando honestamente.

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
3. `python -m scripts.doctor_entorno_calidad`
4. `python -m scripts.gate_pr`

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
