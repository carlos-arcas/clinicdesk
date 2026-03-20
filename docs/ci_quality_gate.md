# Quality gate de CI y PR

## Comandos canónicos
- Doctor de entorno: `python -m scripts.doctor_entorno_calidad`
- Gate rápido: `python -m scripts.gate_rapido`
- Gate completo PR/CI: `python -m scripts.gate_pr`

CI debe ejecutar exactamente `python -m scripts.gate_pr`.

## Flujo local recomendado
1. `python -m scripts.doctor_entorno_calidad`
2. Si reporta tooling ausente o desalineado: `python -m pip install -r requirements-dev.txt`
3. Si reporta lock dev incoherente: `python -m scripts.lock_deps`
4. Cuando el doctor quede en verde: `python -m scripts.gate_pr`

## Fuente de verdad del tooling
- Versiones fijadas: `requirements-dev.txt`
- Entrada editable: `requirements-dev.in`
- Regeneración del lock: `python -m scripts.lock_deps`

El doctor y el gate leen las versiones esperadas desde esa fuente y no mantienen una lista paralela de versiones.

## Qué valida el gate completo
1. Preflight de entorno con diagnóstico explícito del toolchain.
2. Ruff (`check` y `format --check`).
3. Typecheck incremental con mypy.
4. `pytest -q` en el scope bloqueante.
5. Cobertura mínima del core (`>= 85%`).
6. Guardrails estructurales: arquitectura, tamaño, complejidad y residuos prohibidos.
7. Seguridad: `pip-audit`, escaneo de secretos y control básico de PII en logs.
8. Documentación contractual y checklist funcional.

## Entornos con proxy/red restringida
- Si no hay wheelhouse, `setup.py` y el doctor indicarán que la reinstalación depende de red/proxy reales.
- El repo no añade wheels ni degrada el gate para “simular” un PASS.
- Opción offline-first soportada: preparar un wheelhouse externo y apuntarlo con `CLINICDESK_WHEELHOUSE`.

## Si falla
- **Bloqueo de entorno**: corrige primero lo que indique `python -m scripts.doctor_entorno_calidad`.
- **Fallo de proyecto**: corrige el problema real y reejecuta el gate completo.
- No bajar umbrales ni desactivar checks para “pasar”.
