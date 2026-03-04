# Preferencias UX persistidas

ClinicDesk persiste preferencias de UX por perfil en JSON local para restaurar estado útil de trabajo entre sesiones.

## Qué se guarda y por qué

Archivo por defecto: `data/user_prefs.json`.

Campos persistidos:

- `pagina_ultima`: última pantalla activa para restaurar navegación al arrancar.
- `filtros_pacientes`: filtros funcionales del listado de pacientes (estado y texto no sensible).
- `filtros_confirmaciones`: filtros del listado de confirmaciones (`rango`, `riesgo`, `recordatorio`, texto no sensible).
- `last_search_by_context`: última búsqueda de `Ctrl+K` por contexto (`pacientes`, `confirmaciones`) ya saneada.
- `columnas_por_contexto`: mapa opcional para ancho/orden de columnas por contexto.

## Qué NO se guarda (privacidad)

No se persisten datos que parezcan PII:

- email completo,
- DNI/documento,
- teléfono,
- direcciones completas.

Tampoco se persisten entradas abusivas (> 120 caracteres).

## Política de saneamiento aplicada

Se aplica `sanitize_search_text(text)` con política **bloquear persistencia de PII**:

- si detecta PII o input excesivo: devuelve `None` y no se guarda nada;
- si el texto es normal: se guarda normalizado (`strip` + colapso de espacios).

Ejemplos:

- `" ana   pérez  "` → `"ana pérez"` (se persiste).
- `"test@example.com"` → `None` (se omite).
- `"+34 666 777 888"` → `None` (se omite).
- `"Calle Mayor 12"` → `None` (se omite).

## Variable de entorno

Se puede sobrescribir la ruta de persistencia con:

- `CLINICDESK_PREFS_PATH=/ruta/relativa/o/absoluta/prefs.json`

Si no existe el archivo/directorio, el repositorio devuelve defaults y crea la ruta al guardar.
