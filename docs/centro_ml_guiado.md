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

## Lecturas operativas ML (nuevo en Fase 5)

Se añadió una capa reusable de interpretación operativa (`lecturas_operativas_ml`) para transformar lecturas técnicas en decisiones accionables.

### Qué lecturas cubre

- **Scoring**: traduce proporción de riesgo alto en priorización operativa, con límites explícitos.
- **Drift**: convierte PSI en señal de mantenimiento (sin asumir reentreno automático).
- **Métricas de evaluación**: conecta accuracy/precision/recall con nivel de confianza de uso.
- **Exportación**: explica valor operativo de compartir artefactos y qué no implica.

### Estructura estándar por lectura

Cada lectura expone contrato estable con:

- lectura origen,
- resumen humano,
- utilidad práctica,
- nivel de confianza,
- semáforo (verde/amarillo/rojo),
- riesgo principal,
- acción sugerida,
- cuándo mirar,
- cuándo no concluir fuerte,
- qué no significa.

### Mini guía de uso en demo / operación

- **Si quieres saber si el scoring sirve hoy**: mira semáforo + acción sugerida de `scoring`.
- **Si quieres decidir si revisar drift**: mira `drift`; rojo implica investigar, no reentrenar en automático.
- **Si quieres estimar confianza de uso**: mira `métricas`; muestra pequeña o métricas débiles => cautela.
- **Si quieres compartir evidencia a BI**: mira `exportación`; disponible != modelo validado.

## Lista de trabajo ML accionable (Fase 6)

Se añadió una capa de **priorización operativa de citas** que transforma el scoring existente en una bandeja de trabajo real para recepción/coordinación.

### Cómo se genera

1. Se toma el `ScoreCitasResponse` del pipeline (score + label + reasons por cita).
2. Se cruza con el read model de citas visibles.
3. Se construye una lista tipada (`ListaTrabajoML`) con:
   - prioridad (`alta/media/baja`),
   - motivo de priorización,
   - acción sugerida,
   - cautela explícita,
   - trazabilidad mínima del score origen.

### Qué decisiones ayuda a tomar

- **Qué revisar primero hoy** (items de prioridad alta arriba).
- **Qué requiere validación manual** (prioridad media).
- **Dónde no conviene sobreactuar** (prioridad baja / evidencia débil).
- **Cuándo usar acciones fuertes** (solo en casos con señal consistente).

### Guardrails incluidos

- El score **no** se presenta como verdad absoluta.
- Si la evidencia es débil o incompleta, se propone acción no concluyente.
- Las acciones son operativas (confirmación/revisión), **no** decisiones clínicas automáticas.
- Se muestra cautela por item para evitar sobreinterpretación.

### Mini guía de uso sin engañarte

- Empieza por filtro **Prioridad alta** y confirma contexto antes de ejecutar acción intensa.
- Usa **Prioridad media** como cola de validación manual breve.
- En **Prioridad baja**, evita escalar sin nueva evidencia operativa.
- Si aparece cautela por metadata incompleta, úsalo como señal inicial y no como cierre de decisión.
