# Seguros — política operativa de no-fuga en observabilidad y salidas

## Objetivo
Endurecer el módulo de seguros para evitar fuga accidental de PII/PHI y detalle económico innecesario en:
- logging técnico,
- metadatos de auditoría,
- paneles ejecutivos,
- salidas dataset-friendly y read models de UI.

## Matriz operativa aplicada

| Contexto | Campos permitidos | Redacción / resumen | Nunca permitido |
|---|---|---|---|
| `logging_tecnico_seguro` | `evento`, `correlation_id`, `horizonte`, `volumen`, `conversiones_esperadas`, `alertas`, `tareas`, `renovaciones`, `outcome` | Strings redactados por `redactar_texto_pii`, colecciones a `count` | `payload`, `titular`, `beneficiarios`, `objecion`, `*_enc`, `*_hash`, PII |
| `auditoria_seguro` | `action`, `outcome`, `correlation_id`, ids funcionales, estados y contadores | Sanitización por whitelist y truncado seguro | PII/PHI, listas completas, detalle económico granular |
| `dataset_seguro` | ids técnicos + métricas agregadas + estado/riesgo + contadores | `pendiente_tramo` por bucket | importes detallados por póliza, texto clínico, payloads completos |
| Panel ejecutivo campañas | `id_campania`, `titulo`, `criterio`, `tamano_estimado`, `motivo`, `accion_recomendada`, `cautela` | `ids_resumen` (cantidad) en lugar de lista completa | lista completa de oportunidades en vistas ejecutivas |
| Cartera postventa | `id_poliza`, `estado`, `titular_ref`, vigencia, contadores | `titular_ref=id_asegurado` en vez de nombre/documento | nombre/documento titular y lista de beneficiarios |
| Estado económico póliza | estado, riesgo, contadores de cuotas, motivo | `pendiente_tramo` (`0`, `(0,100)`, `[100,500)`, `>=500`) | `total_pendiente` exacto en vistas generales |

## Guardrails de implementación
- Módulo reusable: `clinicdesk/app/application/seguros/seguridad_observabilidad.py`.
- Rechazo por patrón de claves sensibles: documento, email, teléfono, dirección, titular, beneficiarios, objeciones, `payload`, `*_enc`, `*_hash`.
- Política safe-by-default: solo sale whitelist; lo demás se descarta.

## Cobertura de tests
- `tests/application/seguros/test_seguridad_observabilidad_seguro.py` valida:
  - whitelist de metadata segura,
  - fallo en contextos no soportados,
  - snapshots postventa/economía sin PII ni detalle económico excesivo,
  - resumen seguro de campañas,
  - payload de logging sin campos sensibles.

## Limitaciones honestas
- Este endurecimiento prioriza observabilidad y contratos de salida del módulo seguros.
- No sustituye controles globales de cifrado/reposo del resto del sistema.
