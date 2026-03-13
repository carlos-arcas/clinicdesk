# UX states (loading / empty / error / ready / processing)

Para listas y tablas en PySide6 usamos un contrato reusable compuesto por:

- `EstadoPantallaWidget` (render de placeholders y contenido).
- `ConfigEstadoListado` + `aplicar_estado_listado` (`clinicdesk.app.ui.ux.estados_listado`).

## Contrato operativo

1. Crear el contenido real (tabla, barra, paginación).
2. Inyectarlo con `set_content(widget)`.
3. En cada carga/operación:
   - `set_loading("...")` al iniciar carga de datos.
   - `set_processing("...")` en operaciones de guardado/proceso prolongado.
   - `set_empty("...", cta_text_key="...", on_cta=...)` sin resultados.
   - `set_error("...", detalle_tecnico=..., on_retry=...)` en error recuperable.
   - `set_ready(widget)`/`set_content(widget)` al completar OK.

## Cuándo usar toast / modal / placeholder

- **Toast**: feedback breve y no bloqueante (éxito, aviso corto).
- **Modal**: confirmación fuerte o detalle puntual que requiere decisión.
- **Placeholder embebido**: estados persistentes de la pantalla (vacío/error/cargando).

## Accesibilidad operativa básica

- Definir tab-order explícito en pantallas críticas.
- En estado `empty` y `error`, mover foco al CTA principal (`Actualizar`/`Reintentar`).
- En `on_show`, enfocar primer control operativo (búsqueda/filtro).
- Tras carga exitosa con filas, devolver foco a la tabla para navegación por teclado.

## i18n

Todo texto visible de estados y acciones debe vivir en catálogo i18n (`ux_states.*`, `pacientes.accion.*`, etc.).

## Concurrencia

Para evitar congelar UI, la carga de listas debe ejecutarse en worker (`QThread` + `QObject`) y emitir:

- `finished_ok`
- `finished_error`
- `finished`

El hilo de UI solo orquesta estado y render final.
