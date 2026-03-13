# Minimización y no-fuga de datos en salidas

Este documento define la matriz operativa aplicada en código para endurecer rutas de salida transversales.

## Contextos y contrato

| Contexto | Campos permitidos | Redacción obligatoria | Nunca exponer |
|---|---|---|---|
| UI operativa interna | ids operativos, estado, horario, flags | No aplica por defecto | `*_enc`, `*_hash` |
| API demo/read-only | campos de listado de citas/pacientes | `paciente`, `documento`, `telefono`, `email` | `*_enc`, `*_hash`, dirección, observaciones, notas clínicas |
| Export analítico/BI | métricas, versiones, score, labels, contadores | No aplica | PII/PHI directa y columnas técnicas |
| Recordatorios/contacto | `cita_id`, fecha/hora, canal, contacto mínimo | No aplica (contexto operativo) | `*_enc`, `*_hash`, dirección, alergias, observaciones |
| Auditoría | action/outcome, correlación, reason codes, conteos | usuario cuando corresponda | documento, email, teléfono, dirección, `*_enc`, `*_hash` |
| Logging técnico | action, run_id, status, error_code, conteos | No aplica | payloads completos, PII/PHI, `*_enc`, `*_hash` |

## Rutas endurecidas en esta iteración

- **API read-only** (`/api/v1/citas`, `/api/v1/pacientes`): serialización por whitelist explícita con redacción centralizada.
- **Demo ML read models** (`list_doctors`, `list_patients`, `list_appointments`, `list_incidences`): sanitización de campos de salida para evitar fuga de documento/teléfono/motivo/descripcion libre.
- **Compatibilidad**: se mantienen nombres de campos de contrato para no romper consumidores.

## Extensión del patrón

1. Crear serializador por contexto (evitar sanitizer genérico opaco).
2. Definir whitelist de claves de salida antes de mapear datos.
3. Redactar solo los campos sensibles permitidos en ese contexto.
4. Añadir tests de no-fuga con asserts de:
   - ausencia de `*_enc`/`*_hash`,
   - estabilidad de claves de salida,
   - redacción de PII/PHI esperada.

## Limitaciones actuales

- El hardening se aplicó a rutas de mayor exposición transversal (API demo + read models demo ML).
- Queda como siguiente paso extender el mismo patrón a nuevas salidas públicas/semi-públicas que aparezcan en módulos futuros.
