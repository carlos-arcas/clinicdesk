# Pendientes funcionales

Derivado de `docs/features.json`.

## Pendientes reales
- **FTR-003 — Se puede autenticar usuario y bloquear tras intentos fallidos**
  - Pendiente principal: convertir la integración fuerte actual de login desktop en un E2E completo con `main()`, transición real de logout y reapertura de sesión sin vender más cobertura de la que existe hoy.
- **FTR-005 — Se puede ejecutar pipeline ML de riesgo de citas**
  - Pendiente principal: cerrar el salto entre el smoke desktop reforzado y un E2E total real; aún falta cubrir arranque completo de aplicación/loop principal, navegación cross-módulo más amplia y validación operacional de cierre de background fuera del tramo headless ya cubierto.
- **FTR-008 — Se puede rotar claves criptográficas de campos sensibles**
  - Pendiente principal: prueba operacional automatizada dentro de un despliegue realista.
