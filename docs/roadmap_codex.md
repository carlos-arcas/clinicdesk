# Roadmap operativo Codex (fuente de verdad)

> Documento operativo y atómico para ejecuciones autónomas.
> Regla de selección: tomar siempre la primera tarea `TODO` no bloqueada.
> Histórico narrativo complementario: `docs/roadmap_codex_automation.md`.

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
- **dependencias o bloqueo**: RCDX-001 DONE. Bloqueo operativo activo de validación: `VENV_REPO_NO_DISPONIBLE` al ejecutar `python -m scripts.gate_rapido`.

### RCDX-003 — Mantener trazabilidad entre roadmap operativo e histórico
- **estado**: TODO
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
- **estado**: TODO
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
- **dependencias o bloqueo**: RCDX-001 DONE.
