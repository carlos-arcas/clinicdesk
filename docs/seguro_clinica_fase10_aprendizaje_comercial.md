# Seguro Clínica Fase 10 — Aprendizaje comercial prudente

## Qué añade esta fase

Esta fase introduce una capa explícita de **aprendizaje comercial** sobre el histórico operativo de seguros.
La capa consolida resultados de campañas ejecutables, cartera y cierres para construir:

- ranking de efectividad de campañas,
- insights por segmento/cohorte,
- insights por objeción y sensibilidad al precio,
- argumentos y planes con mejor señal por perfil,
- playbooks comerciales recomendados por segmento.

No se usa ML causal ni inferencias fuertes: los resultados se etiquetan con cautela muestral.

## Contratos de aprendizaje incorporados

Se definen contratos tipados para evitar dicts opacos y facilitar evolución:

- `MetricaAprendizajeComercialSeguro`
- `EfectividadCampaniaSeguro`
- `InsightArgumentoSeguro`
- `InsightPlanSeguro`
- `InsightSegmentoSeguro`
- `PlaybookComercialSeguro`
- `RecomendacionCampaniaSeguro`
- `PanelAprendizajeComercialSeguro`

Cada contrato refleja población analizada, tamaño de muestra, métrica principal, señal de efectividad, cautela y acción sugerida.

## Qué aprende el sistema

1. **Campañas**
   - Señal por campaña: `prometedora`, `razonable`, `floja`, `muestra_insuficiente`.
   - Cálculo sobre trabajados/convertidos, sin inventar causalidad.

2. **Segmentos y cohortes**
   - Comparación de conversión por: segmento, objeción principal, sensibilidad al precio, fit comercial y origen.
   - Si no hay base mínima, se informa `Muestra insuficiente`.

3. **Argumentos/planes ganadores**
   - Ranking por `segmento + argumento` y `segmento + plan` con señal prudente.
   - Recomendación para repetir, iterar o capturar más evidencia.

4. **Playbooks operativos**
   - Por segmento objetivo: plan sugerido, argumento principal, objeción a vigilar y siguiente acción.
   - Incluye cautela muestral para no sobreconfiar.

## Cómo leer insights prudentes

- **No** interpretar una señal como verdad universal.
- Si la muestra es insuficiente, usar el insight solo para experimentación controlada.
- Priorizar decisiones con trazabilidad por ítem de campaña y reevaluar periódicamente.

## Mini guía ejecutiva

### Qué campaña repetir
1. Revisar campañas con señal `prometedora`.
2. Validar que la cautela muestral sea aceptable.
3. Replicar en cohortes equivalentes primero.

### Qué segmento atacar primero
1. Elegir segmentos con mejor conversión y muestra aceptable.
2. Excluir segmentos con fricción dominante sin plan de objeciones.

### Qué argumento probar
1. Empezar por argumento con mejor resultado en el segmento objetivo.
2. Si no hay base suficiente, ejecutar lote pequeño con instrumentación completa.

### Cómo no engañarte con muestras pequeñas
- Evitar cambiar estrategia global por 1-2 cierres.
- Exigir umbral mínimo de muestra antes de escalar una recomendación.
- Registrar resultados por campaña/item para retroalimentación confiable.
