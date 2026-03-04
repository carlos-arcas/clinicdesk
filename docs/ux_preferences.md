# Preferencias UX persistidas

ClinicDesk persiste preferencias de experiencia de usuario en `data/user_prefs.json` por perfil.

## Campos persistidos

- `pagina_ultima`: última página activa en la barra lateral.
- `filtros_pacientes`:
  - `activo`: estado del filtro (activos/inactivos/todos).
  - `texto`: texto de filtro solo si no parece PII.
- `filtros_confirmaciones`:
  - `rango`, `riesgo`, `recordatorio`.
  - `texto`: texto de búsqueda solo si no parece PII.
- `last_search_by_context`:
  - última búsqueda de `Ctrl+K` por contexto (`pacientes`, `confirmaciones`).
  - si el texto parece PII se guarda como `"[REDACTED]"`.
- `columnas_por_contexto`: reservado para ancho/orden de columnas por listado.

## Campos NO persistidos (privacidad)

No se persisten valores sensibles completos como:

- DNI/documento completo.
- Email completo.
- Teléfono completo.
- Datos clínicos o de contacto específicos del paciente.

El saneamiento se hace con `sanitize_search_text` para evitar persistir búsquedas con PII.
