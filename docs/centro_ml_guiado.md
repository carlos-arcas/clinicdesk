# Centro ML guiado (Fase 3 — Playbooks operativos por objetivo)

El **Centro ML guiado** ahora combina estado del pipeline + recomendaciones + **playbooks por objetivo real**.

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

## Decisiones por objetivo (no solo por estado global)

Los playbooks reutilizan el estado real del pipeline y añaden reglas de objetivo:

- **Puntuar con seguridad** bloquea score si dataset/modelo no son compatibles.
- **Exportar para BI** marca bloqueo si todavía no hay scoring útil.
- **Revisar drift y reentrenar** marca drift como innecesario cuando no hay dos datasets para comparar.
- Cada playbook recomienda el siguiente paso dentro de su propio contexto.

## Guía rápida de uso

- Si empiezas desde cero: usa **Preparar demo ML completa**.
- Si ya tienes datos pero no modelo: usa **Entrenar un modelo nuevo**.
- Si ya tienes modelo y quieres evitar errores: usa **Puntuar con seguridad**.
- Si sospechas cambio de comportamiento: usa **Revisar drift y decidir reentrenamiento**.
- Si necesitas material para BI/portfolio: usa **Exportar resultados para BI**.

## Limitaciones honestas

- Los playbooks dependen de artefactos locales (`feature_store`, `model_store`, exports).
- El sistema guía y bloquea incoherencias básicas, pero no sustituye criterio experto.
- Drift no aplica si no existe comparación entre versiones de dataset.
