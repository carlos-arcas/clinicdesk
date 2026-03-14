# Seguro clínica fase 1

## Qué modela

Esta fase introduce un núcleo determinista para:

- catálogo normalizado de planes propios y externos,
- comparación por coberturas, carencias, copagos, límites y exclusiones,
- simulación de migración con salida explicable,
- elegibilidad determinista con estados: elegible, elegible con revisión, no elegible e información insuficiente.

## Qué no hace todavía

- No incorpora ML ni scoring de propensión.
- No realiza underwriting complejo.
- No carga todavía planes externos desde CSV (se deja el catálogo en memoria como base inicial).

## Cómo interpretar una migración

- **FAVORABLE**: predominan mejoras y no hay bloqueos de elegibilidad.
- **DESFAVORABLE**: pérdidas relevantes o no elegibilidad.
- **REVISAR**: faltan datos o existen advertencias que requieren criterio humano.

## Cuándo usar comparativa vs migración

- Usa **comparativa** para análisis técnico de diferencias de producto.
- Usa **migración** cuando necesitas una recomendación ejecutiva para conversación comercial.

> Continuación comercial: ver `docs/seguro_clinica_fase2.md`.
