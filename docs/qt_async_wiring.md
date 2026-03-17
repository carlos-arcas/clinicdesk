# Patrón seguro de concurrencia Qt en ClinicDesk

Este repo usa un patrón homogéneo para evitar resultados tardíos, race conditions y mutaciones de UI fuera de contexto.

## Reglas base

- **Worker en `QThread` + `QObject`** para trabajo pesado.
- **Relay/dispatcher explícito** para publicar resultados al hilo GUI.
- **Sin `connect(lambda ...)` en rutas async críticas** (usar slots/métodos nombrados).
- **Token (`token`/`run_id`/`operation_id`)** para descartar resultados obsoletos.
- **Guardas de contexto** antes de renderizar:
  - página visible,
  - widget activo/no destruido,
  - token vigente.
- **Cleanup explícito** de `thread/worker/relay` al terminar.

## Cuándo exigir token

Exigir token cuando haya asincronía o diferidos que puedan solaparse:

- búsquedas rápidas/debounce,
- refrescos diferidos con `QTimer.singleShot`,
- jobs en background que devuelven datos a UI,
- navegación entre páginas/tabs durante una operación pendiente.

## Lifecycle y navegación

- `on_show` debe activar contexto y renovar token vigente.
- `on_hide` debe invalidar contexto para que callbacks tardíos no toquen UI.
- Los callbacks diferidos deben pasar por una función de guarda (`_es_*_vigente`).

## Timers

- Evitar `singleShot(..., lambda que muta UI)` en rutas sensibles.
- Preferir callback nombrado con guardas explícitas.
- Si se referencia un widget, validar vigencia (`QPointer`) antes de mutarlo.
