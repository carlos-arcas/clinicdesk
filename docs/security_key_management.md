# Gestión de claves de cifrado por campo

## Variable de entorno requerida

ClinicDesk usa `CLINICDESK_CRYPTO_KEY` cuando `CLINICDESK_FIELD_CRYPTO=1` para cifrar campos sensibles en reposo.

**Formato recomendado**:
- **Base64** para facilitar transporte seguro en variables de entorno.
- **32 bytes aleatorios** (256 bits) como material de entrada.

Ejemplo de valor esperado (Base64 de 32 bytes):
- `Q3YwN2Q0c1l3bDVaTnJGR3B0WVp6R2RJejVtUXV0QllkQ2k=`

> Nota: la implementación actual deriva claves internas desde el string configurado. Aunque no exige longitud fija, para compliance operativo se recomienda estandarizar a 32 bytes aleatorios codificados en Base64.

## Cómo generar la clave

### Opción recomendada (Python, multiplataforma)

```bash
python -c "import os,base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

### Opción OpenSSL

```bash
openssl rand -base64 32
```

## Dónde almacenarla según sistema operativo

## Windows (recomendado para desktop)

Persistir como variable de entorno de usuario:

```powershell
setx CLINICDESK_CRYPTO_KEY "<TU_CLAVE_BASE64>"
setx CLINICDESK_FIELD_CRYPTO "1"
```

Aplicará en nuevas sesiones de terminal/launcher.

## Linux/macOS

- Entorno de shell (`~/.bashrc`, `~/.zshrc`) si el riesgo operativo es bajo.
- Mejor práctica: archivo local con permisos restrictivos (`chmod 600`) y carga controlada por launcher.

Ejemplo:

```bash
export CLINICDESK_CRYPTO_KEY='<TU_CLAVE_BASE64>'
export CLINICDESK_FIELD_CRYPTO=1
```

## Fichero local (opción operativa)

Si se usa fichero local de secretos:
- Guardarlo fuera del repositorio.
- Permisos mínimos del SO.
- Nunca versionarlo ni incluirlo en backups no cifrados.

## DPAPI (Windows, opcional)

Para endurecer postura local en Windows se puede:
- almacenar la clave cifrada con **DPAPI** ligada al usuario/máquina,
- descifrar en el launcher antes de iniciar ClinicDesk,
- inyectar el valor en `CLINICDESK_CRYPTO_KEY` en memoria.

Estado actual: **no obligatorio en producto**, pero recomendado para despliegues con requisitos reforzados.

## Rotación de clave

## Estado actual

- No existe rotación online automática por versión de clave.
- El cifrado por campo usa una única clave activa vía `CLINICDESK_CRYPTO_KEY`.
- Cambiar la clave sin migración rompe descifrado de datos previos.

## Plan de rotación (propuesto)

1. Introducir `key_id` por registro/campo cifrado.
2. Soportar keyring local (`activo + legacy`).
3. Re-cifrado por lotes con ventana operativa y métricas de progreso.
4. Retirada de clave legacy al 100% de cobertura de migración.

## Recuperación / pérdida de clave

Si se pierde `CLINICDESK_CRYPTO_KEY`:
- los campos cifrados existentes **no pueden descifrarse**,
- la aplicación no debe operar en modo cifrado sin clave,
- sólo es posible recuperar datos desde backup que incluya clave válida o proceso de escrow externo.

Implicación compliance: tratar la custodia de clave como activo crítico (backup seguro, doble control, procedimiento de recuperación probado).
