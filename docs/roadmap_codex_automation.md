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
