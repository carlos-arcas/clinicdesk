# Gestión de claves de cifrado de campo (`CLINICDESK_CRYPTO_KEY`)

Esta guía define el flujo operativo para generar, validar y rotar claves sin pérdida de datos.

## Variables de entorno

- `CLINICDESK_CRYPTO_KEY`: clave **activa** (obligatoria).
- `CLINICDESK_CRYPTO_KEY_PREVIOUS`: clave **anterior** (opcional, solo transición).

Política de uso:

- `encrypt(...)` cifra siempre con `CLINICDESK_CRYPTO_KEY`.
- `decrypt(...)` intenta primero clave activa y, ante `invalid tag`, reintenta con `CLINICDESK_CRYPTO_KEY_PREVIOUS`.
- Tokens no versionados (`legacy`) se devuelven tal cual para compatibilidad retroactiva.

## Generación segura de clave

```bash
python -m scripts.security_cli generate-key
```

Notas:

- La clave se imprime por `stdout` para facilitar piping a secret managers.
- Se muestra advertencia de seguridad por `stderr`.
- **Nunca** commitear ni compartir la clave en tickets/chat/logs.

## Validación rápida de clave

```bash
export CLINICDESK_CRYPTO_KEY='<CLAVE_SEGURA>'
python -m scripts.security_cli check-key
```

La validación revisa mínimos de longitud/entropía simple.

## Procedimiento de rotación (paso a paso)

1. Generar nueva clave con `generate-key` y guardarla en tu gestor de secretos.
2. Configurar entorno de rotación:
   - `CLINICDESK_CRYPTO_KEY=<NUEVA_CLAVE>`
   - `CLINICDESK_CRYPTO_KEY_PREVIOUS=<CLAVE_ANTERIOR>`
3. Ejecutar verificación sin cambios:

```bash
python -m scripts.security_cli rotate-key --dry-run --db-path data/clinicdesk.sqlite
```

4. Aplicar recifrado en base:

```bash
python -m scripts.security_cli rotate-key --apply --db-path data/clinicdesk.sqlite
```

5. Verificar lectura funcional de pacientes.
6. Mantener `CLINICDESK_CRYPTO_KEY_PREVIOUS` solo durante ventana de transición.
7. Retirar `CLINICDESK_CRYPTO_KEY_PREVIOUS` al cerrar la rotación.

## Auditoría y no filtrado

- `rotate-key --apply` registra evento de auditoría `CRYPTO_ROTATE` en `auditoria_eventos`.
- La auditoría guarda métricas operativas (conteos), sin PII y sin claves.
- Las salidas CLI nunca imprimen valores PII ni claves.
