# Security hardening: operaciones peligrosas

## Operaciones protegidas

Se endurecen los flujos de **seed demo / reset / exportación sensible** con tres guardarraíles obligatorios:

1. **RBAC**
   - Seed demo requiere `Action.DEMO_SEED`.
   - Export CSV de auditoría requiere `Action.AUDITORIA_EXPORTAR_CSV`.
2. **Safe paths** para rutas de DB en reset.
3. **Confirmación explícita** para ejecutar acciones destructivas o con PII.

## Safe paths para reset de DB

`es_ruta_db_segura_para_reset(path)` permite reset solo si:

- la ruta está dentro de roots seguras (por defecto `./data` y `./tmp`), o
- la ruta contiene `demo` o `test`.

Además, bloquea:

- `/` (raíz),
- `Path.home()`,
- rutas sin extensión de DB esperada (`.db`, `.sqlite`, `.sqlite3`).

## Confirmación explícita requerida

### Seed / reset demo

Para reset/seed con borrado (`reset_db=True`), se exige:

- `confirmar_reset=True` **o**
- `confirmacion="RESET-DEMO"`.

Sin confirmación, se rechaza con `reason_code="confirmation_required"`.

### Exportación sensible con PII

Si se solicita `incluir_pii=True`, se exige:

- variable `CLINICDESK_EXPORT_PII=1`,
- rol `ADMIN`,
- `confirmacion="EXPORT-PII"`.

## Auditoría obligatoria (sin PII)

Todos los intentos se auditan (`ok`/`fail`) con `reason_code`, evitando PII en metadata.

## Variables de entorno

- `CLINICDESK_SAFE_DB_ROOTS` (default: `data;tmp`)
  - Lista `;`-separada de roots seguras para reset de DB.
- `CLINICDESK_EXPORT_PII` (default: `0`)
  - `0`: bloquea exportación solicitada con PII.
  - `1`: habilita, pero mantiene requisitos de ADMIN + confirmación explícita.


## Referencias

- [Gestión de claves de cifrado](./security_keys.md)


## Guardrails de observabilidad segura (Fase 3)

Se añade contrato explícito para metadata operativa en auditoría:

- Implementación central: `clinicdesk/app/application/auditoria/metadata_segura.py`.
- Estrategia por **allowlist de claves** (`CLAVES_METADATA_AUDITORIA_PERMITIDAS`).
- Bloqueo explícito de claves sensibles (PII/PHI y columnas técnicas `*_enc` / `*_hash`).
- Redacción automática de valores string con `redactar_texto_pii`.

### Reglas operativas

Permitido en metadata de auditoría:
- ids técnicos (`cita_id`, `medico_id`, `sala_id`, `incidencia_id`),
- contadores y métricas agregadas,
- `reason_code`, `error_type`, `outcome`, trazabilidad por `correlation_id`.

No permitido:
- documento/email/teléfono/dirección,
- notas clínicas, observaciones o campos libres con PHI,
- cualquier clave `*_enc` o `*_hash`.

### Guardrail anti-regresión

El chequeo `scripts/quality_gate_components/pii_guardrail.py` ahora detecta además:
- claves sensibles dentro de `extra={...}` en llamadas `logger.*`,
- claves sensibles en `metadata={...}` en llamadas `.registrar(...)` de auditoría.

Objetivo: impedir reintroducción accidental de PII/PHI en telemetría operativa y auditoría técnica.
