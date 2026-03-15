# Seguro Clínica Fase 16 — Cobros, cuotas, impagos, suspensión y reactivación

## Qué añade esta fase

Esta fase incorpora una **capa económica-operativa** de póliza separada de la preventa y de la postventa general:

- emisión de cuotas periódicas,
- gestión de vencimientos,
- registro de pago e impago,
- suspensión y reactivación operativa,
- cartera económica por estado de riesgo.

No incluye pasarela de pago ni conciliación bancaria real.

## Diferencia entre póliza activa y estado económico

- **Póliza activa**: representa vigencia contractual y datos de asegurados.
- **Estado económico**: representa salud de cobros y riesgo operativo (al día, vencida, impagada, suspendida, reactivable).

Una póliza puede estar activa en vigencia y, a la vez, estar en riesgo económico.

## Cómo leer cartera en riesgo

La cartera económica clasifica por:

- AL_DIA
- PROXIMA_A_VENCER
- VENCIDA
- IMPAGADA
- SUSPENDIDA
- REACTIVABLE

Además expone motivo de estado para trazabilidad operativa.

## Qué significa suspensión/reactivación en esta fase

- **Suspensión**: evento operativo prudente ante riesgo económico alto, sin automatismo agresivo.
- **Reactivación**: evento operativo cuando existe regularización suficiente y procede revisión de retorno.

## Qué no cubre todavía

- Cobro automático con pasarela externa.
- Integración bancaria o conciliación contable.
- Reglas actuariales avanzadas o recobro judicial.

## Mini guía operativa

### Cómo revisar cuotas vencidas
1. Filtrar cartera por estado `VENCIDA` o `IMPAGADA`.
2. Priorizar pólizas con más cuotas impagadas y mayor pendiente.
3. Registrar acción operativa e incidencia si aplica.

### Qué pólizas priorizar por riesgo económico
1. Prioridad 1: `SUSPENDIDA` e `IMPAGADA`.
2. Prioridad 2: `VENCIDA`.
3. Prioridad 3: `PROXIMA_A_VENCER` para prevención.

### Cuándo suspender o revisar
- Suspender cuando haya impago persistente y riesgo operativo alto.
- Mantener en revisión cuando hay señales mixtas sin base dura para suspensión.

### Cómo interpretar reactivación
- Reactivable no implica activación automática.
- Requiere validación operativa para cerrar riesgo económico.
