# Quality gate de CI y PR

## Comandos canónicos
- Doctor de entorno: `python -m scripts.doctor_entorno_calidad`
- Doctor offline-first: `python -m scripts.doctor_entorno_calidad --require-wheelhouse`
- Gate rápido: `python -m scripts.gate_rapido`
- Gate completo PR/CI: `python -m scripts.gate_pr`

CI debe ejecutar exactamente `python -m scripts.gate_pr`.

## Flujo local recomendado
1. Ejecuta el doctor.
2. Si falta tooling o hay versiones desalineadas, ejecuta `python -m pip install -r requirements-dev.txt`.
3. Si el doctor reporta lock incoherente o desalineado con `requirements-dev.in`, ejecuta `python -m scripts.lock_deps`.
4. Si necesitas reproducibilidad sin red, valida `--require-wheelhouse`.
5. Cuando el doctor quede en verde, ejecuta `python -m scripts.gate_pr`.

## Fuente de verdad del tooling
- Versiones fijadas: `requirements-dev.txt`
- Entrada editable: `requirements-dev.in`
- Regeneración del lock: `python -m scripts.lock_deps`

El doctor, el preflight del gate y las validaciones específicas de Ruff consumen esa misma fuente de verdad.

## Significado de `rc=20`
`rc=20` en `python -m scripts.gate_pr` significa **bloqueo operativo del entorno local**. El proyecto todavía no fue validado por el gate funcional.

## Entornos con proxy/red restringida
- Si no hay wheelhouse, `setup.py` deja claro que la instalación depende de red/proxy reales.
- Si hay wheelhouse pero es incompatible o incompleto, `setup.py` lo reporta como problema de wheelhouse/configuración, no como PASS.
- El repo no añade binarios ni degrada el gate para ocultar fallos.

## Si falla
- **Bloqueo de entorno**: corrige lo que indique el doctor y vuelve a correr `python -m scripts.gate_pr`.
- **Fallo de proyecto**: corrige el problema real del repositorio y reejecuta el gate completo.
