# Bitácora Codex (append-only)

Reglas:
- agregar entradas nuevas al final,
- no reescribir entradas previas salvo corrección factual mínima y explícita,
- cada entrada debe mapear a una tarea del `docs/roadmap_codex.md`.

---

## Entrada
- **fecha/hora**: 2026-03-26 11:06:42Z
- **tarea**: RCDX-001 — Fundar contrato operativo de automations
- **estado final**: DONE
- **archivos tocados**:
  - `AGENTS.md`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
  - `docs/roadmap_codex_automation.md`
- **decisiones**:
  - Se promovió `AGENTS.md` a contrato operativo específico del repo, manteniendo gates canónicos existentes.
  - Se creó roadmap operativo atómico como fuente de verdad (`docs/roadmap_codex.md`).
  - Se inicializó bitácora append-only con estructura obligatoria de trazabilidad.
  - Se mantuvo el histórico `docs/roadmap_codex_automation.md` y se aclaró su rol como histórico.
- **checks ejecutados**:
  - `python -m scripts.gate_rapido`
  - `git status --short`
- **resultado**:
  - Documentación base de automations creada y alineada con el contrato de gates y arquitectura.
  - `python -m scripts.gate_rapido` no pudo validar funcionalmente por bloqueo operativo de entorno (`rc=20`, `reason_code=VENV_REPO_NO_DISPONIBLE`).
- **bloqueo o siguiente paso exacto**:
  - Bloqueo de validación: falta `/workspace/clinicdesk/.venv/bin/python`; acción de remediación indicada por gate: `python scripts/setup.py` y reintentar.
  - Tras remediar entorno, siguiente paso de producto documental: ejecutar RCDX-002 (primera `TODO` no bloqueada) sin ampliar alcance.

## Entrada
- **fecha/hora**: 2026-03-26 11:38:00Z
- **tarea**: RCDX-002 — Enlazar ejecución diaria con disciplina de una tarea
- **estado final**: BLOCKED
- **archivos tocados**:
  - `AGENTS.md`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **decisiones**:
  - Se eliminó ambigüedad sobre selección diaria: una sola tarea por ejecución y elección estricta de la primera `TODO` no bloqueada en orden textual.
  - Se explicitó regla de cierre: `DONE` solo con checks obligatorios en verde; bloqueo operativo en checks obliga cierre `BLOCKED`.
  - Se explicitó trazabilidad cuando no hay validación completa: metadata de commit/PR debe registrarse como `N/A por bloqueo operativo` hasta destrabar.
- **checks ejecutados**:
  - `python -m scripts.gate_rapido`
  - `git status --short`
- **resultado**:
  - Contrato y roadmap quedaron alineados para disciplina de una tarea por run, bloqueo y parada.
  - `python -m scripts.gate_rapido` quedó bloqueado por entorno (`rc=20`, `reason_code=VENV_REPO_NO_DISPONIBLE`), sin validación funcional del repositorio.
  - Metadata de commit/PR para validación: `N/A por bloqueo operativo`.
- **bloqueo o siguiente paso exacto**:
  - Bloqueo operativo: falta `/workspace/clinicdesk/.venv/bin/python`.
  - Ejecutar `python scripts/setup.py` y luego reintentar `python -m scripts.gate_rapido` sobre esta misma tarea antes de promoverla a `DONE`.

## Entrada
- **fecha/hora**: 2026-03-26 12:05:00Z
- **tarea**: RCDX-002 — Enlazar ejecución diaria con disciplina de una tarea
- **estado final**: BLOCKED
- **archivos tocados**:
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **decisiones**:
  - Se ejecutó el flujo canónico de recuperación de entorno definido en `docs/TESTING.md` para destrabar validación de RCDX-002.
  - No se aplicaron cambios de producto ni ajustes de lógica: el bloqueo actual es operativo externo (proxy/red) y no un defecto del setup/doctor del repo.
  - Se mantiene política de metadata de validación/PR en `N/A por bloqueo operativo` hasta recuperar conectividad o wheelhouse válido.
- **checks ejecutados**:
  - `python scripts/setup.py`
  - `python -m scripts.doctor_entorno_calidad`
  - `python -m scripts.gate_rapido`
  - `python -m pip install -r requirements-dev.txt`
  - `git status --short`
- **resultado**:
  - `.venv` del repo se recreó y quedó detectable (`python esperado .venv: /workspace/clinicdesk/.venv/bin/python`, `Intérprete repo activo: sí`).
  - El doctor quedó en `reason_code=DEPENDENCIAS_FALTANTES` por toolchain desalineado/faltante (ruff/pytest/mypy/pip-audit).
  - `python scripts/setup.py` y la instalación manual del lock fallan contra índice remoto por proxy (`Tunnel connection failed: 403 Forbidden`) y no existe wheelhouse local utilizable.
  - `python -m scripts.gate_rapido` devuelve `rc=20` (bloqueo operativo local), por lo que RCDX-002 no puede pasar a `DONE`.
  - Metadata de validación/PR: `N/A por bloqueo operativo`.
- **bloqueo o siguiente paso exacto**:
  - Bloqueo operativo externo: acceso a dependencias bloqueado por proxy/red y sin wheelhouse del repo.
  - Siguiente paso exacto: habilitar conectividad del proxy/índice para `pip install` o proveer wheelhouse completo y válido; luego reejecutar en orden `python scripts/setup.py`, `python -m scripts.doctor_entorno_calidad`, `python -m scripts.gate_rapido` sobre RCDX-002.

## Entrada
- **fecha/hora**: 2026-03-26 12:22:00Z
- **tarea**: RCDX-002 — Enlazar ejecución diaria con disciplina de una tarea
- **estado final**: BLOCKED
- **archivos tocados**:
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **decisiones**:
  - Se ejecutó la secuencia canónica de revalidación solicitada (`setup` → `doctor` → `gate_rapido`) sin abrir trabajo nuevo de roadmap.
  - RCDX-002 no puede pasar a `DONE` porque el check obligatorio (`python -m scripts.gate_rapido`) no quedó en verde.
  - Se actualizó la trazabilidad del bloqueo con evidencia vigente de esta ejecución.
- **checks ejecutados**:
  - `python scripts/setup.py`
  - `python -m scripts.doctor_entorno_calidad`
  - `python -m scripts.gate_rapido`
  - `git status --short`
- **resultado**:
  - `python scripts/setup.py` crea/repara `.venv`, pero falla al instalar dependencias runtime por proxy/red (`Tunnel connection failed: 403 Forbidden`) y sin wheelhouse local; termina con `No matching distribution found for PySide6==6.8.3`.
  - `python -m scripts.doctor_entorno_calidad` queda en `reason_code=DEPENDENCIAS_FALTANTES` (toolchain desalineado/faltante: ruff, pytest, mypy, pip-audit).
  - `python -m scripts.gate_rapido` aborta con `rc=20` por bloqueo operativo local y no ejecuta validaciones funcionales del repositorio.
  - Metadata de validación/PR: `N/A por bloqueo operativo`.
- **bloqueo o siguiente paso exacto**:
  - Bloqueo operativo externo vigente: conectividad/proxy e índice no permiten completar instalación del lock, y no existe wheelhouse local utilizable.
  - Siguiente paso exacto: restaurar acceso efectivo al índice (o proveer wheelhouse completo compatible con `requirements-dev.txt` y `requirements.txt`), luego reejecutar en orden `python scripts/setup.py`, `python -m scripts.doctor_entorno_calidad`, `python -m scripts.gate_rapido` para reevaluar cierre de RCDX-002.
