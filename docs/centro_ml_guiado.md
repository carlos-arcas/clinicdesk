# Centro ML guiado (Fase 4 — Playbooks ejecutables, guardrails y reanudación)

El **Centro ML guiado** combina estado del pipeline + recomendaciones + **playbooks por objetivo real** y ahora añade ejecución asistida.

## Objetivos disponibles

1. **Preparar demo ML completa**
2. **Entrenar un modelo nuevo**
3. **Puntuar datos con seguridad**
4. **Revisar drift y decidir reentrenamiento**
5. **Exportar resultados para BI**

Cada objetivo muestra: descripción, cuándo usarlo, prerequisitos, criterio de cierre y pasos guiados.

## Qué incluye cada paso guiado

Para cada paso (prepare/train/score/drift/export), la UI muestra:

- qué hace,
- por qué importa,
- qué necesitas antes,
- qué resultado produce,
- qué mirar después,
- CTA sugerida,
- estado contextual: completado / recomendado / disponible / bloqueado / innecesario.

## Playbooks ejecutables (nuevo)

El panel de playbook incorpora:

- **CTA del siguiente paso** con preset seguro (prepare/train/score/drift),
- **progreso operativo** (completados, bloqueados, total),
- **último resultado ejecutado** con siguiente paso recomendado,
- **guardrail de confirmación** al repetir un paso ya completado.

La ejecución usa estado real de artefactos y no dispara acciones bloqueadas.

## Guardrails aplicados

- No se ejecuta train sin dataset disponible.
- No se ejecuta score sin dataset + modelo vigente.
- No se ejecuta drift sin dos versiones de dataset.
- Los pasos completados pasan a modo **requiere confirmación** para evitar repeticiones inútiles.

## Reanudación y continuidad

Al volver a la pantalla, el sistema vuelve a inferir el estado desde `feature_store`, `model_store` y exports. El usuario ve:

- qué pasos siguen pendientes,
- cuál es la siguiente acción recomendada,
- qué pasó en el último paso lanzado desde el playbook.

## Guía rápida

- **Quiero demo completa sin liarme**: selecciona `demo_completa` y pulsa la CTA sugerida en cada iteración.
- **Quiero entrenar y luego puntuar**: usa `entrenar_modelo_nuevo`, ejecuta train y después score.
- **Quiero revisar si debo reentrenar**: usa `revisar_drift_reentrenar` y ejecuta drift con dos datasets.
- **Quiero exportar sin equivocarme**: usa `exportar_bi`; si el paso está bloqueado, primero completa scoring.

## Limitaciones honestas

- En esta fase la ejecución directa está habilitada para `prepare/train/score/drift`.
- `export` se mantiene guiado por estado y guardrails, pero sin ejecución directa unificada desde el CTA.
- El sistema guía y bloquea incoherencias básicas, pero no sustituye criterio experto.
