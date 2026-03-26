# AGENTS.md — Contrato operativo de Codex Automations (ClinicDesk)

Este documento define cómo debe trabajar cualquier agente automático en este repositorio.
Es un contrato ejecutable: si hay duda, prevalece este archivo.

## 1) Fuente de verdad y selección de trabajo

1. **Fuente de verdad operativa**: `docs/roadmap_codex.md`.
2. En cada ejecución, el agente debe:
   - tomar **solo una** tarea,
   - elegir la **primera tarea en `TODO` que no esté bloqueada** (orden textual, de arriba hacia abajo, sin saltos),
   - moverla a `WIP` al iniciar y a `DONE`/`BLOCKED` al cerrar.
3. **Prohibido expandir alcance**: no incluir mejoras “ya que estamos”.
4. Si detectas bloqueo real (técnico, de dependencia o de contrato):
   - no improvises,
   - documenta evidencia,
   - marca tarea `BLOCKED`,
   - registra siguiente paso exacto,
   - termina la ejecución.

## 2) Gates canónicos obligatorios

Comandos canónicos y versionados del repositorio:

- Gate rápido: `python -m scripts.gate_rapido`
- Gate completo (PR/CI): `python -m scripts.gate_pr`

Reglas:
- CI debe ejecutar exactamente `python -m scripts.gate_pr`.
- No se permite reemplazar estos comandos por variantes ad-hoc.
- Política de PR: **no abrir PR si `python -m scripts.gate_pr` no pasa**.
- Máximo 3 ciclos de “arreglar → re-ejecutar gate completo” antes de parar y reportar bloqueo.

## 3) Arquitectura (Clean Architecture estricta)

Capas y límites:

- Este repo no usa carpetas top-level `dominio/`, `aplicacion/`, `infraestructura/` y `presentacion/`.
- La variante real y obligatoria vive en `clinicdesk/app/`:
  - `clinicdesk/app/domain`: reglas de negocio puras, sin dependencias externas.
  - `clinicdesk/app/application`: casos de uso, DTOs y puertos; depende de `domain`.
  - `clinicdesk/app/infrastructure`: adaptadores concretos; implementa puertos.
  - `clinicdesk/app/ui` y `clinicdesk/app/pages`: presentación desktop, wiring visual y coordinación de entrada/salida, sin lógica de negocio.
- Cuando este contrato hable de `dominio`, `aplicacion`, `infraestructura` y `presentacion`, debe interpretarse sobre esas rutas reales del repo.
- La composición de infraestructura concreta solo puede resolverse en `clinicdesk/app/container.py` y `clinicdesk/app/composicion/**`, en línea con `docs/architecture_contract.md`.

Prohibiciones duras:
- mezclar reglas de negocio en UI/controladores/adaptadores de entrada,
- dependencias invertidas entre capas,
- atajos que salten casos de uso desde presentación a infraestructura.

## 4) Calidad, tests y Definition of Done

No hay tarea terminada sin cumplir lo siguiente:

- lint y formato en verde,
- typecheck donde aplique,
- tests deterministas,
- cobertura global mínima del gate (>=85%) en gate completo,
- guardarraíl de arquitectura activo,
- check de i18n/hardcodes activo,
- checks documentales sincronizados.

Regla de cierre sin ambigüedad:
- `DONE` solo si los checks obligatorios de la tarea se ejecutaron y quedaron en verde.
- Si un check obligatorio no puede ejecutarse o falla por bloqueo operativo de entorno/contrato, el estado de cierre obligatorio es `BLOCKED`.

Para cambios de ejecución normal:
1. ejecutar `python -m scripts.gate_rapido`,
2. antes de PR ejecutar `python -m scripts.gate_pr`.

## 5) UI, i18n y golden gate

- **Cero hardcodes visibles**: todo texto visible pasa por i18n.
- Si hay UI, los flujos relevantes deben ser testeables de forma determinista.
- Si aplica al cambio, mantener/actualizar pruebas golden (`tests/golden`) con intención explícita.
- No usar snapshots frágiles cuando un contrato semántico estable sea suficiente.

## 6) Seguridad, validación y logging

- Validación explícita de entradas antes de llegar a dominio.
- Manejo explícito de errores (sin silencios ambiguos).
- Logging estructurado obligatorio.
- Prohibido `print()` para observabilidad operativa.
- No exponer PII ni secretos en logs o mensajes al usuario.

## 7) Límites de cambio y deuda técnica

- Cambios mínimos y de alta confianza.
- Sin refactor masivo fuera del alcance de la tarea activa.
- Todo código nuevo debe respetar:
  - archivo <= 300 LOC (salvo excepción justificada),
  - función <= 40 LOC (sin docstring),
  - complejidad ciclomática <= 10,
  - sin duplicación evitable,
  - nombres en español técnico coherente.

## 8) Prohibición de binarios/compilados en cambios

No se deben versionar ni modificar artefactos binarios/compilados en estas ejecuciones:

- `*.mo`
- `*.pyc`
- `*.sqlite3`
- `*.db`
- imágenes generadas
- `.zip`
- binarios `.pdf`

Si aparece alguno en el diff, hay que retirarlo antes de cerrar.

## 9) Roadmap y bitácora obligatorios

- Roadmap operativo: `docs/roadmap_codex.md`.
- Bitácora append-only: `docs/bitacora_codex.md`.
- Histórico narrativo: `docs/roadmap_codex_automation.md`.

Al cierre de **cada** ejecución se debe:
1. actualizar estado de la tarea en roadmap operativo,
2. añadir entrada nueva en bitácora (append-only),
3. dejar checks ejecutados y resultado,
4. documentar bloqueos si existen.

## 10) Qué hacer si no puedes validar en el entorno

Si el entorno impide ejecutar checks obligatorios:
- se registra como bloqueo operativo,
- se documentan comandos exactos intentados,
- se deja diagnóstico concreto,
- no se inventa PASS ni se abre PR fuera de política.
- no se registra metadata de commit/PR como evidencia de validación (usar `N/A por bloqueo operativo`), hasta destrabar y revalidar.

## 11) Relación con documentación histórica

`docs/roadmap_codex_automation.md` se conserva como **histórico** de ciclos previos.
La planificación activa y seleccionable por automations vive en `docs/roadmap_codex.md`.

## Changelog del contrato
- v2.1: el contrato deja explícita la variante real de capas del repo (`clinicdesk/app/domain|application|infrastructure|ui/pages`) y los puntos válidos de composición.
- v2.0: contrato operativo específico para Codex Automations en ClinicDesk (fuente de verdad, selección única de tarea, política de bloqueo, roadmap/bitácora obligatorios, prohibición explícita de binarios).
- v1.x: contrato genérico previo (arquitectura, gates, calidad, i18n, seguridad y DoD).
