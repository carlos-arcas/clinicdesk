# Refactor Pacientes + nueva Home operativa

## Pacientes: causa raíz y solución

Se detectó fragilidad en la carga asíncrona de pacientes: cuando entraban refrescos consecutivos con un worker en curso, la página descartaba el segundo refresh (`return` temprano) y se quedaba mostrando estado `loading` hasta que llegaba un resultado no siempre alineado con el último contexto de filtros/selección.

### Cambios aplicados

- Se añadió un coordinador de carga (`CoordinadorCargaPacientes`) con contrato explícito de:
  - carga en curso,
  - última solicitud pendiente,
  - promoción automática al finalizar el worker activo.
- La página ahora:
  - programa el último refresh pendiente sin depender de timing,
  - procesa resultados solo para token activo,
  - encadena la siguiente carga pendiente al finalizar el thread.
- Se reforzó telemetría estructurada de carga con eventos:
  - `pacientes_carga_inicio`,
  - `pacientes_carga_reprogramada`,
  - `pacientes_carga_ok`,
  - `pacientes_carga_error`.

## Inicio: reemplazo de placeholder

Inicio deja de ser una pantalla vacía y pasa a reutilizar `PageGestionDashboard` como home operativa.

### Decisión

Se eligió reuso limpio de Gestión para aportar valor operativo inmediato sin duplicar lógica ni widgets:

- KPIs,
- alertas,
- estado operativo,
- accesos de navegación ya existentes.

Además, el título de navegación de `home` pasa a i18n (`nav.home`).
