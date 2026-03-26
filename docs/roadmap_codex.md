# Roadmap operativo Codex (fuente de verdad)

> Documento operativo y atómico para ejecuciones autónomas.
> Regla de selección: tomar siempre la primera tarea `TODO` no bloqueada.
> Histórico narrativo complementario: `docs/roadmap_codex_automation.md`.

## Relación con el histórico narrativo

- `docs/roadmap_codex.md` define el backlog seleccionable y el estado vigente de cada tarea.
- `docs/roadmap_codex_automation.md` conserva contexto narrativo de ciclos previos, pero no reordena ni sustituye este roadmap.
- Si un “Siguiente paso recomendado” del histórico sigue vigente, primero debe materializarse aquí como tarea `TODO` antes de poder ejecutarse.
- Si ambos documentos divergen, prevalece este roadmap operativo.

## Estado seleccionable actual

- 2026-03-26 21:36:42Z: backlog operativo reabierto. La primera tarea `TODO` no bloqueada es `RCDX-007 — Retirar o alinear launcher Windows legado`, porque `launch.bat` sigue versionado en la raíz, exige `main.py` inexistente y conserva branding `Horas Sindicales`, mientras los entrypoints soportados del repo son `scripts/run_app.py`, `START_APP.bat` y `launcher.bat`.

## Tareas

### RCDX-001 — Fundar contrato operativo de automations
- **estado**: DONE
- **objetivo**: Establecer contrato permanente para agentes, roadmap operativo y bitácora append-only.
- **alcance permitido**:
  - actualizar `AGENTS.md` como contrato operativo del repo,
  - crear `docs/roadmap_codex.md`,
  - crear `docs/bitacora_codex.md`,
  - aclarar relación con `docs/roadmap_codex_automation.md`.
- **fuera de alcance**:
  - cambios de lógica de negocio,
  - UI/infra/CI,
  - refactors funcionales.
- **archivos o zonas probables**:
  - `AGENTS.md`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
  - `docs/roadmap_codex_automation.md`
- **checks obligatorios**:
  - `python -m scripts.gate_rapido`
  - verificación manual de no binarios en diff
- **criterios de cierre**:
  - contrato operativo explícito y ejecutable para Codex,
  - roadmap atómico listo para selección automática,
  - bitácora inicializada y append-only.
- **dependencias o bloqueo**: ninguna.

### RCDX-002 — Enlazar ejecución diaria con disciplina de una tarea
- **estado**: BLOCKED
- **objetivo**: Asegurar que cada run mantenga disciplina de una única tarea y sin expansión de alcance.
- **alcance permitido**:
  - reforzar texto operativo en docs si hay ambigüedad residual,
  - verificar consistencia entre `AGENTS.md`, roadmap y bitácora.
- **fuera de alcance**:
  - cambios de producto,
  - cambios de scripts del gate.
- **archivos o zonas probables**:
  - `AGENTS.md`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `python -m scripts.gate_rapido`
- **criterios de cierre**:
  - no hay contradicciones entre contrato y operación diaria,
  - queda explícito cómo proceder ante bloqueo y parada,
  - queda explícita la regla `DONE` vs `BLOCKED` cuando no se pueden completar checks obligatorios,
  - roadmap y bitácora documentan `N/A por bloqueo operativo` para metadata de commit/PR cuando corresponda.
- **dependencias o bloqueo**: RCDX-001 DONE. Revalidación 2026-03-26: persiste bloqueo operativo de validación con `reason_code=DEPENDENCIAS_FALTANTES` en `python -m scripts.doctor_entorno_calidad` y `rc=20` en `python -m scripts.gate_rapido`; `python scripts/setup.py` no logra instalar dependencias runtime por proxy/red (`Tunnel connection failed: 403 Forbidden` y `No matching distribution found for PySide6==6.8.3`) sin wheelhouse local, por lo que no se puede alinear el toolchain en este entorno.

### RCDX-003 — Mantener trazabilidad entre roadmap operativo e histórico
- **estado**: DONE
- **objetivo**: Evitar deriva entre roadmap operativo actual e histórico narrativo de automatizaciones.
- **alcance permitido**:
  - añadir notas de enlace cruzado y reglas de actualización mínima.
- **fuera de alcance**:
  - reescritura histórica completa,
  - compactación destructiva del historial.
- **archivos o zonas probables**:
  - `docs/roadmap_codex.md`
  - `docs/roadmap_codex_automation.md`
- **checks obligatorios**:
  - `python -m scripts.gate_rapido`
- **criterios de cierre**:
  - relación histórico↔operativo inequívoca y estable.
- **dependencias o bloqueo**: RCDX-001 DONE.

### RCDX-004 — Estandarizar plantilla de cierre en bitácora
- **estado**: BLOCKED
- **objetivo**: Consolidar formato de evidencia para cierres de ejecución (checks, decisión, siguiente paso).
- **alcance permitido**:
  - ajustar únicamente estructura documental de `docs/bitacora_codex.md`.
- **fuera de alcance**:
  - cambios de scripts,
  - cambios funcionales de producto.
- **archivos o zonas probables**:
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `python -m scripts.gate_rapido`
- **criterios de cierre**:
  - plantilla clara, reutilizable y append-only.
- **dependencias o bloqueo**: RCDX-001 DONE. Revalidación 2026-03-26: `python -m scripts.gate_rapido` aborta con `rc=20`/`reason_code=VENV_REPO_NO_DISPONIBLE`; `python scripts/setup.py` y `python -m venv .venv` fallan al ejecutar `ensurepip`; además `python -c "import tempfile, pathlib; d=tempfile.TemporaryDirectory(dir='.tmp'); p=pathlib.Path(d.name)/'probe.txt'; p.write_text('ok', encoding='utf-8')"` reproduce `PermissionError [Errno 13]`/`WinError 5` incluso dentro de `.tmp` del worktree, por lo que `.venv` queda parcial sin `pip` y no se puede instalar el toolchain obligatorio (`ruff`, `pytest`, `mypy`, `pip-audit`) ni completar la validación.

### RCDX-005 — Registrar backlog sin tarea seleccionable
- **estado**: BLOCKED
- **objetivo**: Hacer explícito el bloqueo contractual cuando el roadmap operativo queda sin ninguna tarea `TODO` elegible para automations.
- **alcance permitido**:
  - documentar el agotamiento o bloqueo total del backlog seleccionable,
  - exigir definición de la siguiente tarea priorizada o cierre explícito del backlog,
  - mantener trazabilidad entre roadmap y bitácora sin inventar trabajo funcional.
- **fuera de alcance**:
  - crear prioridad funcional nueva sin decisión humana,
  - ejecutar cambios de producto sin tarea seleccionable,
  - reordenar tareas ya registradas.
- **archivos o zonas probables**:
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `python -m scripts.gate_rapido`
- **criterios de cierre**:
  - existe al menos una tarea `TODO` no bloqueada en el roadmap, o
  - se declara explícitamente que el backlog operativo queda cerrado.
- **dependencias o bloqueo**: El roadmap vigente solo contiene `RCDX-001` DONE, `RCDX-002` BLOCKED, `RCDX-003` DONE y `RCDX-004` BLOCKED; no existe ninguna entrada `TODO` seleccionable. Revalidación 2026-03-26 16:02Z: la ejecución sigue en la rama aislada `codex/radar-inspector-20260326` y `python -m scripts.gate_rapido` aborta con `rc=20`/`reason_code=DEPENDENCIAS_FALTANTES` porque faltan `ruff`, `pytest`, `mypy` y `pip-audit` en `.venv`; además `wheelhouse/` sigue ausente, por lo que tampoco hay validación automática disponible para promover este cierre documental a `DONE`. Revalidación 2026-03-26 18:02Z: persiste la misma ausencia de tarea `TODO` elegible y el gate vuelve a abortar en preflight con `reason_code=DEPENDENCIAS_FALTANTES`; el doctor confirma que el intérprete del repo sí es utilizable, pero siguen faltando `ruff`, `pytest`, `mypy` y `pip-audit` y no existe `wheelhouse/`, por lo que continúa el doble bloqueo de gobernanza y toolchain. Revalidación 2026-03-26 18:02:28Z: la rama activa sigue siendo `codex/radar-inspector-20260326`, el selector continúa sin ninguna `TODO` elegible y `python -m scripts.gate_rapido` vuelve a abortar con `rc=20`/`reason_code=DEPENDENCIAS_FALTANTES`; faltan `ruff`, `pytest`, `mypy` y `pip-audit` en `.venv` y `wheelhouse/` permanece ausente, así que el bloqueo contractual y el del toolchain siguen sin cambios. Revalidación 2026-03-26 19:01:50Z: la ejecución permanece en la rama aislada `codex/radar-inspector-20260326`, `git status --short --untracked-files=no` solo muestra cambios documentales en `docs/roadmap_codex.md` y `docs/bitacora_codex.md`, el selector sigue sin ninguna `TODO` elegible y `python -m scripts.gate_rapido` vuelve a abortar con `rc=20`/`reason_code=DEPENDENCIAS_FALTANTES`; el doctor confirma de nuevo que faltan `ruff`, `pytest`, `mypy` y `pip-audit` en `.venv` y que `wheelhouse/` sigue ausente. Revalidación 2026-03-26 20:01:16Z: la ejecución sigue en la rama aislada `codex/radar-inspector-20260326`, `git status --short --untracked-files=no` estaba limpio antes de documentar, el selector continúa sin ninguna `TODO` elegible y `python -m scripts.gate_rapido` vuelve a abortar con `rc=20`/`reason_code=DEPENDENCIAS_FALTANTES`; el doctor confirma otra vez que faltan `ruff`, `pytest`, `mypy` y `pip-audit` en `.venv` y que `wheelhouse/` permanece ausente. Revalidación 2026-03-26 21:36:42Z: deja de aplicar el cierre total del backlog porque se detecta `launch.bat` versionado en la raíz como entrypoint Windows legado roto; el archivo exige `main.py` inexistente, ejecuta `main.py` y muestra `Launcher Horas Sindicales iniciado`, mientras `README.md`, `scripts/run_app.py`, `START_APP.bat` y `launcher.bat` ya apuntan al entrypoint real `clinicdesk.app.main`. Se materializa `RCDX-007` como primera `TODO` no bloqueada; `python -m scripts.gate_rapido` sigue abortando con `rc=20`/`reason_code=DEPENDENCIAS_FALTANTES` por ausencia de `ruff`, `pytest`, `mypy` y `pip-audit` en `.venv`.

### RCDX-006 — Saneamiento contractual Bootstrap 1
- **estado**: BLOCKED
- **objetivo**: Verificar y corregir contradicciones mínimas entre contrato, roadmap, bitácora, gates canónicos y la variante real de arquitectura del repo para dejar el backlog listo para automations seguras.
- **alcance permitido**:
  - ajustar `AGENTS.md` para mapear Clean Architecture a `clinicdesk/app/domain`, `clinicdesk/app/application`, `clinicdesk/app/infrastructure`, `clinicdesk/app/ui` y `clinicdesk/app/pages`,
  - actualizar `docs/roadmap_codex.md` para reflejar esta priorización humana y el estado seleccionable real del backlog,
  - añadir evidencia append-only en `docs/bitacora_codex.md`,
  - tocar `docs/roadmap_codex_automation.md` solo si aparece una contradicción contractual estricta.
- **fuera de alcance**:
  - cambios de producto,
  - cambios de scripts, CI o dependencias,
  - refactors funcionales o de arquitectura ejecutable.
- **archivos o zonas probables**:
  - `AGENTS.md`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
  - `docs/roadmap_codex_automation.md`
- **checks obligatorios**:
  - `python -m scripts.gate_rapido`
  - verificación manual de no binarios en diff
- **criterios de cierre**:
  - el contrato operativo referencia la variante real de capas del repo,
  - el roadmap deja explícito si existe tarea seleccionable o backlog cerrado,
  - la bitácora registra decisiones, checks y bloqueo real de entorno si aplica.
- **dependencias o bloqueo**: Priorización humana 2026-03-26: `BOOTSTRAP CONTRATO 1`. Revalidación 2026-03-26 20:11:48Z: `python -m scripts.gate_rapido` vuelve a abortar con `rc=20`/`reason_code=DEPENDENCIAS_FALTANTES`; el intérprete de `.venv` es utilizable, pero siguen ausentes `ruff`, `pytest`, `mypy` y `pip-audit`, `wheelhouse/` permanece ausente y el check obligatorio no queda en verde. La tarea debe cerrarse en `BLOCKED` y el backlog operativo vuelve a quedar cerrado hasta nueva priorización humana.

### RCDX-007 — Retirar o alinear launcher Windows legado
- **estado**: TODO
- **objetivo**: Eliminar el entrypoint Windows versionado que hoy no puede arrancar la app y contradice el branding y los entrypoints soportados del repo.
- **alcance permitido**:
  - corregir `launch.bat` para que delegue al entrypoint real soportado o retirarlo si se confirma que es legado no soportado,
  - mantener consistencia mínima con `START_APP.bat`, `launcher.bat` y `README.md`,
  - añadir guardarraíl o verificación mínima si hace falta para evitar la reintroducción del launcher legado roto.
- **fuera de alcance**:
  - cambios de lógica de negocio o UI,
  - cambios de packaging/release más allá del launcher raíz,
  - cambios de CI, dependencias o setup.
- **archivos o zonas probables**:
  - `launch.bat`
  - `START_APP.bat`
  - `launcher.bat`
  - `README.md`
  - `tests/guardrails/test_saneamiento_legacy_repo.py`
- **checks obligatorios**:
  - `python -m scripts.gate_rapido`
  - `pytest -q tests/guardrails/test_saneamiento_legacy_repo.py tests/test_build_release.py`
- **criterios de cierre**:
  - `launch.bat` deja de apuntar a `main.py` inexistente y ya no conserva branding ajeno,
  - los launchers Windows soportados quedan alineados con `clinicdesk.app.main` o `scripts/run_app.py`,
  - existe una protección mínima para que el launcher legado roto no reaparezca.
- **dependencias o bloqueo**: Evidencia 2026-03-26 21:36:42Z: `launch.bat` versionado en la raíz comprueba `main.py`, ejecuta `"%VENV_PY%" main.py` y muestra `Launcher Horas Sindicales iniciado`; `main.py` no existe en la raíz del repo y el README documenta `python scripts/run_app.py`, mientras `START_APP.bat` y `launcher.bat` sí delegan a `clinicdesk.app.main`.
