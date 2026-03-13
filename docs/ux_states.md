# UX states (loading / processing / empty / error / ready)

Para listados operativos en PySide6 usamos `EstadoPantallaWidget` + `EstadoListadoPresenter`.

## Contrato reusable

Estados soportados en ViewModel (`EstadoPantalla`):

- `LOADING`: carga inicial o recarga por filtros.
- `PROCESSING`: operación en curso sobre datos (ej. preparar recordatorio).
- `EMPTY`: carga correcta sin resultados.
- `ERROR`: error recuperable con opción de reintento.
- `CONTENT`: vista lista con datos.

## Patrón de implementación

1. Definir el `EstadoPantallaWidget` en el `ui_builder` y registrar `set_content(widget_real)`.
2. Usar `EstadoListadoPresenter` en `render_*` de la página.
3. En cada transición:
   - `set_loading("...")` al iniciar carga.
   - `set_processing("...")` al ejecutar acción de guardado/proceso.
   - `set_empty("...", cta_text_key="...", on_cta=...)` si no hay resultados.
   - `set_error("...", on_retry=...)` para error recuperable.
   - `set_content(widget)` al volver a estado listo.

## Toast vs modal vs placeholder

- **Toast**: feedback breve no bloqueante (éxito rápido, aviso de recarga).
- **Modal**: confirmación fuerte o resultado que requiere cierre explícito.
- **Placeholder embebido**: estados persistentes de pantalla (vacío/error/cargando/procesando).

Regla: no usar toast para errores persistentes que necesitan contexto dentro de la página.

## Accesibilidad operativa mínima

- Definir tab order explícito en `ui_builder` para filtros → acciones → tabla → paginación.
- Asignar `accessibleName` en controles principales de cada pantalla crítica.
- Al mostrar estado `empty/error`, mover foco al CTA/reintento cuando exista.
- Al cerrar modal de acción rápida, devolver foco a la tabla/listado origen.

## i18n

Todo texto de estados usa claves de catálogo (`ux_states.*`) y evita hardcodes visibles.
