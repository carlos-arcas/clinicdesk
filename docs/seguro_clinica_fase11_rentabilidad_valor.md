# Seguro Clínica Fase 11 — Rentabilidad prudente y priorización por valor

## Qué añade esta fase

Esta fase incorpora una capa de **economía operativa prudente** para no priorizar solo por calor comercial.
Ahora el panel puede combinar:

- propensión comercial,
- margen esperado del plan,
- esfuerzo comercial estimado,
- riesgo de renovación,
- y nivel de cautela por evidencia.

## Contratos nuevos

Se incorporan contratos tipados en `clinicdesk/app/application/seguros/economia_valor.py`:

- `ValorEsperadoOportunidadSeguro`
- `MargenEsperadoPlanSeguro`
- `RiesgoEconomicoSeguro`
- `PrioridadValorSeguro`
- `InsightRentabilidadSeguro`
- `CampaniaRentableSeguro`
- `SegmentoRentableSeguro`
- `PanelValorEconomicoSeguro`

## Interpretación prudente (sin actuarial fiction)

- El margen usa una base simple y explicable: cuota anual estimada con factor de prudencia menos esfuerzo comercial.
- El valor esperado combina margen prudente con score comercial existente.
- Si la confianza es débil, la categoría cae a `EVIDENCIA_INSUFICIENTE` y fuerza acción conservadora.

## Cómo leer el panel ejecutivo

El resumen ejecutivo incorpora un bloque adicional de **valor esperado y priorización** con:

1. Oportunidades de mayor impacto combinado.
2. Campañas/canales con valor esperado total más alto.
3. Segmentos con mayor valor esperado prudente.
4. Insights con acción sugerida y nivel de cautela.

## Guía rápida de decisiones

### Qué oportunidad merece más esfuerzo
Prioriza las que combinan score de impacto alto + categoría de valor `ALTO` y cautela no alta.

### Qué campaña compensa repetir
Repite campañas/canales con mayor valor total esperado y cautela baja/media.

### Qué segmento convierte pero deja poco valor
Si un segmento tiene conversión razonable pero categoría `BAJO`, evitar sobreinversión de seguimiento.

### Qué renovación salvar primero
Renovaciones en riesgo con valor alto o razonable se priorizan antes que casos calientes de bajo margen.

## Límites y cautelas

- No sustituye pricing actuarial ni modelos de siniestralidad.
- No debe usarse para prometer ROI exacto.
- Es una capa de priorización operativa para asignar esfuerzo comercial con más criterio.
