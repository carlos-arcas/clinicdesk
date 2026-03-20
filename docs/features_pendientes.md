# Pendientes funcionales

Derivado de `docs/features.json`.

## Pendientes reales
- **FTR-003 — Se puede autenticar usuario y bloquear tras intentos fallidos**
  - Pendiente residual: ejecutar de forma automatizada el arranque completo con `main()` hasta `app.exec()`/salida real del loop Qt. El wiring real de login, logout, reapertura y cancelación ya queda cubierto en headless controlado, pero no existe aún un recorrido operacional completo del entrypoint hasta cierre final del proceso.
- **FTR-005 — Se puede ejecutar pipeline ML de riesgo de citas**
  - Pendiente principal: cerrar el salto entre el smoke desktop reforzado y un E2E total real; aún falta cubrir arranque completo de aplicación/loop principal, navegación cross-módulo más amplia y validación operacional de cierre de background fuera del tramo headless ya cubierto.
- **FTR-008 — Se puede rotar claves criptográficas de campos sensibles**
  - Pendiente principal: prueba operacional automatizada dentro de un despliegue realista.
