# UX states (loading / empty / error)

Para listas y tablas en PySide6 usamos `EstadoPantallaWidget`.

## Patrón

1. Crear el contenido real (tabla, barra, paginación).
2. Inyectarlo con `set_content(widget)`.
3. En cada carga:
   - `set_loading("...")` al iniciar.
   - `set_empty("...", cta_text_key="...", on_cta=...)` si no hay datos.
   - `set_error("...", detalle_tecnico=..., on_retry=...)` si falla.
   - `set_content(widget)` al completar correctamente.

## i18n

Todos los textos de estado deben vivir en catálogo i18n (`ux_states.*`).

## Concurrencia

Para evitar congelar UI, la carga de listas debe ejecutarse en un worker (`QThread` + `QObject`) y emitir:

- `finished_ok`
- `finished_error`
- `finished`

El hilo de UI solo renderiza el resultado final.
