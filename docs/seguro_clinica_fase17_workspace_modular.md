# Seguro clínica fase 17 — Workspace modular de seguros

## Objetivo

Desacoplar la presentación de seguros para que `PageSeguros` actúe como orquestador fino y el módulo crezca por áreas funcionales sin volver a un contenedor monolítico.

## Estructura modular aplicada

Se introduce un workspace interno con navegación por sección y composición de paneles separados:

- **preventa**: comparativa y migración.
- **cartera**: funnel comercial, seguimiento y cola operativa.
- **campanias**: ejecución y trazabilidad por lote/cohorte.
- **analitica**: panel ejecutivo, aprendizaje, valor y forecast.
- **agenda**: alertas, plan semanal y cierre.
- **postventa**: pólizas e incidencias.
- **economia**: cuotas, pagos, impagos, suspensión/reactivación.

## Mapa de módulos de presentación

- `clinicdesk/app/pages/seguros/page.py`
  - Orquestador de servicios y wiring de handlers.
- `clinicdesk/app/pages/seguros/workspace_layout.py`
  - Construcción de widgets por sección y composición en `QStackedWidget`.
- `clinicdesk/app/pages/seguros/workspace_navegacion.py`
  - Estado de sección activa, opciones de selector y restauración.
- `clinicdesk/app/pages/seguros/page_actions_comercial.py`
  - Casos de interacción comercial/campañas/analítica/agenda.
- `clinicdesk/app/pages/seguros/page_actions_postventa.py`
  - Casos de interacción de pólizas y estado económico.
- `clinicdesk/app/pages/seguros/page_ui_support.py`
  - Retraducción i18n del workspace y labels por sección.

## Convenciones para futuras fases

1. **No ampliar `PageSeguros` con lógica de rendering o reglas UI complejas**: extraer a `workspace_layout` o `page_actions_*`.
2. **Toda nueva subárea debe entrar en `workspace_navegacion.py`** para mantener contrato único de secciones.
3. **Textos visibles solo con i18n** (`core.py`), sin literales en widgets.
4. **Acciones de botones delegadas** en módulos especializados (comercial/postventa/economía).
5. **Tests de navegación y contratos de workspace** obligatorios cuando se agreguen secciones.
