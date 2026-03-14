# Seguro Clínica Fase 5 — ML comercial prudente para priorizar cartera

## Qué predice esta fase

Esta fase añade una primera capa de **scoring comercial explicable y prudente** sobre oportunidades de seguro:

- propensión a conversión,
- propensión a migración favorable,
- prioridad comercial de seguimiento,
- siguiente mejor acción comercial.

No sustituye criterio humano: organiza trabajo y foco comercial.

## Dataset histórico usado

El dataset reproducible de seguros parte del read model persistido en `seguro_oportunidades` + `seguro_seguimientos` + `seguro_renovaciones`:

- segmento y origen,
- sensibilidad de precio,
- objeción principal,
- fricción de migración,
- clasificación de migración,
- fit comercial,
- plan destino,
- número de seguimientos,
- días de ciclo,
- estado actual,
- resultado comercial,
- indicador de renovación favorable.

> Guardrail: no se usa PII para scoring en esta fase.

## Modelo/base implementada

Se utiliza baseline determinista con mezcla de:

1. tasas históricas base de conversión y migración favorable,
2. ajustes transparentes por señales comerciales de oportunidad,
3. umbral de confianza relativa según tamaño de histórico.

Cuando la muestra histórica es baja, el sistema rebaja confianza y añade cautela explícita.

## Cómo interpretar una oportunidad

- **Alta**: oportunidad caliente, priorizar contacto.
- **Media**: viable, requiere afinar oferta o seguimiento.
- **Baja**: débil por ahora; mantener vigilancia.
- **No prioritaria**: no dedicar esfuerzo activo en el ciclo actual.

Cada caso incluye:

- motivo principal,
- acción sugerida,
- cautela/límite,
- confianza relativa.

## Siguiente mejor acción (NBA) en esta fase

Acciones disponibles:

- insistir seguimiento,
- preparar mejor oferta,
- revisar objeción de precio,
- revisar elegibilidad/migración,
- posponer y reevaluar,
- no priorizar por ahora.

Se sugiere como recomendación operativa, no orden automática.

## Qué NO predice todavía

- estimación causal individual de cierre,
- recomendación automática de plan óptimo,
- riesgo de fuga/retención avanzado,
- uplift por canal de contacto.

Estas capacidades quedan para siguientes fases con más histórico validado.

## Mini guía operativa

### Cómo decidir a quién llamar primero

1. tomar oportunidades con prioridad alta,
2. revisar confianza relativa y cautela,
3. ejecutar acción sugerida con criterio humano,
4. registrar seguimiento para retroalimentar histórico.

### Cómo usar la prioridad comercial sin sobreconfiar

- usar prioridad como orden de trabajo, no como veredicto.
- combinar score con contexto clínico/comercial real.

### Qué hacer con oportunidades débiles

- pasar a seguimiento liviano,
- evitar sobreinversión en llamadas repetitivas,
- reabrir foco al cambiar señal comercial.
