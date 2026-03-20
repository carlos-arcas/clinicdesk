# Pendientes funcionales

Derivado de `docs/features.json`.

## Pendientes reales
- **FTR-005 — Se puede ejecutar pipeline ML de riesgo de citas**
  - Pendiente principal: cerrar el salto entre el harness E2E/controlado del entrypoint real y un E2E total real; ya existe arranque con `main()` hasta `app.exec()`/salida limpia, navegación real al módulo ML y verificación de cierre sin hilos de entrenamiento activos, pero aún falta navegación cross-módulo más amplia y validación operacional de background fuera del tramo controlado.
- **FTR-006 — Se puede exportar KPIs y resultados en CSV**
  - Sin pendiente E2E relevante en el flujo hoy soportado por producto: el wiring contractual vía CLI ya queda cubierto con SQLite y stores temporales, incluyendo scoring, drift opcional y validación de contenido de los cuatro CSV. El residual honesto queda fuera de este feature: no existe UI real para este flujo y no se reclama cobertura UI inventada.
- **FTR-008 — Se puede rotar claves criptográficas de campos sensibles**
  - Pendiente principal: prueba operacional automatizada dentro de un despliegue realista.
