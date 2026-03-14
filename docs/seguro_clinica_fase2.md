# Seguro clínica fase 2: flujo comercial y renovación

## Qué añade esta fase

La fase 2 incorpora un funnel comercial operativo encima del comparador/migración determinista de fase 1.

Incluye:
- modelado de candidato, oportunidad, oferta, seguimiento, cierre y renovación,
- pipeline explícito con transiciones válidas/inválidas,
- generación de oferta comercial desde la simulación técnica,
- soporte de seguimiento humano separado de la sugerencia del motor,
- base mínima de renovación para preparar churn/riesgo de fuga en fases ML.

## Estados del funnel comercial

`DETECTADA -> ANALIZADA -> ELEGIBLE -> OFERTA_PREPARADA -> OFERTA_ENVIADA -> EN_SEGUIMIENTO -> (CONVERTIDA | RECHAZADA | POSPUESTA)`

Post-conversión:
`CONVERTIDA -> PENDIENTE_RENOVACION -> (RENOVADA | NO_RENOVADA)`

No se permiten saltos no definidos; cualquier transición inválida genera error de dominio.

## Seguimiento comercial

Cada seguimiento guarda:
- fecha,
- estado aplicado,
- acción comercial tomada,
- nota corta,
- siguiente paso.

El seguimiento representa intervención humana comercial, mientras que la clasificación de migración se mantiene como salida del motor determinista.

## Cierre comercial

Resultados soportados:
- `CONVERTIDO`
- `RECHAZADO`
- `POSPUESTO`
- `PENDIENTE_REVISION`

Cuando la oportunidad se convierte, se genera automáticamente una renovación pendiente.

## Renovación básica

La renovación almacena:
- plan vigente,
- fecha prevista de renovación,
- flag de revisión pendiente,
- resultado (`PENDIENTE`, `RENOVADA`, `NO_RENOVADA`).

Esta estructura queda preparada para futuras recomendaciones ML (propensión, fuga, valor esperado).

## Guía operativa corta

1. Ejecutar comparador como diagnóstico técnico.
2. Abrir oportunidad cuando exista destino potencial y caso comercial.
3. Preparar oferta con resumen de valor y notas comerciales estructuradas.
4. Registrar seguimientos con acciones y siguiente paso.
5. Cerrar como convertido/rechazado/pospuesto según resultado.
6. Revisar renovaciones pendientes para continuidad.

## Pendiente para fase ML comercial

- score de propensión a contratar,
- probabilidad de migración por segmento,
- recomendación automática de plan,
- señal temprana de no renovación/churn,
- estimación de valor esperado de cliente.
