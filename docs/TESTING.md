# Pruebas

## Preparar entorno
```bash
python scripts/setup.py
```

## Diagnóstico rápido del entorno de calidad
Antes de intentar reinstalar nada, usa el doctor canónico:

```bash
python -m scripts.doctor_entorno_calidad
```

Este comando **no instala dependencias**. Solo informa de forma determinista:
- qué herramientas bloqueantes espera el gate (`ruff`, `pytest`, `mypy`, `pip-audit`);
- qué versión exacta espera, leída desde `requirements-dev.txt`;
- cuál falta, cuál está desalineada y qué comando exacto corrige cada caso;
- si el problema es de red/proxy/offline-first (`wheelhouse`, `PIP_INDEX_URL`, `HTTP[S]_PROXY`).

## Si necesitas hacerlo a mano
```bash
python -m venv .venv
. .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Comandos canónicos
- Doctor de entorno: `python -m scripts.doctor_entorno_calidad`
- Suite rápida: `pytest -q`
- Gate rápido: `python -m scripts.gate_rapido`
- Gate completo: `python -m scripts.gate_pr`

## Toolchain esperado y fuente de verdad
- La **fuente única de verdad de versiones** del tooling de calidad es `requirements-dev.txt`.
- `requirements-dev.in` es la entrada editable y `python -m scripts.lock_deps` regenera el lock.
- Si el doctor indica que falta una herramienta o que la versión instalada no coincide, el comando de corrección esperado es:

```bash
python -m pip install -r requirements-dev.txt
```

- Si el lock no contiene todas las herramientas del gate o está corrupto, regénéralo con:

```bash
python -m scripts.lock_deps
```

## Proxy, red restringida y modo offline-first
- Si `setup.py` detecta errores como `ProxyError`, timeouts o fallo de resolución DNS, lo reportará explícitamente como bloqueo de entorno.
- Si no hay `wheelhouse`, el setup depende de red/proxy reales. En ese caso el repo **no simula** un PASS: solo informa del bloqueo.
- Si necesitas preparar un entorno local sin acceso externo, puedes construir un wheelhouse fuera del repo y reutilizarlo con `CLINICDESK_WHEELHOUSE`:

```bash
python -m scripts.dev.build_wheelhouse
CLINICDESK_WHEELHOUSE=/ruta/a/wheelhouse python scripts/setup.py
```

Si tampoco puedes generar ese wheelhouse por restricciones de red reales, el entorno local no es recuperable automáticamente y el doctor lo dejará indicado.

## Qué protege el gate
- Lint y formato.
- Typecheck incremental.
- Tests rápidos y cobertura mínima del core.
- Guardrails estructurales, secretos, PII y contratos documentales.
- Verificación de entrypoints y documentación funcional mínima.

## Regla operativa
Antes de abrir PR hay que ejecutar `python -m scripts.gate_pr`. Si falla por entorno, primero corrige lo que indique `python -m scripts.doctor_entorno_calidad`; si falla por proyecto, corrige el código y repite el ciclo completo.
