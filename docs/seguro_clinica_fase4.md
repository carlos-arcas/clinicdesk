# Seguro Clínica Fase 4 — Segmentación comercial y encaje de producto

## Qué añade esta fase

Esta fase incorpora una capa comercial determinista y persistible sobre el contexto de seguros para:

- clasificar público objetivo operativo,
- registrar motivaciones y objeciones comerciales,
- calcular fit comercial explicable por oportunidad,
- habilitar consultas de cartera orientadas a priorización,
- dejar un read model utilizable en fases futuras de ML comercial.

## Segmentación comercial disponible

Se modelan contratos de dominio explícitos para:

- `SegmentoClienteSeguro`
- `OrigenClienteSeguro`
- `NecesidadPrincipalSeguro`
- `MotivacionCompraSeguro`
- `ObjecionComercialSeguro`
- `SensibilidadPrecioSeguro`
- `FriccionMigracionSeguro`
- `EncajePlanSeguro`
- `PerfilComercialSeguro`
- `EvaluacionFitComercialSeguro`

## Interpretación del fit comercial

El motor `MotorFitComercialSeguro` combina:

1. clasificación de simulación de migración,
2. sensibilidad al precio,
3. fricción de migración,
4. objeción principal,
5. motivaciones,
6. advertencias de migración.

Resultado:

- `ALTO`, `MEDIO`, `BAJO` o `REVISAR`,
- motivo principal del fit,
- riesgos/fricciones,
- argumentos de valor,
- indicador de insistencia comercial,
- recomendación de revisión humana.

## Operación comercial recomendada

### Cómo registrar una buena oportunidad

- usar segmento y origen reales,
- registrar necesidad principal + motivaciones concretas,
- explicitar objeción principal y sensibilidad de precio,
- revisar argumentos de valor antes de enviar oferta.

### Cómo detectar una oportunidad débil

- fit `BAJO` o `REVISAR`,
- objeción crítica (permanencia o precio alto),
- fricción de migración alta,
- advertencias múltiples en simulación.

## Base preparada para ML comercial futuro (sin ML en esta fase)

La persistencia de oportunidades incluye variables históricas útiles para dataset:

- segmento y origen,
- necesidad, motivaciones y objeción,
- sensibilidad al precio y fricción,
- fit y motivo del fit,
- evolución de estados, seguimientos y cierre comercial.

Además, se exponen consultas agregadas por segmento, fit y objeción para análisis de cartera.
