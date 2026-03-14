# Centro ML guiado (Fase 2 — Asistente de decisiones)

El **Centro ML guiado** ahora incluye un asistente operativo que no solo muestra estado, también recomienda **qué hacer ahora**, **por qué**, **beneficio**, **riesgo de no actuar** y **cuándo no conviene ejecutar un paso**.

## Flujo guiado base

1. Preparar datos
2. Entrenar modelo
3. Puntuar citas
4. Revisar drift
5. Exportar artefactos
6. Revisar resumen y decidir

## Qué añade el asistente de decisiones ML

- Recomendaciones accionables priorizadas por estado real del pipeline.
- Distinción explícita entre acción **posible**, **recomendada**, **bloqueada** e **innecesaria**.
- Bloqueo explícito de scoring trained cuando dataset/modelo no son compatibles.
- Advertencias útiles (por ejemplo, drift pendiente o resultados débiles).
- Resumen ejecutivo corto para lectura rápida no técnica.

## Cómo se generan las recomendaciones

El motor de recomendaciones evalúa:

- existencia y calidad mínima de dataset,
- disponibilidad de modelo,
- compatibilidad dataset/modelo (`trained_on_dataset_version`),
- disponibilidad de score,
- necesidad de drift,
- estado de exportaciones,
- señales de calidad de evaluación (`test_metrics`).

No inventa recomendaciones cuando faltan evidencias en metadata.

## Resumen ejecutivo ML

El resumen responde en 5 líneas:

- estado actual,
- qué falta,
- siguiente paso,
- riesgo principal,
- utilidad inmediata.

Está diseñado para demo de portfolio y uso operativo diario.

## Mini guía rápida

### Si no hay dataset

1. Preparar datos.
2. Validar volumen mínimo.
3. Recién entonces entrenar.

### Si el modelo no es compatible

1. No usar scoring trained.
2. Reentrenar con dataset actual.
3. Volver a puntuar.

### Cuándo mirar drift

- Siempre que haya dos o más versiones de dataset.
- Antes de decisiones de operación sensibles.

### Para qué exportar

- Compartir resultados con operación/gestión.
- Trazabilidad para auditoría.
- Integración con reporting externo (CSV contractuales).

## Limitaciones honestas

- El asistente orienta; no reemplaza criterio clínico u operativo humano.
- Las métricas offline ayudan a decidir, pero no garantizan rendimiento futuro.
- El estado depende de artefactos locales (`feature_store`, `model_store`, carpeta de export).
