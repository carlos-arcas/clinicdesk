# Quality gate de CI y PR

## Comandos canónicos
- Setup local recomendado: `python scripts/setup.py`
- Doctor de entorno: `python -m scripts.doctor_entorno_calidad`
- Doctor offline-first: `python -m scripts.doctor_entorno_calidad --require-wheelhouse`
- Gate rápido: `python -m scripts.gate_rapido`
- Gate completo PR/CI: `python -m scripts.gate_pr`

CI debe ejecutar exactamente `python -m scripts.gate_pr`.

## Flujo local recomendado
1. Ejecuta `python scripts/setup.py` para crear o reparar `.venv`.
2. Usa siempre los comandos canónicos del repo. Si `.venv` existe y es utilizable, `doctor`, `gate_rapido` y `gate_pr` se reejecutan automáticamente con ese intérprete.
3. Ejecuta el doctor.
4. Si falta tooling o hay versiones desalineadas, ejecuta `python -m pip install -r requirements-dev.txt` dentro del Python del repo o vuelve a correr `python scripts/setup.py`.
5. Si el doctor reporta lock incoherente o desalineado con `requirements-dev.in`, ejecuta `python -m scripts.lock_deps`.
6. Si necesitas reproducibilidad sin red, valida `--require-wheelhouse`.
7. Cuando el doctor quede en verde, ejecuta `python -m scripts.gate_pr`.

## Flujo CI real
Los workflows de CI hacen la misma secuencia lógica:
1. `actions/setup-python` fija la versión de Python del job.
2. Se instalan `requirements.txt` y `requirements-dev.txt`.
3. Se ejecuta `python -m scripts.doctor_entorno_calidad` como evidencia de preflight.
4. Se ejecuta el gate canónico `python -m scripts.gate_pr`.

En CI no se usa `setup.py` porque el runner no necesita crear `.venv`; el equivalente es `actions/setup-python` + instalación explícita del lock. La autorreejecución canónica se desactiva en CI para no interferir con ese flujo.

## Fuente de verdad del tooling
- Versiones fijadas: `requirements-dev.txt`
- Entrada editable: `requirements-dev.in`
- Regeneración del lock: `python -m scripts.lock_deps`
- Python mínimo del repo: `pyproject.toml`

El doctor, el preflight del gate y las validaciones específicas de Ruff consumen esa misma fuente de verdad.

## Significado de `rc=20`
`rc=20` en `python -m scripts.gate_pr` significa **bloqueo operativo del entorno local o del job**. El proyecto todavía no fue validado por el gate funcional. Si el problema era ejecutar con un Python ajeno al repo y `.venv` existe, el comando ya se habrá reejecutado automáticamente antes de llegar a ese punto.

## Glosario breve de `reason_code` operativo
Fuente de verdad de códigos documentables del contrato operativo: `scripts.gate_pr.reason_codes_operativos_documentables()`.

| `reason_code` | Significado corto | Acción sugerida |
| --- | --- | --- |
| `VENV_REPO_NO_DISPONIBLE` | El comando canónico no puede usar el Python esperado del repo (`.venv`). | `python scripts/setup.py` y reintentar el comando canónico. |
| `TOOLCHAIN_LOCK_INVALIDO` | El lock de desarrollo no es coherente con lo requerido por el gate. | `python -m scripts.lock_deps` y luego `python scripts/setup.py`. |
| `DEPENDENCIAS_FALTANTES` | Faltan herramientas del gate en el intérprete activo. | `python -m pip install -r requirements-dev.txt`. |
| `TOOLCHAIN_DESALINEADO` | Hay tooling instalado con versión distinta al lock. | `python -m pip install -r requirements-dev.txt`. |
| `WHEELHOUSE_REQUERIDO_NO_DISPONIBLE` | Se exigió modo offline y el wheelhouse no cubre el lock. | `python -m scripts.build_wheelhouse` y repetir doctor/gate. |
| `RED_PROXY_REQUERIDA_SIN_WHEELHOUSE` | Sin wheelhouse utilizable, la reparación depende de red/proxy. | `python -m scripts.doctor_entorno_calidad` y corregir proxy/red o generar wheelhouse. |

## Entornos con proxy/red restringida
- Si no hay wheelhouse, `setup.py` deja claro que la instalación depende de red/proxy reales.
- Si `CLINICDESK_WHEELHOUSE` apunta a una ruta inválida o incompleta, doctor/setup lo reportan de forma inmediata.
- Si hay wheelhouse pero es incompatible o incompleto, `setup.py` lo reporta como problema de wheelhouse/configuración, no como PASS.
- El repo no añade binarios ni degrada el gate para ocultar fallos.


## Contrato offline-first del wheelhouse
- `doctor` y `setup.py` validan el wheelhouse contra la misma fuente de verdad del lock: `requirements-dev.txt` y sus includes.
- Un wheelhouse con wheels irrelevantes o parciales se marca como **incompleto**, no como disponible.
- `build_wheelhouse` ahora verifica la cobertura del lock al final de la descarga y falla si aún faltan paquetes/versiones.
- La ruta offline-first solo es realmente recuperable cuando el estado reportado es **utilizable**.

## Cómo distinguir bloqueo de entorno vs fallo de proyecto
- **Bloqueo de entorno**: corrige lo que indique el doctor y vuelve a correr `python -m scripts.gate_pr`.
- **Fallo de proyecto**: si el doctor está alineado y el gate cae después, corrige el problema real del repositorio y reejecuta el gate completo.
