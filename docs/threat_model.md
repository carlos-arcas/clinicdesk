# Threat model ligero (STRIDE) — ClinicDesk

## Alcance

Aplicación de escritorio con base SQLite local. Este documento cubre amenazas prácticas del repo sobre activos de datos, configuración y distribución.

## Activos principales

- Base de datos local SQLite (`.db`, `-wal`, `-shm`).
- Preferencias UX en JSON (`user_prefs.json`).
- Logs operativos y de error.
- Claves/variables de cifrado de campo (`CLINICDESK_CRYPTO_KEY`).
- Exportaciones CSV (incluyendo escenarios con PII).
- Artefacto de release (`clinicdesk.zip`).

## Superficies de ataque consideradas

- Inputs de UI.
- QuickSearch y persistencia de última búsqueda.
- Exportaciones y acciones sensibles.
- Seed/reset de demo.
- Rutas de filesystem (DB, exports, prefs).
- Variables de entorno.
- SQLite (integridad/consistencia local).

## STRIDE por superficie

| Superficie | Amenaza (STRIDE) | Impacto | Mitigación existente en repo | Gaps abiertos |
|---|---|---|---|---|
| UI inputs | Tampering / DoS por payloads excesivos | Estados corruptos o bloqueo de flujo | Validaciones de casos de uso + saneamiento de búsquedas antes de persistir preferencias | Endurecer límites homogéneos en todos los formularios avanzados |
| QuickSearch | Information Disclosure por persistir PII en prefs | Fuga local de PII en disco | `sanitize_search_text` bloquea emails/teléfonos/direcciones y longitudes abusivas | Añadir auditoría específica de intentos bloqueados (sin PII) |
| Export CSV | Elevation of Privilege / Information Disclosure | Exfiltración de datos sensibles | RBAC + confirmación explícita + flag de entorno para PII (`CLINICDESK_EXPORT_PII`) | Firma/verificación de integridad del CSV exportado |
| Seed/reset | Tampering / Repudiation | Borrado accidental o abuso operativo | Confirmación obligatoria + `reason_code` + safe paths para reset | Flujo formal de aprobación dual para entornos no demo |
| Filesystem paths | Tampering | Escritura/lectura fuera de rutas esperadas | Validación de rutas seguras para reset y defaults controlados | Unificar política para todos los módulos que escriben disco |
| Env vars | Spoofing / Misconfiguration | Arranque inseguro o cifrado mal configurado | Validación de startup cuando se exige cifrado de campo | Integrar chequeo de entorno endurecido por perfil (dev/demo/prod local) |
| SQLite | Tampering / Information Disclosure | Lectura no autorizada o alteración local | Cifrado de campo para PII + pragmas SQLite + tests de seguridad | Backup cifrado y política de rotación más automatizada |

## No hacemos (explícito)

- No hay autenticación remota federada (OIDC/SAML).
- No hay modelo multiusuario real en red con aislamiento fuerte por tenant.
- No se ofrece garantía de hardening del sistema operativo desde la app.
- No hay HSM/KMS obligatorio embebido en el producto.

## Mitigaciones ya implementadas

- Hardening de operaciones sensibles (RBAC, confirmaciones, safe paths). Ver [security_hardening.md](./security_hardening.md).
- Gestión/rotación operativa de claves de cifrado de campo. Ver [security_keys.md](./security_keys.md).
- Política de persistencia UX sin PII en preferencias. Ver [ux_preferences.md](./ux_preferences.md).
- Evidencia de calidad y seguridad para evaluación técnica. Ver documentación principal del producto en `README.md`.

## Roadmap de seguridad (máximo 3)

1. Firmar artefactos de release (`clinicdesk.zip`) y verificar firma en distribución.
2. Añadir backup cifrado con procedimiento de restauración probado.
3. Extender controles RBAC a más operaciones transversales de administración.
