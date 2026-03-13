# UX Notifications y progreso global

## Objetivo

Centralizar el feedback de operaciones largas en la `MainWindow` para que cualquier página pueda:

- informar estado de carga (`set_busy`),
- disparar notificaciones toast (`toast_success`, `toast_info`, `toast_error`),
- mantener un contrato reutilizable con acciones y detalles,
- usar diálogo modal solo cuando el usuario solicite más contexto (`Ver detalles`).

## Contrato de feedback toast

API pública en `MainWindow` (re-exportada vía `window_feedback`):

- `toast_success(key: str, **kwargs) -> None`
- `toast_info(key: str, **kwargs) -> None`
- `toast_error(key: str, **kwargs) -> None`

`kwargs` soportados:

- `titulo_key`: clave i18n opcional para encabezado.
- `detalle`: detalle técnico opcional (se muestra en modal al pulsar **Ver detalles**).
- `accion_label_key`: clave i18n para botón de acción.
- `accion_callback`: callback de acción (se ejecuta una sola vez).
- `persistente`: evita auto-cierre (útil para errores recuperables).
- `duracion_ms`: override por toast.
- `on_close`: callback al cerrar (manual o automático).

## Cuándo usar toast vs diálogo modal

- **Toast**: feedback breve, no bloqueante, estado operativo normal.
- **Toast + Ver detalles**: errores técnicos recuperables donde UX debe ser clara sin exponer detalle crudo en la barra.
- **Diálogo modal directo**: decisiones de alto impacto (confirmaciones destructivas) o lectura obligatoria.

## ToastManager reutilizable

Archivo: `clinicdesk/app/ui/widgets/toast_manager.py`

- Cola FIFO de toasts.
- Auto-hide configurable (`duracion_ms`, default 2500 ms).
- Cierre manual con `close_current()`.
- Acción de toast con protección anti-duplicación (`run_current_action()`).
- Soporte de detalle técnico y estado persistente.

## Integración en flujos reales

### Pacientes / Confirmaciones

- Al refrescar: busy ON (`busy.loading_*`).
- Al terminar OK: toast de éxito.
- Al fallar: toast persistente recuperable con acción `Reintentar` y `Ver detalles`.

## Guardarraíles

- No incluir PII en logs ni en notificaciones.
- No usar SQL en UI.
- Reutilizar workers para evitar bloquear el hilo principal.
- Todo texto visible debe salir de i18n.
