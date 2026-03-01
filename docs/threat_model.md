# Threat model (desktop) — ClinicDesk

## Alcance

Aplicación desktop con base SQLite local y datos clínicos/PII. El foco es confidencialidad e integridad de datos sensibles en endpoint de puesto clínico.

## Activos críticos

- Datos personales y clínicos (pacientes, personal, médicos).
- Credenciales y sesiones de usuario.
- Clave de cifrado por campo (`CLINICDESK_CRYPTO_KEY`).
- Logs operativos (riesgo de fuga indirecta).

## Amenazas principales en entorno desktop

1. **Acceso local no autorizado al equipo**
   - Robo del dispositivo, sesión desbloqueada o usuario compartido.
2. **Exfiltración de base SQLite en reposo**
   - Copia de `.db`, `-wal`, backups o snapshots.
3. **Exposición de secretos por mala operación**
   - Clave en texto plano en scripts, ficheros sin permisos o historiales.
4. **Abuso interno por exceso de privilegios**
   - Operaciones fuera de rol o consulta indebida.
5. **Filtrado de PII por logs/errores**
   - Stack traces o eventos con datos sensibles.
6. **Manipulación local del entorno**
   - Variables de entorno incorrectas, desactivación accidental de controles.

## Mitigaciones ya implementadas

- **Autenticación y control de acceso por roles** para reducir acceso no autorizado.
- **Redacción de logs** para limitar exposición de datos sensibles en observabilidad.
- **Cifrado por campo en reposo** para PII sensible en tablas objetivo.
- **Validación de startup**: si `CLINICDESK_FIELD_CRYPTO=1` sin `CLINICDESK_CRYPTO_KEY`, arranque bloqueado con mensaje claro.
- **Prácticas de inicialización SQLite** (WAL + pragmas operativos) y flujo controlado de bootstrap.

## Riesgos aceptados (estado actual)

1. **Compromiso de endpoint autenticado**
   - Si el atacante controla una sesión válida, puede leer datos en uso.
2. **Custodia de clave dependiente de operación local**
   - Sin KMS central obligatorio, la madurez depende del despliegue.
3. **Rotación de clave no automatizada**
   - Cambio de clave requiere plan operativo/migración explícita.
4. **Cobertura parcial de hardening de secretos en OS**
   - DPAPI/keystore recomendado, no forzado por producto.

## Suposiciones

- El sistema operativo y políticas corporativas aportan hardening base (cuentas, bloqueo de pantalla, disco cifrado, antivirus/EDR).
- El equipo operativo mantiene backups cifrados y procedimiento documentado de recuperación de clave.

## Próximos pasos recomendados

- Introducir estrategia de rotación con `key_id` y keyring.
- Estandarizar almacenamiento seguro de clave por SO (DPAPI/Keychain/libsecret según plataforma).
- Añadir controles de auditoría orientados a acceso a datos sensibles.
