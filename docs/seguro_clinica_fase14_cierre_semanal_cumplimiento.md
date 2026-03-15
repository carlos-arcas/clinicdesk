# ClinicDesk Seguros · Fase 14 · Cierre semanal, cumplimiento y aprendizaje operativo

## Qué añade esta fase

Esta fase cierra el ciclo operativo entre planificación y ejecución real para seguros:

- lectura semanal de **plan vs hecho**,
- cálculo de **cumplimiento real**,
- detección de **desvíos operativos**,
- identificación de **bloqueos recurrentes**,
- generación de **aprendizaje prudente** para la semana siguiente.

## Componentes principales

1. **Contratos explícitos de cierre**
   - `PeriodoSemanaSeguro`
   - `CumplimientoPlanSeguro`
   - `DesvioEjecucionSeguro`
   - `BloqueoOperativoSeguro`
   - `AprendizajeEjecucionSeguro`
   - `CierreSemanalSeguro`
   - `ResumenSemanaSeguro`

2. **Motor de cierre semanal (`CierreSemanalSeguroService`)**
   - reutiliza agenda semanal, cola operativa, campañas y analítica,
   - compara tareas previstas vs ejecutadas,
   - calcula cumplimiento y tareas críticas no ejecutadas,
   - detecta posposición repetida, campañas sugeridas no lanzadas y renovaciones críticas sin atención.

3. **Integración ejecutiva en UI de seguros**
   - resumen de cierre semanal,
   - bloqueos de proceso,
   - recomendación de foco para próxima semana.

## Cómo leer el cierre semanal

### Qué mirar al final de la semana

1. **Cumplimiento semanal** (`ejecutadas / previstas`).
2. **Pendientes y vencidas** para estimar arrastre real.
3. **Patrones** (posposición repetida, campañas no lanzadas, renovaciones críticas sin resolver).
4. **Bloqueos** con acción de desbloqueo propuesta.

### Qué hacer si cae el cumplimiento

- reducir alcance operativo la semana siguiente,
- cerrar primero tareas críticas no ejecutadas,
- limitar nuevas iniciativas hasta recuperar ratio de cierre.

### Cómo detectar sobrecarga o foco mal repartido

Señales:

- pendientes > resueltas,
- volumen de vencidas en crecimiento,
- campañas sugeridas sin lanzamiento,
- renovaciones críticas acumuladas sin resolución.

## Limitaciones honestas

- El motor detecta **patrones operativos**, no causalidad fuerte.
- Las recomendaciones son prudentes y de gestión táctica, no decisiones automáticas.
- El aprendizaje se basa en trazas y estados disponibles, no en instrumentación externa avanzada.
