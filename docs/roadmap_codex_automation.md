# Roadmap Codex Automation

> Nota (2026-03-26): este documento se mantiene como histórico narrativo de ciclos. La planificación operativa seleccionable por automations vive en `docs/roadmap_codex.md`.

## Estado actual
- Se endureció el ciclo de vida de jobs UI para evitar cierres abruptos durante ejecución en `QThread`.
- `MainWindow` ahora usa una ruta explícita de cierre controlado cuando detecta jobs activos.
- `JobManager` tiene API pública para inspección/cancelación masiva/cierre seguro y limpieza integral de recursos.

## Ciclo 19

## Objetivo
Cerrar el enlace mínimo doc ↔ smoke transversal para congelar la semántica compartida de bloqueo operativo sin listas hardcodeadas dispersas.

## Cambios aplicados
- Se añadió en `docs/ci_quality_gate.md` un bloque mínimo y estable delimitado por marcadores `GATE_BLOQUEO_OPERATIVO_SEMANTICA:START/END` con los snippets contractuales de bloqueo operativo.
- Se extendió `scripts/quality_gate_components/contrato_reason_codes_doc.py` con helper reutilizable para extraer esos snippets desde el bloque marcado, reutilizando un extractor genérico por marcadores.
- El smoke transversal `tests/test_gate_operational_contract_smoke.py` dejó de hardcodear tokens semánticos y ahora consume la semántica mínima desde el helper documental único.
- Se añadieron tests de parser del bloque semántico en `tests/test_gate_reason_codes_docs_sync.py` para cubrir caso bien formado y fallo claro cuando el bloque falta.

## Tests ejecutados
- `pytest -q tests/test_gate_operational_contract_smoke.py tests/test_gate_reason_codes_docs_sync.py`
- `ruff check docs/ci_quality_gate.md scripts/quality_gate_components/contrato_reason_codes_doc.py tests/test_gate_operational_contract_smoke.py tests/test_gate_reason_codes_docs_sync.py docs/roadmap_codex_automation.md`

## Riesgos abiertos
- El contrato semántico sigue siendo intencionalmente mínimo; no congela wording completo de todos los mensajes operativos.
- Si se cambia intencionalmente la semántica compartida, debe actualizarse el bloque marcado para mantener sincronía con el smoke.

## Siguiente paso recomendado
- Reutilizar el mismo helper documental en cualquier test adicional de contrato operativo para evitar reintroducir listas paralelas.

## Ciclo 18

## Objetivo
Congelar el contrato compartido de bloqueo operativo entre `python -m scripts.gate_pr` y `python -m scripts.gate_rapido` con un smoke test transversal estable.

## Cambios aplicados
- Se añadió el smoke test transversal `tests/test_gate_operational_contract_smoke.py` para ejecutar ambos entrypoints bajo el mismo diagnóstico simulado de bloqueo operativo.
- El smoke valida contrato mínimo compartido sin snapshot frágil: `rc=20`, semántica de bloqueo local, confirmación de “todavía no se validó el proyecto”, y presencia de acción sugerida/reintento.
- Se eliminó una aserción transversal parcial en `tests/test_gate_pr.py` para dejar el contrato centralizado en el smoke test único.

## Tests ejecutados
- `pytest -q tests/test_gate_operational_contract_smoke.py tests/test_gate_pr.py tests/test_gate_rapido.py`
- `ruff check scripts/gate_pr.py scripts/gate_rapido.py scripts/quality_gate_components/bloqueo_operativo.py tests/test_gate_pr.py tests/test_gate_rapido.py tests/test_gate_operational_contract_smoke.py`
- `python -m scripts.gate_pr`

## Riesgos abiertos
- El contrato smoke congela semántica mínima (intención + piezas clave), no equivalencia literal de wording completo entre ambos entrypoints.
- Cambios futuros en mensajes operativos deben preservar tokens semánticos mínimos del smoke para evitar regresión transversal accidental.

## Siguiente paso recomendado
- Añadir una verificación documental mínima que vincule explícitamente el smoke transversal con el contrato de `reason_code` operativo para detectar drift de texto/causa en un solo lugar.

## Ciclo 17

## Objetivo
Cerrar la brecha de contrato operativo entre `python -m scripts.gate_pr` y `python -m scripts.gate_rapido` para bloqueos de doctor/preflight.

## Cambios aplicados
- Se agregó un helper pequeño compartido (`reportar_bloqueo_operativo_doctor`) para normalizar salida/rc de bloqueo operativo del doctor en ambos entrypoints canónicos.
- `gate_pr` reutiliza el helper y conserva `EXIT_ENTORNO_BLOQUEADO=20` con semántica explícita de “todavía no se validó el proyecto”.
- `gate_rapido` ahora ejecuta preflight de doctor antes de delegar al entrypoint report-only; cuando detecta bloqueo operativo retorna también `rc=20` con mensaje equivalente y acción sugerida.
- Se añadieron tests de consistencia para cubrir:
  - bloqueo doctor/preflight en `gate_rapido`,
  - continuidad del flujo normal sin bloqueo,
  - consistencia base de semántica/rc con `gate_pr`.

## Tests ejecutados
- `pytest -q tests/test_gate_rapido.py tests/test_gate_pr.py`
- `ruff check scripts/gate_rapido.py scripts/gate_pr.py scripts/quality_gate_components/bloqueo_operativo.py tests/test_gate_rapido.py tests/test_gate_pr.py`
- `python -m scripts.gate_pr`

## Riesgos abiertos
- El modo `report-only` de `entrypoint` conserva su `returncode` histórico; la normalización a `rc=20` ocurre en los entrypoints canónicos.
- Si aparecen nuevos `reason_code` operativos en doctor, deben seguir documentándose y cubrirse en tests de contrato documental.

## Siguiente paso recomendado
- Añadir un test transversal ligero que ejerza explícitamente ambos entrypoints con el mismo diagnóstico simulado para reforzar la trazabilidad del contrato operativo compartido.

## Ciclo 1

## Objetivo
Construir base estable de shutdown controlado, cleanup seguro de hilos/workers y manejo no fatal de errores de worker para sostener iteraciones posteriores.

## Cambios aplicados
- `JobManager`:
  - Nuevas APIs: `tiene_jobs_activos`, `ids_jobs_activos`, `cancelar_todos`, `solicitar_cierre_seguro`, `resumen_recursos_activos`.
  - Señales nuevas: `cierre_seguro_completado`, `jobs_activos_cambiaron`.
  - Limpieza total de `threads/workers/relays/tokens/states` en `_cleanup`.
  - Guardarraíles para ignorar señales tardías de progreso/finalización sobre jobs ya terminales.
  - Logging estructurado de fallo de worker con `job_id` y `reason_code=worker_exception`.
- `MainWindow`:
  - Intercepta cierre de ventana (`closeEvent`) y evita cierre abrupto con jobs activos.
  - Inicia secuencia de cierre controlado, cancela jobs y completa cierre sólo cuando `JobManager` confirma fin de limpieza.
  - Mantiene estado visual coherente durante shutdown.
- i18n:
  - Claves nuevas para estado de cierre controlado y feedback al usuario.
- Tests:
  - Cobertura de cierre seguro y limpieza en `JobManager`.
  - Cobertura de cierre controlado de `MainWindow` con job activo.

## Tests ejecutados
- `pytest -q tests/test_job_manager.py`
- `pytest -q tests/test_main_window_shutdown.py`
- `python -m scripts.gate_pr`

## Riesgos abiertos
- No se implementó timeout forzado de shutdown: si un worker ignora `CancelToken`, el cierre espera indefinidamente.
- `jobs_activos_cambiaron` aún no se usa en toda la UI (se dejó disponible para próximos ciclos).

## Siguiente paso recomendado
- Añadir política de timeout configurable para cierre seguro y fallback controlado (sin kill abrupto), con trazabilidad explícita por `reason_code`.
- Añadir test de stress con múltiples jobs concurrentes y cierre simultáneo.
- Integrar métricas simples de tiempo de cancelación por job.

## Ciclo 2

## Objetivo
Cerrar el hueco de workers no cooperativos sin forzar kill de hilos: timeout no destructivo, cierre reentrante e idempotente y mejor separación de responsabilidades.

## Cambios aplicados
- Nueva pieza `ControladorCierreApp` para orquestar el lifecycle de cierre:
  - decide cierre inmediato, inicio de shutdown, estado en progreso y timeout;
  - modela reentrancia/idempotencia (reintentos durante shutdown no duplican side effects);
  - agrega trazabilidad estructurada (`shutdown_started`, `shutdown_completed`, `shutdown_timeout`) con `shutdown_id`, duración y jobs bloqueantes.
- `MainWindow` quedó más fina:
  - delega decisiones de `closeEvent` al controlador;
  - mantiene wiring mínimo de UI (bloquear/restaurar controles, feedback toast);
  - incorpora timeout configurable (`shutdown_timeout_ms`) y restaura estado operativo al expirar.
- i18n:
  - nueva clave UX `job.shutdown.timeout` para feedback no destructivo al usuario.
- Tests:
  - nueva suite unitaria determinista para el controlador de cierre sin dependencia de UI;
  - cobertura de timeout no destructivo, no duplicación de timer y reintento de cierre en `MainWindow`.

## Tests ejecutados
- `pytest -q tests/test_job_manager.py`
- `pytest -q tests/test_controlador_cierre_app.py`
- `pytest -q tests/test_main_window_shutdown.py`
- `python -m scripts.gate_pr`

## Problema cerrado en este ciclo
- Si un worker no coopera con `CancelToken`, el cierre ya no queda pendiente indefinidamente: se aborta el intento tras timeout, la app sigue abierta en estado consistente y permite reintento posterior.

## Riesgos abiertos
- Sin kill forzado, un worker permanentemente bloqueado seguirá consumiendo recursos hasta que coopere o finalice por su cuenta.
- Pendiente ampliar métricas agregadas por job para diagnosticar bloqueos recurrentes.

## Siguiente paso recomendado
- Añadir telemetría histórica de tiempos de shutdown por tipo de job y alertas operativas de timeouts repetidos.
- Extender pruebas a escenarios multi-job no cooperativos con mezcla de jobs cooperativos.

## Ciclo 3

## Objetivo
Unificar el entrenamiento de `prediccion_ausencias` con el contrato canónico de jobs premium (`MainWindow.run_premium_job` + `JobManager`) y eliminar el `QThread` local en la página.

## Cambios aplicados
- `PagePrediccionAusencias`:
  - dejó de crear `QThread`/worker local para entrenar;
  - ahora delega el arranque a un coordinador de entrenamiento premium;
  - mantiene callbacks explícitos de éxito/fallo con `refresh` de salud/resultados/previsualización y limpieza de recordatorio.
- Nueva pieza `CoordinadorEntrenamientoPrediccionAusencias`:
  - encapsula el wiring de `run_premium_job`;
  - construye `worker_factory(cancel_token, report_progress)` con progreso i18n (`preflight`, `entrenando`, `refrescando`, `done`);
  - respeta cancelación cooperativa y normaliza fallos a `reason_code`.
- `MainWindow`:
  - `run_premium_job` ahora acepta `on_failed` opcional para notificar a la página y evitar estado atascado tras error.
- i18n UX:
  - nuevas claves de título/progreso para el entrenamiento de predicción de ausencias.
- Guardarraíles/tests:
  - tests unitarios para coordinador/worker premium;
  - tests de handlers de página para no doble arranque, éxito y fallo normalizado;
  - test AST estructural para congelar “sin `QThread` local” en la página.

## Tests ejecutados
- `pytest -q tests/ui/test_prediccion_ausencias_coordinador_entrenamiento.py`
- `pytest -q tests/test_prediccion_ausencias_page_entrenamiento_handlers.py`
- `pytest -q tests/guardrails/test_prediccion_ausencias_page_entrenamiento_job_manager_ast.py`
- `python -m scripts.gate_pr`

## Deuda cerrada en este ciclo
- Entrenamiento de `prediccion_ausencias` fuera del carril de lifecycle común por uso de `QThread` local.

## Riesgos abiertos
- El caso de uso de entrenamiento sigue sin cancelación interna granular; la cancelación es cooperativa en bordes del worker y no interrumpe cómputo interno no cooperativo.
- La página todavía concentra responsabilidades de presentación amplias fuera del flujo de entrenamiento (pendiente para iteraciones futuras pequeñas).

## Siguiente paso recomendado
- Extraer un coordinador adicional para “post-entrenamiento refresh” (salud + resultados + preview) y reducir tamaño de `page.py` sin cambiar comportamiento.
- Añadir telemetría de duración por job `prediccion_ausencias_entrenar` para observar rendimiento y timeouts en cierre.

## Ciclo 4

## Objetivo
Endurecer el contrato ML de `prediccion_ausencias` sin cambiar el algoritmo baseline: evaluación determinista, metadata rica persistida y resumen compacto de calidad en UI.

## Cambios aplicados
- Entrenamiento con split determinista reproducible (orden temporal del dataset) y cálculo de métricas básicas (`accuracy`, `precision_no_show`, `recall_no_show`, `f1_no_show`).
- Persistencia extendida del artefacto de modelo con metadata ML útil:
  - `model_type`, `muestras_train`, `muestras_validacion`,
  - `tasa_no_show_train`, `tasa_no_show_validacion`,
  - métricas de evaluación.
- Compatibilidad hacia atrás para metadata antigua (`fecha_entrenamiento`, `citas_usadas`, `version`) sin romper carga.
- UI de `PagePrediccionAusencias` con bloque compacto de “último entrenamiento”:
  - fecha, tipo de modelo, split train/validación, accuracy, recall no-show y estado de calidad.
- Coordinador puro de calidad UX (`VERDE/AMARILLO/ROJO`) desacoplado de Qt para mantener testeo determinista.
- Logging de entrenamiento exitoso con métricas clave en el evento `prediccion_entrenar_ok`.

## Tests ejecutados
- `pytest -q tests/test_prediccion_ausencias_usecases.py tests/test_prediccion_ausencias_resumen_modelo.py`
- `python -m scripts.gate_rapido`

## Riesgos abiertos
- El umbral UX (`VERDE/AMARILLO/ROJO`) es deliberadamente simple; puede requerir calibración posterior con evidencia operativa real.
- La evaluación usa holdout temporal fijo (20% final); aún no hay comparación multi-split ni tracking histórico de drift para este módulo.

## Siguiente paso recomendado
- Mantener este contrato y, en ciclo posterior, introducir predictor más fuerte detrás de `model_type` sin rehacer UI ni persistencia.
- Añadir vista histórica de entrenamientos (últimas N corridas) y tendencias de métricas para detectar degradación.

## Ciclo 5

## Objetivo
Cerrar la deuda de lectura de estado ML en `prediccion_ausencias` con un contrato explícito de resumen del último entrenamiento, desacoplando la UI de accesos indirectos a metadata.

## Cambios aplicados
- Se endureció `ResumenEntrenamientoModeloDTO` como contrato explícito para presentación con estado de disponibilidad/reason code y metadata ML completa (versionado, split, tasas y métricas principales).
- `ObtenerResumenUltimoEntrenamientoPrediccion` pasó a ser el punto único de lectura para resumen:
  - devuelve estado explícito cuando no existe metadata;
  - mantiene compatibilidad con metadata legacy;
  - registra logging estructurado en degradación por metadata incompleta o legacy.
- `PrediccionAusenciasFacade` ahora expone `obtener_resumen_ultimo_entrenamiento_uc` y la composición lo cablea de forma explícita.
- `PagePrediccionAusencias` dejó de leer metadata por `obtener_salud_uc.lector_metadata` y consume sólo el nuevo contrato del facade.
- Se añadieron pruebas para contrato de resumen (metadata nueva, legacy y ausencia de modelo), wiring del facade y guardarraíl AST de desacople en página.

## Tests ejecutados
- `pytest -q tests/test_prediccion_ausencias_usecases.py tests/test_prediccion_ausencias_resumen_modelo.py tests/test_prediccion_ausencias_page_estabilidad.py tests/test_prediccion_ausencias_facade_wiring.py`
- `python -m scripts.gate_pr`

## Deuda cerrada en este ciclo
- Lectura de resumen ML por ruta indirecta/acoplada desde la página (`obtener_salud_uc.lector_metadata.cargar_metadata`).

## Riesgos abiertos
- El contrato nuevo sigue leyendo “último entrenamiento” únicamente; aún no modela histórico ni comparación temporal.
- `reason_code` queda preparado para UX futura, pero actualmente la vista compacta sigue degradando con placeholders neutrales.

## Siguiente paso recomendado
- Mantener este contrato y avanzar al cambio de predictor detrás de `model_type` sin tocar presentación.
- Introducir histórico de entrenamientos consumiendo este DTO como base de compatibilidad.

## Ciclo 6

## Objetivo
Introducir un predictor v2 dependency-free para `prediccion_ausencias` con comparación reproducible frente a baseline y selección determinista de `model_type` ganador, sin romper el contrato ML/UI de ciclos 4-5.

## Cambios aplicados
- Se incorporó `PredictorAusenciasV2` (probabilístico jerárquico) con suavizado bayesiano ligero y mezcla por soporte entre:
  - tasa global,
  - tasa por paciente,
  - tasa por bucket de antelación.
- Se añadió selector puro de modelo (`seleccion_modelo.py`) con criterio explícito y estable:
  - `f1_no_show` > `recall_no_show` > `accuracy` > baseline en empate total.
- `EntrenarPrediccionAusencias` ahora:
  - entrena baseline y v2 sobre el mismo split determinista existente;
  - evalúa ambos con las métricas ya estandarizadas;
  - selecciona ganador por criterio reproducible;
  - persiste predictor y `model_type` ganador en metadata.
- Se agregó logging estructurado de cierre de entrenamiento con:
  - `model_type_ganador`,
  - métricas baseline,
  - métricas v2,
  - criterio de decisión.
- La UI no requirió rediseño: continúa leyendo `model_type` y resumen del último entrenamiento con el contrato existente.

## Tests ejecutados
- `pytest -q tests/test_prediccion_ausencias_model_selection.py`
- `pytest -q tests/test_prediccion_ausencias_usecases.py tests/test_prediccion_ausencias_resumen_modelo.py tests/test_prediccion_ausencias_facade_wiring.py`
- `python -m scripts.gate_pr`

## Riesgos abiertos
- El predictor v2 está limitado por features disponibles (`paciente_id`, `no_vino`, `dias_antelacion`); sin señales adicionales, la ganancia esperada puede saturar.
- El criterio prioriza recall/f1 de no-show (intencional), lo que puede sesgar ligeramente falsos positivos en cohorts particulares.
- No existe histórico de entrenamientos aún; sólo último snapshot, por decisión de alcance del ciclo.

## Siguiente paso recomendado
- Añadir histórico acotado de entrenamientos (últimas N corridas) reutilizando el contrato de resumen actual.
- Monitorear drift temporal por bucket de antelación y calibrar umbrales de riesgo si aparece degradación operacional.

## Ciclo 7

## Objetivo
Agregar observabilidad temporal liviana al módulo `prediccion_ausencias` manteniendo un único modelo activo (`predictor.pkl`) y sin introducir artefactos pesados históricos.

## Cambios aplicados
- Persistencia extendida en `AlmacenamientoModeloPrediccion` con `history.json` ligero:
  - snapshot por entrenamiento exitoso (metadata + métricas),
  - truncado determinista a `MAX_SNAPSHOTS_HISTORIAL=20`,
  - orden consistente más reciente primero,
  - compatibilidad degradada si `history.json` no existe o está corrupto (con logging estructurado).
- Entrenamiento conserva contrato actual de modelo activo + metadata y añade contexto de selección al snapshot histórico (`ganador_criterio`, `baseline_f1`, `v2_f1` cuando disponible).
- Nuevo caso de uso explícito `ObtenerHistorialEntrenamientosPrediccion` y wiring en facade/composición (`obtener_historial_entrenamientos_uc`).
- `PagePrediccionAusencias` incorpora bloque compacto “Últimos entrenamientos” (fecha, modelo ganador, accuracy, recall no-show, calidad) consumiendo el facade; sin acceso directo a storage.
- Coordinador puro de resumen extiende normalización para filas compactas de historial, manteniendo la lógica fuera de la página.
- i18n actualizado (ES/EN) para nuevo bloque UI.

## Tests ejecutados
- `pytest -q tests/test_prediccion_ausencias_usecases.py tests/test_prediccion_ausencias_facade_wiring.py tests/test_prediccion_ausencias_page_estabilidad.py tests/test_prediccion_ausencias_resumen_modelo.py`
- `python -m scripts.gate_pr`

## Riesgos abiertos
- `history.json` mantiene snapshots compactos (sin dataset ni artefactos binarios), por lo que no cubre análisis profundos de drift por cohorte.
- La calidad UX se deriva de umbrales actuales de `accuracy/recall`; puede requerir recalibración con más evidencia operativa.

## Siguiente paso recomendado
- Añadir una señal de tendencia mínima (delta contra entrenamiento previo) en el mismo bloque compacto, reutilizando `history.json`.
- Evaluar alertas de degradación cuando se acumulen N snapshots consecutivos con calidad `ROJO`.

## Ciclo 8

## Objetivo
Cerrar el valor operativo del histórico ligero (`history.json`) con tendencia mínima y alerta simple de degradación, saneando además i18n en el área tocada.

## Cambios aplicados
- Se añadió cálculo puro y determinista de tendencia en `application/prediccion_ausencias/tendencia_entrenamientos.py`:
  - comparación último vs anterior para `accuracy` y `recall_no_show`,
  - etiquetas `MEJORA | EMPEORA | ESTABLE | NO_DISPONIBLE`,
  - tolerancia explícita `0.005` para evitar ruido.
- Se incorporó alerta operativa simple por histórico:
  - activa cuando hay `3` corridas consecutivas en `ROJO`,
  - inactiva en cualquier otro patrón.
- El coordinador de resumen de página ahora traduce ese estado a contrato UI i18n (`derivar_estado_tendencia_historial`) sin mover lógica a la página.
- `PagePrediccionAusencias` muestra en modo compacto:
  - “Tendencia reciente” (accuracy + recall),
  - “Alerta operativa” (activa/inactiva).
- Se saneó `clinicdesk/app/i18n_catalogos/pred.py` en el alcance afectado:
  - eliminación de bloque duplicado de claves `demo_ml.playbook.*` que dejaba `ruff` en rojo,
  - alta de claves ES/EN para tendencia/alerta del historial.

## Tests ejecutados
- `pytest -q tests/test_tendencia_entrenamientos.py tests/test_prediccion_ausencias_resumen_modelo.py tests/test_prediccion_ausencias_page_estabilidad.py`
- `ruff check clinicdesk/app/application/prediccion_ausencias/dtos.py clinicdesk/app/application/prediccion_ausencias/tendencia_entrenamientos.py clinicdesk/app/pages/prediccion_ausencias/coordinador_resumen_modelo.py clinicdesk/app/pages/prediccion_ausencias/page.py clinicdesk/app/i18n_catalogos/pred.py tests/test_tendencia_entrenamientos.py tests/test_prediccion_ausencias_resumen_modelo.py`
- `python -m scripts.gate_pr`

## Riesgos abiertos
- La tendencia usa sólo las dos últimas corridas; no detecta estacionalidad ni cambios por cohorte (decisión intencional de alcance).
- La alerta por `3` rojos consecutivos es deliberadamente simple y puede requerir ajuste futuro con evidencia real de operación.

## Siguiente paso recomendado
- Añadir una recomendación operativa contextual (acción sugerida) cuando la alerta esté activa, manteniendo el mismo contrato compacto.
- Evaluar si conviene registrar también delta numérico (además de etiqueta) en telemetry interna, sin añadir complejidad visual.

## Ciclo 9

## Objetivo
Cerrar el bucle entre observabilidad ML y acción sugerida en `prediccion_ausencias` con una recomendación operativa compacta y telemetría mínima de estado de monitor.

## Cambios aplicados
- Se añadió una regla pura y testeable de recomendación operativa en `tendencia_entrenamientos.py` con prioridad explícita:
  - alerta activa (`3` rojos consecutivos) ⇒ recomendación fuerte (`ACCION_REVISAR_DATOS` o `ACCION_REENTRENAR`),
  - sin alerta + tendencia en empeoramiento ⇒ recomendación suave (`ACCION_MONITORIZAR`),
  - estable/mejora/no disponible ⇒ `SIN_ACCION`.
- Se extendió el coordinador de resumen para derivar `EstadoMonitorMlDTO` (estado_tendencia, alerta_activa, calidad_ultimo_entrenamiento, recomendacion_operativa).
- `PagePrediccionAusencias` incorporó un único bloque compacto de “Recomendación operativa” y delega toda la lógica de decisión al coordinador/helper puro (sin lógica en la página).
- Se añadió telemetría ligera del monitor ML con evento `prediccion_monitor_ml_estado`, registrando:
  - `estado_tendencia`,
  - `alerta_activa`,
  - `calidad_ultimo_entrenamiento`,
  - `recomendacion_operativa`.
- i18n actualizado con claves ES/EN para el bloque y los textos de recomendación operativa.

## Tests ejecutados
- `pytest -q tests/test_tendencia_entrenamientos.py tests/test_prediccion_ausencias_resumen_modelo.py tests/test_prediccion_ausencias_page_estabilidad.py`
- `ruff check clinicdesk/app/application/prediccion_ausencias/dtos.py clinicdesk/app/application/prediccion_ausencias/tendencia_entrenamientos.py clinicdesk/app/pages/prediccion_ausencias/coordinador_resumen_modelo.py clinicdesk/app/pages/prediccion_ausencias/page.py clinicdesk/app/i18n_catalogos/pred.py tests/test_tendencia_entrenamientos.py tests/test_prediccion_ausencias_resumen_modelo.py tests/test_prediccion_ausencias_page_estabilidad.py`
- `python -m scripts.gate_pr`

## Riesgos abiertos
- La recomendación operativa sigue una regla pequeña intencional; puede necesitar ajuste fino de umbrales con evidencia real.
- La telemetría se registra al refrescar el bloque de resumen, por lo que puede generar eventos repetidos si la vista se recarga frecuentemente.

## Siguiente paso recomendado
- Añadir agregación mínima de eventos del monitor (por sesión o por ventana temporal) para reducir ruido y observar cambios de estado.
- Mantener la recomendación compacta y, si se requiere, incorporar en ciclo futuro una razón corta i18n (“por qué”) sin ampliar UI.

## Ciclo 10

## Objetivo
Rematar el monitor ML compacto eliminando ruido de telemetría en recargas frecuentes y haciendo la recomendación operativa más explicable con una razón corta i18n.

## Cambios aplicados
- Se introdujo deduplicación ligera por sesión para `prediccion_monitor_ml_estado`:
  - fingerprint estable del estado relevante (`estado_tendencia`, `alerta_activa`, `calidad_ultimo_entrenamiento`, `recomendacion_operativa`, `razon_corta`);
  - emisión de telemetría sólo cuando ese fingerprint cambia;
  - sin persistencia adicional y sin distribuir estado por múltiples componentes UI.
- Se extendió la recomendación operativa con `razon_corta_i18n_key` en el contrato de aplicación.
- La lógica de “razón corta” quedó en capa de aplicación/coordinador (no en la página), con casos compactos:
  - alerta fuerte: `3 corridas seguidas en rojo`,
  - empeora sin alerta: `la tendencia empeora`,
  - sin acción con señal estable: `sin señales preocupantes`,
  - sin historial suficiente: `no hay datos suficientes`.
- `PagePrediccionAusencias` mantiene layout compacto y sólo renderiza:
  - sigue mostrando recomendación principal;
  - añade una única línea corta de razón i18n sin crear paneles nuevos.
- i18n actualizado en ES/EN para etiqueta y motivos cortos del monitor.

## Tests ejecutados
- `pytest -q tests/test_tendencia_entrenamientos.py tests/test_prediccion_ausencias_resumen_modelo.py tests/test_prediccion_ausencias_page_estabilidad.py`
- `ruff check clinicdesk/app/application/prediccion_ausencias/dtos.py clinicdesk/app/application/prediccion_ausencias/tendencia_entrenamientos.py clinicdesk/app/pages/prediccion_ausencias/coordinador_resumen_modelo.py clinicdesk/app/pages/prediccion_ausencias/page.py clinicdesk/app/i18n_catalogos/pred.py tests/test_tendencia_entrenamientos.py tests/test_prediccion_ausencias_resumen_modelo.py tests/test_prediccion_ausencias_page_estabilidad.py`
- `python -m scripts.gate_pr`

## Riesgos abiertos
- La deduplicación es por sesión de página; al recrear la vista, el primer estado vuelve a emitirse (comportamiento esperado por simplicidad de alcance).
- El fingerprint usa claves compactas i18n y estado operativo; si en futuro cambia la semántica de recomendación podría requerir ajuste de granularidad.

## Siguiente paso recomendado
- Medir volumen real de eventos tras dedupe para confirmar reducción de ruido en operación.
- Mantener la razón corta compacta y evaluar sólo ajustes de wording i18n con feedback de uso real, sin ampliar superficie visual.

## Ciclo 11

## Objetivo
Hacer explícito y trazable el bloqueo operativo del gate canónico para reducir tiempo perdido en entornos con `.venv` roto, toolchain incompleto o dependencia de red/proxy.

## Cambios aplicados
- `scripts.gate_pr` ahora emite un bloque de diagnóstico estable cuando aborta por entorno:
  - `reason_code` y `categoria` de bloqueo operativo,
  - detalle legible y `accion_sugerida`,
  - lista explícita de validaciones que **no** se ejecutaron (para evitar falsos negativos funcionales).
- Se introdujo una clasificación pequeña y estable en el doctor (`clasificar_bloqueo_entorno`) para distinguir:
  - lock/toolchain inválido,
  - dependencias faltantes,
  - versiones desalineadas,
  - wheelhouse requerido no disponible,
  - dependencia de red/proxy sin wheelhouse.
- El bloqueo canónico por `.venv` ausente/no utilizable ahora incluye `reason_code` explícito (`VENV_REPO_NO_DISPONIBLE`) en la salida.
- Se reforzó cobertura de tests en gate/doctor/ejecución canónica para validar no solo `rc` sino también clasificación y mensaje.

## Tests ejecutados
- `pytest -q tests/test_gate_pr.py tests/test_doctor_entorno_calidad.py tests/test_ejecucion_canonica.py`
- `ruff check scripts/gate_pr.py scripts/quality_gate_components/doctor_entorno_calidad_core.py scripts/quality_gate_components/ejecucion_canonica.py tests/test_gate_pr.py tests/test_doctor_entorno_calidad.py tests/test_ejecucion_canonica.py`
- `python -m scripts.gate_pr` (reintento local para verificar contrato de bloqueo operativo según entorno actual)

## Riesgos abiertos
- La clasificación de red/proxy es diagnóstica (dependencia de red) y no confirma por sí sola un `403` remoto específico; se mantiene intencionalmente sin heurísticas intrusivas.
- El contrato nuevo mejora trazabilidad local, pero no reemplaza observabilidad de CI remota cuando hay diferencias de infraestructura.

## Siguiente paso recomendado
- Añadir un mini “glosario de reason_code” en docs del gate para mapear cada código a acciones de remediación rápidas por perfil (dev local vs sandbox CI).
- Consolidar en un smoke test adicional el texto de “validaciones no ejecutadas” para preservar el contrato ante futuros refactors de scripts.

## Ciclo 12

## Objetivo
Congelar mejor el contrato operativo del gate con un glosario breve y smoke tests de trazabilidad que detecten regresiones sin depender de snapshots frágiles.

## Cambios aplicados
- Se añadió un glosario corto y accionable de `reason_code` operativo en `docs/ci_quality_gate.md`, con mapeo directo `código -> significado -> acción sugerida`.
- Se estabilizó el listado de validaciones omitidas del preflight en `scripts.gate_pr` mediante constante explícita (`VALIDACIONES_NO_EJECUTADAS`) para evitar drift accidental de contrato.
- El bloqueo canónico por `.venv` no disponible ahora explicita que el proyecto todavía **no** se validó funcionalmente, reforzando la separación entre bloqueo operativo y fallo funcional.
- Se añadieron smoke tests de contrato textual mínimo:
  - preflight de `gate_pr` valida presencia de `rc=20`, `reason_code`, acción sugerida y bloque de validaciones no ejecutadas;
  - ejecución canónica valida la pieza de “no validado funcionalmente” en el bloqueo por entorno.

## Tests ejecutados
- `pytest -q tests/test_gate_pr.py tests/test_ejecucion_canonica.py`
- `ruff check scripts/gate_pr.py scripts/quality_gate_components/ejecucion_canonica.py tests/test_gate_pr.py tests/test_ejecucion_canonica.py`
- `python -m scripts.gate_pr` (esperable `rc=20` en entorno bloqueado; se verifica contrato operativo, no validación funcional completa)

## Riesgos abiertos
- El glosario es intencionalmente corto y cubre los códigos operativos actuales; si se agregan nuevos `reason_code`, hay que actualizar esta tabla para mantener trazabilidad.
- El smoke test textual protege estructura mínima, pero no valida semántica profunda del diagnóstico del doctor (se mantiene como alcance deliberadamente acotado).

## Siguiente paso recomendado
- Añadir una verificación ligera que falle si aparece un `reason_code` operativo nuevo sin entrada correspondiente en el glosario.
- Mantener el contrato textual mínimo y evitar crecerlo con snapshots completos para no introducir fragilidad de wording.

## Ciclo 13

## Objetivo
Cerrar fuga de mantenimiento del contrato operativo del gate para evitar desincronización entre `reason_code` reales y glosario documental.

## Cambios aplicados
- Se definió una fuente explícita y estable de `reason_code` operativos documentables:
  - `REASON_CODES_OPERATIVOS_DOCTOR` en `doctor_entorno_calidad_core.py`.
  - `REASON_CODES_OPERATIVOS_CANONICO` en `ejecucion_canonica.py`.
  - `reason_codes_operativos_documentables()` en `scripts/gate_pr.py` como agregador canónico para documentación/chequeos.
- Se agregó verificación de coherencia código↔docs en `tests/test_gate_reason_codes_docs_sync.py`:
  - falla si aparece un `reason_code` operativo nuevo no documentado,
  - falla si el glosario contiene códigos inexistentes.
- Se mantuvo breve la documentación en `docs/ci_quality_gate.md`, referenciando la fuente de verdad en código sin ampliar el glosario.

## Tests ejecutados
- `pytest -q tests/test_doctor_entorno_calidad.py tests/test_ejecucion_canonica.py tests/test_gate_pr.py tests/test_gate_reason_codes_docs_sync.py`
- `ruff check scripts/gate_pr.py scripts/quality_gate_components/doctor_entorno_calidad_core.py scripts/quality_gate_components/ejecucion_canonica.py tests/test_doctor_entorno_calidad.py tests/test_ejecucion_canonica.py tests/test_gate_reason_codes_docs_sync.py`

## Riesgos abiertos
- La sincronización depende de mantener el encabezado del glosario en `docs/ci_quality_gate.md`; si cambia, el test debe ajustar el selector de sección.
- El alcance está acotado al contrato operativo gate/doctor/canónico (intencional); otros `reason_code` fuera de ese contrato no entran en este chequeo.

## Siguiente paso recomendado
- Exponer un check dedicado dentro del flujo de gate documental (si se decide), reutilizando la misma función canónica para no duplicar fuentes.

## Ciclo 14

## Objetivo
Endurecer el contrato de coherencia doc↔código de `reason_code` operativos del gate, eliminando dependencia de títulos frágiles y encapsulando verificación reutilizable.

## Cambios aplicados
- Se introdujo un anclaje documental estable en `docs/ci_quality_gate.md` con marcadores explícitos:
  - `<!-- GATE_REASON_CODES_GLOSARIO:START -->`
  - `<!-- GATE_REASON_CODES_GLOSARIO:END -->`
- Se agregó helper reutilizable `scripts/quality_gate_components/contrato_reason_codes_doc.py` para:
  - extraer `reason_code` documentados desde bloque delimitado,
  - comparar contra códigos canónicos,
  - fallar con error claro ante delimitación ausente/rota o divergencia doc↔código.
- `scripts.gate_pr` expone `reason_codes_operativos_documentados_en_docs(ruta_doc)` para reutilización limpia por tests y futuras verificaciones documentales, manteniendo única fuente canónica en `reason_codes_operativos_documentables()`.
- Se reforzó la suite de contrato en `tests/test_gate_reason_codes_docs_sync.py` con cobertura de:
  - sincronización nominal,
  - independencia de wording del título,
  - fallo por glosario sin marcadores,
  - diffs explícitos de faltantes/sobrantes.

## Tests ejecutados
- `pytest -q tests/test_gate_reason_codes_docs_sync.py`
- `pytest -q tests/test_gate_pr.py tests/test_doctor_entorno_calidad.py tests/test_ejecucion_canonica.py`
- `ruff check scripts/gate_pr.py scripts/quality_gate_components/contrato_reason_codes_doc.py tests/test_gate_reason_codes_docs_sync.py`

## Riesgos abiertos
- El parser asume formato de tabla markdown para filas (`| \`CODE\` | ... | ... |`); si cambia ese formato, habrá que ajustar el helper (intencional para mantenerlo pequeño y explícito).
- La validación sigue en capa de tests; si se requiere enforcement en ejecución de gate documental, se puede reutilizar el helper sin duplicar lógica.

## Siguiente paso recomendado
- Reusar `validar_coherencia_reason_codes_doc(...)` en un check documental liviano del flujo canónico cuando se priorice enforcement fuera de tests.

## Ciclo 15

## Objetivo
Integrar la validación doc↔`reason_code` como check documental liviano dentro del flujo canónico de calidad, reutilizando la lógica existente sin duplicaciones.

## Cambios aplicados
- `scripts.gate_pr` ahora expone `validar_contrato_reason_codes_doc(...)` como punto reutilizable de ejecución explícita del contrato documental.
- El quality gate canónico (`scripts/quality_gate_components/entrypoint.py`) ejecuta ese check en la etapa documental antes de seguridad/changelog.
- La salida de error del check documental se normaliza con contexto de ruta y motivo (`sin documentar`, `sin fuente canonica`, delimitadores ausentes/rotos).
- Se añadieron tests de integración liviana del nuevo enganche documental y test directo del check reutilizable.
- Se actualizó `docs/ci_quality_gate.md` para documentar el nuevo punto de entrada reutilizable del check.

## Tests ejecutados
- `pytest -q tests/test_gate_reason_codes_docs_sync.py tests/test_quality_gate_reason_codes_doc_check.py`
- `ruff check scripts/gate_pr.py scripts/quality_gate_components/entrypoint.py tests/test_gate_reason_codes_docs_sync.py tests/test_quality_gate_reason_codes_doc_check.py`

## Riesgos abiertos
- El contrato sigue acotado al glosario delimitado por marcadores; si el formato de tabla cambia intencionalmente, hay que ajustar el parser del helper.
- El check documental se ejecuta dentro del gate completo; si se quiere enforcement también en gate rápido, se puede reutilizar la misma función sin abrir una segunda implementación.

## Siguiente paso recomendado
- Reusar el mismo check en `gate_rapido` solo si se prioriza detección más temprana, manteniendo `gate_pr.validar_contrato_reason_codes_doc(...)` como única lógica invocable.

## Ciclo 16

## Objetivo
Alinear el contrato operativo de bloqueo por entorno entre `python -m scripts.gate_pr` y `python -m scripts.gate_rapido`, manteniendo cambio mínimo y trazabilidad clara sin alterar el flujo funcional del gate.

## Cambios aplicados
- Se consolidó el `rc` operativo estable de bloqueo en la capa canónica compartida (`scripts.quality_gate_components.ejecucion_canonica.EXIT_ENTORNO_BLOQUEADO = 20`) y `gate_pr` pasó a reutilizar esa constante.
- `scripts.gate_rapido` ahora devuelve `rc=20` cuando `resolver_ejecucion_canonica(...)` decide `bloquear`, en lugar de `1` genérico.
- En el bloqueo canónico de `gate_rapido` se añadió salida trazable mínima para evitar confusión con fallo funcional:
  - identifica bloqueo operativo local;
  - explicita que no equivale a fallo funcional del repositorio;
  - sugiere reparar `.venv/toolchain` y reintentar el comando canónico.
- Se agregó prueba específica de contrato para `gate_rapido` bloqueado por canónico (`rc`, semántica de mensaje y acción sugerida).
- Se actualizó documentación corta del gate para indicar que `rc=20` tiene la misma semántica en gate completo y gate rápido.

## Tests ejecutados
- `pytest -q tests/test_gate_rapido.py`
- `pytest -q tests/test_gate_pr.py tests/test_ejecucion_canonica.py`
- `ruff check scripts/gate_rapido.py scripts/gate_pr.py scripts/quality_gate_components/ejecucion_canonica.py tests/test_gate_rapido.py`

## Riesgos abiertos
- La coherencia de `rc=20` queda alineada para bloqueo canónico, pero futuros tipos de bloqueo operativo nuevos deben seguir reutilizando la misma constante compartida para evitar drift.
- El mensaje de `gate_rapido` se mantiene deliberadamente breve; si se amplía en ciclos futuros conviene conservar smoke tests de semántica mínima (no wording exacto).

## Siguiente paso recomendado
- Añadir un smoke test transversal de consistencia `gate_pr`/`gate_rapido` sobre `rc` operativo compartido para prevenir regresiones al tocar entrypoints canónicos.
