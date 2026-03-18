# Pendientes funcionales (derivado de `docs/features.json`)

## Funciones con trabajo pendiente

- **FTR-004 — Se puede crear y consultar citas clínicas**
  - Pendiente principal: Hay cobertura robusta de caso de uso y queries; la verificación UI existe en componentes aislados, sin E2E extremo a extremo confirmado para el ciclo completo de agenda.
- **FTR-005 — Se puede ejecutar pipeline ML de riesgo de citas**
  - Pendiente principal: Core analítico con buena cobertura; no hay evidencia en este corte de un escenario E2E automatizado que recorra UI + pipeline completo.
- **FTR-008 — Se puede rotar claves criptográficas de campos sensibles**
  - Pendiente principal: Cobertura fuerte de contrato CLI y no exposición de PII; no hay escenario E2E operacional de rotación dentro de despliegue real automatizado.
- **FTR-009 — WEB_LORE_V1 en Next.js como slice extremo a extremo**
  - Pendiente principal: Bloqueada en esta rama: no existen rutas frontend/ ni web/apps/lore; el repositorio activo es una app de escritorio Python + API read-only opcional, por lo que no se puede implementar el slice solicitado sin cambiar de código base.

## Funciones con estado "No verificada" por dimensión

- FTR-003: UI, E2E.
- FTR-004: E2E.
- FTR-005: UI, E2E.
- FTR-008: E2E.
