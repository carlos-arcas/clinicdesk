# Roadmap Codex Automation

## Estado actual
- Se endureció el ciclo de vida de jobs UI para evitar cierres abruptos durante ejecución en `QThread`.
- `MainWindow` ahora usa una ruta explícita de cierre controlado cuando detecta jobs activos.
- `JobManager` tiene API pública para inspección/cancelación masiva/cierre seguro y limpieza integral de recursos.

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
