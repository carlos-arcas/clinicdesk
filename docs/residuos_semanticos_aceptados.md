# Residuos semánticos aceptados

Este inventario recoge residuos demo que **siguen soportando infraestructura real** y cuyo renombrado total no se aborda en este ciclo para evitar un refactor transversal innecesario.

## Aceptados en este ciclo

- `DemoMLFacade` y el módulo `application/services/demo_ml_facade.py`.
  - **Motivo**: siguen siendo el contrato central consumido por múltiples servicios de aplicación y tests estructurales. Renombrarlo por completo implicaría tocar imports transversales, snapshots mentales del equipo y documentación histórica sin ganancia funcional inmediata.
  - **Mitigación aplicada**: el wiring canónico del contenedor ya usa naming de producto (`analitica_ml_facade`, `build_analitica_ml_facade`) y se mantiene alias legacy estable para compatibilidad.
- Claves i18n con prefijo `demo_ml.`.
  - **Motivo**: el prefijo funciona hoy como namespace técnico estable para el centro analítico y playbooks ML. Renombrarlo en bloque sería una migración extensa de bajo valor para este ciclo.
  - **Mitigación aplicada**: se eliminó copy principal que presentaba la capacidad como demo donde ya no aplica y se reforzaron smoke tests contra reintroducción en rutas principales.
- Flujos explícitos `seed_demo` / `modo_demo`.
  - **Motivo**: representan capacidades reales de seed controlado y auditoría de acceso demo, con implicaciones de seguridad y trazabilidad. No son mero copy legacy.
  - **Mitigación aplicada**: se conservan solo en superficies donde describen comportamiento real, no como narrativa principal del producto.
