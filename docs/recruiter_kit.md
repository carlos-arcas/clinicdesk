# Recruiter Kit (ClinicDesk)

## TL;DR
ClinicDesk es una aplicación clínica con analítica de riesgo de citas y flujo demo end-to-end.
Combina Clean Architecture, calidad automatizada y exportaciones listas para BI.
Está pensada para mostrar ingeniería de producto mantenible (no solo un prototipo ML).

## Demo en 3 minutos

### Objetivo de la demo
Mostrar, sin entrar en código, cómo ClinicDesk pasa de datos clínicos demo a decisiones operativas y artefactos auditables.

### Guion exacto (minuto a minuto)
1. **00:00 - 00:30 | Abrir app y contexto**
   - Ejecuta `python scripts/run_app.py`.
   - Muestra que hay un flujo funcional de escritorio y módulos clínicos.
2. **00:30 - 01:15 | Cargar datos demo reproducibles**
   - Ve a **Analítica (Demo)** o **Demo & ML**.
   - Ejecuta seed/demo data para poblar médicos, pacientes y citas.
   - Mensaje clave: entorno reproducible, sin depender de datos reales (PII).
3. **01:15 - 02:15 | Ejecutar pipeline completo**
   - Lanza el flujo completo (`seed -> build-features -> train -> score -> drift -> export`).
   - Enseña progreso paso a paso y resultado final (versiones + estado).
4. **02:15 - 02:45 | Enseñar resultados de negocio**
   - Abre carpeta `exports/` y enseña los CSV (`features`, `metrics`, `scoring`, `drift`, KPIs).
   - Explica que esos contratos alimentan Power BI.
5. **02:45 - 03:00 | Cierre técnico**
   - Enseña comando de calidad: `python -m scripts.gate_pr`.
   - Mensaje final: arquitectura limpia + gates + seguridad de datos + entregable BI.

## Puntos fuertes para CV
- **Clean Architecture real**: separación explícita dominio/aplicación/infra/presentación.
- **Quality gate canónico**: el estándar de PR se valida con `python -m scripts.gate_pr`.
- **Seguridad y privacidad**: controles anti-PII en logs/auditoría y opción de cifrado de PII en reposo.
- **i18n en UI**: catálogos y claves para evitar hardcodes visibles.
- **UI asíncrona para operaciones largas**: workflows demo con progreso/cancelación sin bloquear experiencia.

## Qué miraría un tech lead
- **Tests**: cobertura del core y pruebas por capas.
- **Gates**: lint, typing, tests, cobertura, seguridad y checks de arquitectura.
- **Separación de capas**: puertos/adaptadores y composición explícita.
- **Seguridad**: minimización de PII y políticas de sanitización.
- **DX**: setup reproducible, scripts de ejecución y comandos canónicos documentados.

## Cómo ejecutarlo
1. Setup
   - `./scripts/setup.sh` (Linux/macOS)
   - `scripts\\setup.bat` (Windows)
   - Alternativa: `python scripts/setup.py`
2. Run app
   - `python scripts/run_app.py`
3. Gate completo PR
   - `python -m scripts.gate_pr`

## Roadmap corto (próximos 3 hits)
1. **Demo grabada + dataset fixture oficial**
   - Impacto: onboarding más rápido para recruiting/sales y demos consistentes.
2. **Dashboard ejecutivo empaquetado (Power BI template)**
   - Impacto: acorta tiempo desde scoring a valor visible para negocio.
3. **Observabilidad operativa ampliada (SLA de jobs + trazas)**
   - Impacto: mejora confiabilidad en escenarios reales y facilita soporte.
