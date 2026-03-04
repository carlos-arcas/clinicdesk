# UX Notifications y progreso global

## Objetivo

Centralizar el feedback de operaciones largas en la `MainWindow` para que cualquier página pueda:

- informar estado de carga (`set_busy`),
- disparar notificaciones toast (`toast_success`, `toast_info`, `toast_error`),
- mantener el comportamiento no bloqueante con workers asíncronos.

## API pública de `MainWindow`

- `set_busy(busy: bool, mensaje_key: str) -> None`
  - `busy=True`: muestra indicador indeterminado en status bar con texto i18n.
  - `busy=False`: restaura estado listo.
- `toast_success(key: str) -> None`
- `toast_info(key: str) -> None`
- `toast_error(key: str) -> None`

> Todas las claves de texto deben existir en i18n (ES/EN).

## ToastManager reutilizable

Archivo: `clinicdesk/app/ui/widgets/toast_manager.py`

- Cola FIFO de toasts.
- Auto-hide configurable (`duracion_ms`, default 2500 ms).
- Cierre manual con `close_current()`.
- Suscripción por callback para desacoplar lógica de render.

## Integración en flujos reales

### Pacientes

- Al refrescar: busy ON con `busy.loading_pacientes`.
- Al terminar OK: `toast.refresh_ok_pacientes`.
- Al fallar: `toast.refresh_fail`.

### Confirmaciones

- Al refrescar: busy ON con `busy.loading_confirmaciones`.
- Al terminar OK: `toast.refresh_ok_confirmaciones`.
- Si lista vacía: `toast.refresh_empty_confirmaciones` (info).
- Al fallar: `toast.refresh_fail`.

## Guardarraíles

- No incluir PII en logs ni en notificaciones.
- No usar SQL en UI.
- Reutilizar workers para evitar bloquear el hilo principal.
