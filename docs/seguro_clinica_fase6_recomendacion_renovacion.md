# Seguro clínica fase 6: recomendación prudente, riesgo de renovación y retención

La fase 6 añade una capa comercial explicable para responder cuatro preguntas operativas:

1. qué plan conviene proponer,
2. qué riesgo de no renovación/fuga existe,
3. cuál es el argumento comercial principal,
4. qué siguiente acción de retención se sugiere.

## Enfoque de diseño

Se implementa una estrategia **híbrida y prudente**:

- reglas deterministas del dominio comercial (segmento, sensibilidad a precio, objeción, fit y clasificación de migración),
- señales de scoring existente para graduar confianza y cautela,
- semáforo de renovación sin prometer precisión estadística cuando el histórico es bajo.

El servicio no automatiza cierre ni renovación. Solo prioriza y explica.

## Contratos de salida

`RecomendadorProductoSeguroService` devuelve `DiagnosticoComercialSeguro` con:

- `RecomendacionPlanSeguro` (plan recomendado/alternativo, motivo, objeción y cautela),
- `RiesgoRenovacionSeguro` (semaforo `ALTO|MEDIO|BAJO|EVIDENCIA_INSUFICIENTE`, score orientativo y evidencia),
- `ArgumentoComercialSeguro` (ángulo dominante + contraargumento prudente),
- `AccionRetencionSeguro` (siguiente paso sugerido y límites de información).

## Cómo leer la recomendación

### Qué plan recomendar y por qué

- Si existe base comercial y fit suficiente, se propone plan principal y alternativo.
- Si no hay ventaja robusta, la salida explicita **sin recomendación fuerte**.

### Cómo leer una renovación en riesgo

- `ALTO`: priorizar revisión de renovación y fricciones activas.
- `MEDIO`: mantener seguimiento cercano y afinar propuesta.
- `BAJO`: continuar cadencia normal de cartera.
- `EVIDENCIA_INSUFICIENTE`: no inferir riesgo; pedir más señales.

### Cliente sensible al precio

- Argumento dominante orientado a ahorro/coste total,
- acción sugerida: trabajar objeción de precio con transparencia,
- evitar descuentos automáticos sin validar margen y cobertura.

## Limitaciones honestas de la fase

- El score de riesgo es orientativo, no probabilidad calibrada.
- Sin histórico denso por segmento, la cautela tiene prioridad.
- No se sustituyen decisiones humanas de venta/retención.
