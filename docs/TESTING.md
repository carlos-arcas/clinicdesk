# Pruebas

## Flujo operativo recomendado
1. Ejecuta el doctor canónico: `python -m scripts.doctor_entorno_calidad`.
2. Si necesitas validar recuperabilidad sin red, usa: `python -m scripts.doctor_entorno_calidad --require-wheelhouse`.
3. Corrige el entorno según el comando exacto que indique el doctor.
4. Solo cuando el doctor quede alineado, ejecuta `python -m scripts.gate_pr`.

## Setup estándar
```bash
python scripts/setup.py
```

El setup ahora diferencia explícitamente entre:
- herramienta faltante o no instalada en el intérprete activo;
- versión incompatible con el lock;
- fallo de red/proxy;
- wheelhouse ausente o incompatible;
- lock incoherente o desactualizado.

## Doctor de entorno
```bash
python -m scripts.doctor_entorno_calidad
```

El doctor no instala nada. Informa de forma reproducible:
- herramienta bloqueante;
- versión esperada (desde `requirements-dev.txt`);
- versión instalada en el intérprete activo;
- path exacto del intérprete activo;
- comando exacto para corregir;
- estado de `wheelhouse`, `PIP_INDEX_URL` y proxies;
- si el problema parece estar en lock, intérprete o dependencias ausentes.

## Doctor offline-first
```bash
python -m scripts.doctor_entorno_calidad --require-wheelhouse
```

Úsalo cuando quieras saber si el entorno es recuperable **sin red**. Si falta wheelhouse, el doctor falla de forma explícita y no intenta instalar nada.

## Fuente única de verdad del tooling
- Lock efectivo: `requirements-dev.txt`.
- Entrada editable: `requirements-dev.in`.
- Regeneración del lock: `python -m scripts.lock_deps`.

No deben existir listas paralelas de versiones del toolchain. El doctor, Ruff y el gate leen la expectativa desde el lock.

## Correcciones típicas
### Falta tooling o la versión está desalineada
```bash
python -m pip install -r requirements-dev.txt
```

### El lock no coincide con `requirements-dev.in`
```bash
python -m scripts.lock_deps
```

### Red/proxy restringidos
- Si `setup.py` informa un error de proxy/red, el repo no “simula” un PASS.
- Revisa `HTTP_PROXY`, `HTTPS_PROXY` y `PIP_INDEX_URL`.
- Si necesitas modo offline-first, prepara un wheelhouse fuera del repo y reutilízalo con `CLINICDESK_WHEELHOUSE`.

```bash
python -m scripts.dev.build_wheelhouse
CLINICDESK_WHEELHOUSE=/ruta/a/wheelhouse python scripts/setup.py
```

Si tampoco puedes construir ese wheelhouse por restricciones reales de red, el entorno local sigue bloqueado y debes resolver esa dependencia externa fuera del repo.

## Significado exacto de `rc=20` en `gate_pr`
`python -m scripts.gate_pr` devuelve `rc=20` cuando el preflight del entorno detecta un **bloqueo operativo local**. Eso significa que el gate funcional **todavía no ejecutó** las validaciones del proyecto.

Interpretación:
- `rc=20`: falla de entorno local. Revisa el doctor.
- otro código no-cero tras pasar preflight: fallo real del proyecto o del gate funcional.

## Qué valida el gate
- preflight de entorno;
- lint y formato;
- typecheck;
- tests rápidos y cobertura;
- guardrails estructurales, seguridad y documentación.
