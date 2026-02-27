# ML Roadmap en Prompts de Codex (Strangler, incremental)

> Objetivo: evolucionar ClinicDesk hacia una base mantenible y escalable, lista para integrar ML útil sin acoplarlo a la UI.

## Prompt 1 — Establecer Quality Gate CI para Core
**Reglas fijas (obligatorias):**
- CI estricto y alto: coverage >= 85% sobre CORE ignorando UI.
- Clean Architecture 100%: domain/application/infrastructure/presentation con dependencias correctas.
- Evitar monolitos: funciones y clases pequeñas, con responsabilidad única.
- Evitar duplicación: usar piezas canónicas y eliminar duplicados.
- Registrar cambios en `docs/progress_log.md`.

**Objetivo único:** definir y automatizar gate de calidad para el core.
**Cambios esperados:** `docs/ci_quality_gate.md`, `docs/TESTING.md`, configuración de CI (si aplica).
**Tests a añadir:** smoke de ejecución de pytest con `--cov` sobre core.
**Criterio de éxito:** CI falla si coverage core <85% y no bloquea por UI.

## Prompt 2 — Congelar contrato de arquitectura por capas
**Reglas fijas (obligatorias):** (mismas 5 reglas del prompt 1)

**Objetivo único:** explicitar reglas de importación y límites por capa.
**Cambios esperados:** `docs/architecture_contract.md`, pruebas de arquitectura básicas (si hay framework disponible).
**Tests a añadir:** test de imports prohibidos (p. ej., domain importando infrastructure).
**Criterio de éxito:** imports inválidos detectados automáticamente en CI.

## Prompt 3 — Normalizar estructura de paquetes core
**Reglas fijas (obligatorias):** (mismas 5 reglas del prompt 1)

**Objetivo único:** alinear estructura física con contrato sin refactor masivo.
**Cambios esperados:** ajustes mínimos en `clinicdesk/app/domain`, `clinicdesk/app/application`, `clinicdesk/app/infrastructure`.
**Tests a añadir:** tests de importación y tests existentes en verde.
**Criterio de éxito:** estructura coherente por capas y sin regresiones.

## Prompt 4 — Definir puertos de lectura/escritura clínicos
**Reglas fijas (obligatorias):** (mismas 5 reglas del prompt 1)

**Objetivo único:** declarar ports contract-first para repositorios principales.
**Cambios esperados:** `clinicdesk/app/domain/repositorios.py` y/o `clinicdesk/app/application/ports/*`.
**Tests a añadir:** tests de contrato de puertos (Protocol/ABC).
**Criterio de éxito:** casos de uso consumen interfaces, no implementaciones SQLite.

## Prompt 5 — Extraer un caso de uso vertical (citas) a patrón estándar
**Reglas fijas (obligatorias):** (mismas 5 reglas del prompt 1)

**Objetivo único:** migrar un caso de uso por borde (crear cita) a I/O tipado y errores explícitos.
**Cambios esperados:** `clinicdesk/app/application/usecases/crear_cita.py`, adaptadores mínimos.
**Tests a añadir:** unit tests del caso de uso (happy path + errores de dominio).
**Criterio de éxito:** controlador/UI solo orquesta; lógica en application/domain.

## Prompt 6 — Introducir eventos de dominio mínimos
**Reglas fijas (obligatorias):** (mismas 5 reglas del prompt 1)

**Objetivo único:** modelar eventos relevantes (p. ej. CitaCreada, StockAjustado).
**Cambios esperados:** `clinicdesk/app/domain/modelos.py` o módulo `events.py`.
**Tests a añadir:** tests de creación/publicación de eventos (sin broker externo).
**Criterio de éxito:** eventos desacoplados y consumibles por application.

## Prompt 7 — Pipeline de datos clínicos v1 (extracción)
**Reglas fijas (obligatorias):** (mismas 5 reglas del prompt 1)

**Objetivo único:** crear servicio application para extraer dataset desde repositorios.
**Cambios esperados:** `clinicdesk/app/application/data_pipeline/*`, adaptador SQLite.
**Tests a añadir:** unit tests del pipeline (filtros, ventanas temporales, validación).
**Criterio de éxito:** dataset reproducible sin dependencias de UI.

## Prompt 8 — Transformaciones y validación de features v1
**Reglas fijas (obligatorias):** (mismas 5 reglas del prompt 1)

**Objetivo único:** convertir dataset crudo a features canónicas en application.
**Cambios esperados:** `clinicdesk/app/application/features/*`.
**Tests a añadir:** tests de transformaciones puras y manejo de nulos/outliers básicos.
**Criterio de éxito:** funciones puras, pequeñas y testeadas.

## Prompt 9 — Feature Store mínimo (offline, local)
**Reglas fijas (obligatorias):** (mismas 5 reglas del prompt 1)

**Objetivo único:** definir port de feature store e implementación local mínima.
**Cambios esperados:** puertos en application/domain + adaptador en infrastructure (SQLite/archivos).
**Tests a añadir:** tests de contrato (save/load/versionado básico).
**Criterio de éxito:** casos de uso de features dependen de port, no de storage concreto.

## Prompt 10 — Baseline ML dummy desacoplado
**Reglas fijas (obligatorias):** (mismas 5 reglas del prompt 1)

**Objetivo único:** añadir baseline predictor simple (heurístico o modelo trivial) como servicio.
**Cambios esperados:** `clinicdesk/app/application/ml/*`, puertos de inferencia.
**Tests a añadir:** tests de inferencia determinística + manejo de entradas inválidas.
**Criterio de éxito:** baseline invocable desde application, sin lógica ML en UI.

## Prompt 11 — Caso de uso de scoring integrado
**Reglas fijas (obligatorias):** (mismas 5 reglas del prompt 1)

**Objetivo único:** crear use case que use feature store + baseline para generar score útil.
**Cambios esperados:** nuevo use case en `clinicdesk/app/application/usecases/*` y adaptadores.
**Tests a añadir:** unit tests end-to-end de application (sin UI).
**Criterio de éxito:** flujo completo datos→features→modelo→resultado con contratos claros.

## Prompt 12 — Observabilidad mínima y trazabilidad
**Reglas fijas (obligatorias):** (mismas 5 reglas del prompt 1)

**Objetivo único:** registrar métricas básicas de pipeline/scoring y decisiones.
**Cambios esperados:** logging estructurado en application/infrastructure.
**Tests a añadir:** tests de eventos/logs críticos.
**Criterio de éxito:** trazabilidad de ejecuciones sin contaminar domain.

## Prompt 13 — Hardening de tests de core y deuda técnica
**Reglas fijas (obligatorias):** (mismas 5 reglas del prompt 1)

**Objetivo único:** elevar cobertura de core >85% sostenida y reducir flaky tests.
**Cambios esperados:** tests en `tests/` + ajustes menores de diseño para testabilidad.
**Tests a añadir:** casos borde faltantes y regresiones detectadas.
**Criterio de éxito:** coverage core >=85% estable en CI.

## Prompt 14 — Interfaz de aplicación para consumo UI/API
**Reglas fijas (obligatorias):** (mismas 5 reglas del prompt 1)

**Objetivo único:** definir façade/application service para que UI no conozca detalles ML.
**Cambios esperados:** servicios application + adaptación mínima en controllers.
**Tests a añadir:** tests de integración ligera controller→usecase (dobles de puertos).
**Criterio de éxito:** UI thin, toda decisión en application/domain.

## Prompt 15 — Cierre de fase: checklist de producción interna
**Reglas fijas (obligatorias):** (mismas 5 reglas del prompt 1)

**Objetivo único:** validar que la base ML está integrada limpiamente y mantenible.
**Cambios esperados:** actualización de docs (`progress_log`, contrato, quality gate).
**Tests a añadir:** suite de regresión de core completa.
**Criterio de éxito:** CI verde, arquitectura respetada, pipeline+feature store+baseline activos.
