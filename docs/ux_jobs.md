# UX Jobs premium (status bar)

## Objetivo
Centralizar trabajos largos en un `JobManager` para mostrar progreso real, permitir cancelación y notificar resultado por toast.

## Patrón
1. UI dispara `run_premium_job(...)` en `MainWindow`.
2. `JobManager` ejecuta el worker en `QThread`.
3. Worker publica progreso `report_progress(percent, message_key)`.
4. `MainWindow` renderiza status bar con formato i18n.
5. Estado final:
   - `finished` -> toast success.
   - `failed` -> toast error.
   - `cancelled` -> toast info.

## Contrato del worker
```python
 def worker(cancel_token, report_progress):
     report_progress(10, "job.algo.preflight")
     if cancel_token.is_cancelled:
         raise JobCancelledError()
```

## Reglas
- Sin SQL en UI: delegar en usecases/facade.
- Sin bloqueo: todo trabajo pesado en `QThread`.
- Sin PII en mensajes de progreso ni toasts.
