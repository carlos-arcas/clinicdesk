# Centro ML guiado (Fase 1)

El **Centro ML guiado** organiza el flujo operativo de ML para usuarios no técnicos en 6 pasos:

1. Preparar datos
2. Entrenar modelo
3. Puntuar citas
4. Revisar drift
5. Exportar artefactos
6. Revisar resumen y decidir

## Qué hacer primero

1. Entrar en **Centro ML guiado**.
2. Verificar el bloque **Estado del pipeline**.
3. Ejecutar la **acción recomendada** mostrada en pantalla.

## Qué hacer si falla

- Si el botón está bloqueado, leer el motivo de bloqueo en el estado.
- Corregir el prerequisito (por ejemplo: generar dataset o entrenar modelo compatible).
- Reintentar el paso bloqueado.

## Cómo interpretar resultados

- **Scoring**: porcentaje de citas en riesgo alto para priorizar seguimiento.
- **Drift**: cambios entre datasets; AMBER/RED indica revisar datos y posible reentrenamiento.
- **Resumen de entrenamiento**: accuracy/precision/recall ayudan a entender desempeño histórico, no futuro garantizado.
- **Exportaciones**: CSV para reporting externo y trazabilidad.

## Limitaciones actuales

- El estado guiado se basa en artefactos locales (`feature_store`, `model_store`, carpeta de export).
- La compatibilidad se valida por `trained_on_dataset_version` del metadata de modelo.
- No sustituye criterio clínico ni decisiones operativas humanas.
