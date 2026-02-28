# Seguridad y manejo de datos sensibles (PII/PHI)

## Objetivo
Definir una política base de protección de datos para `clinicdesk` sin introducir todavía cifrado de base de datos completo (por ejemplo SQLCipher), preparando el siguiente PR de cifrado real.

## Alcance
Inventario y política sobre datos en tablas del esquema SQLite actual.

Fuente principal: `clinicdesk/app/infrastructure/sqlite/schema.sql`.

---

## 1) Inventario de PII/PHI por entidad/tabla

> Clasificación usada:
> - **PII**: datos de identificación personal.
> - **PHI**: datos de salud (incluye relación paciente-atención clínica y contenido clínico).

| Tabla | Campo | Clasificación | Sensibilidad | Uso operativo actual |
|---|---|---:|---:|---|
| `pacientes` | `tipo_documento`, `documento` | PII | Alta | Identificación única y búsquedas por documento |
| `pacientes` | `nombre`, `apellidos` | PII | Alta | Listados, UI, búsqueda textual |
| `pacientes` | `telefono`, `email`, `direccion` | PII | Alta | Contacto y búsqueda parcial |
| `pacientes` | `fecha_nacimiento` | PII/PHI contextual | Alta | Datos demográficos |
| `pacientes` | `num_historia` | PHI (identificador clínico) | Alta | Vinculación clínica |
| `pacientes` | `alergias`, `observaciones` | PHI | Crítica | Información clínica libre |
| `medicos` | `tipo_documento`, `documento` | PII | Alta | Identificación única |
| `medicos` | `nombre`, `apellidos` | PII | Media | Operación diaria/listados |
| `medicos` | `telefono`, `email`, `direccion`, `fecha_nacimiento` | PII | Media-Alta | Contacto/gestión |
| `medicos` | `num_colegiado` | PII profesional | Media | Validación y operación |
| `medicos` | `especialidad` | Dato profesional | Baja | Filtrado operativo |
| `personal` | `tipo_documento`, `documento` | PII | Alta | Identificación única |
| `personal` | `nombre`, `apellidos` | PII | Media | Operación diaria/listados |
| `personal` | `telefono`, `email`, `direccion`, `fecha_nacimiento` | PII | Media-Alta | Contacto/gestión |
| `personal` | `puesto`, `turno` | Dato laboral | Baja-Media | Operación |
| `citas` | `paciente_id`, `medico_id`, `sala_id`, `inicio`, `fin`, `estado` | PHI contextual | Alta | Agenda clínica y trazabilidad |
| `citas` | `motivo`, `notas`, `override_nota` | PHI | Crítica | Contenido clínico/operativo libre |
| `recetas` | `paciente_id`, `medico_id`, `fecha`, `estado`, `observaciones` | PHI | Alta-Crítica | Prescripción clínica |
| `receta_lineas` | `dosis`, `duracion_dias`, `instrucciones`, `estado` | PHI | Alta-Crítica | Detalle terapéutico |
| `dispensaciones` | `personal_id`, `fecha_hora`, `cantidad`, `observaciones`, `override_nota` | PHI + PII laboral | Alta-Crítica | Evidencia de administración |
| `incidencias` | `descripcion`, `nota_override`, referencias a paciente/receta/cita | PHI + PII laboral | Crítica | Auditoría clínica y seguridad |
| `ausencias_*` | `motivo`, `tipo`, fechas, ids personal/medico | PII laboral | Media | RRHH/operación |
| `movimientos_*` | `motivo`, `referencia`, `personal_id` | PII laboral / trazabilidad | Media | Auditoría logística |

---

## 2) Política de protección (cifrar / hashear / claro)

## Principios
1. **Minimización**: no almacenar más de lo necesario.
2. **Defensa en profundidad**: combinar control de acceso + cifrado por campo + logging seguro.
3. **Determinismo solo cuando aporte valor operativo** (búsqueda/igualdad).
4. **No romper UX/queries existentes en esta fase**.

## Matriz de decisión

| Tipo de dato | Decisión | Implementación propuesta (sin dependencias pesadas) | Justificación |
|---|---|---|---|
| Documento identificativo (`documento`) | **Hash + último4 en claro** | `HMAC-SHA256(pepper, documento_normalizado)` en columna nueva `documento_hash`; mantener `documento_last4` y/o `documento_masked` | Permite lookups exactos y reduce exposición de identificador completo |
| Email/teléfono (búsqueda exacta opcional) | **Hash para igualdad + claro temporal** | `email_hash`, `telefono_hash` + mantener temporalmente campo claro hasta migrar búsquedas | Permite transición gradual sin romper funcionalidades |
| Nombre/apellidos | **Claro (fase 1), cifrado en fase 2** | Mantener claro por alta dependencia de búsquedas `LIKE`; preparar índices/search alternativo | Cifrado fuerte rompería búsquedas textuales actuales |
| Dirección | **Cifrar** | Cifrado simétrico a nivel aplicación (AES-GCM/Fernet equivalente liviano) | No requiere búsqueda parcial en la mayoría de casos |
| Fecha nacimiento | **Cifrar** (o claro con restricción estricta) | Preferible cifrado por campo | Dato sensible con bajo requisito de búsqueda textual |
| `num_historia` | **Hash determinista + token público** | Hash para correlación interna; token visible separado para UI | Identificador clínico debe evitar exposición directa |
| PHI libre (`alergias`, `observaciones`, `motivo`, `notas`, `descripcion`, `instrucciones`, `override_nota`) | **Cifrar** | Cifrado por campo en aplicación; descifrado bajo necesidad | Riesgo alto por texto libre con datos clínicos/contextuales |
| IDs foráneos y estados operativos (`*_id`, `estado`, flags) | **Claro** | Sin cambios | Necesarios para integridad relacional/reporting |
| Timestamps (`fecha`, `fecha_hora`, `inicio`, `fin`) | **Claro** (fase 1) | Sin cambios iniciales | Críticos para agenda/reporting; evaluar tokenización temporal futura |

## Estado actual vs política
- Actualmente el esquema guarda los campos sensibles **en claro**.
- Ya existen transformaciones de higiene útiles para la política:
  - normalización de strings opcionales por `strip`;
  - validación básica de teléfono/email;
  - normalización de parámetros de búsqueda.

Estas transformaciones no cifran ni hashean, pero son precondiciones para que hashing/cifrado sea consistente (canonicalización antes de proteger).

---

## 3) Checklist accionable para el PR de cifrado real

## Diseño y migración
- [x] Definir módulo `common/crypto_field_protection.py` con interfaz estable (`encrypt/decrypt/hash_lookup`) para PACIENTES.
- [x] Introducir secret management mínimo por entorno (`CLINICDESK_CRYPTO_KEY`) y flag (`CLINICDESK_FIELD_CRYPTO`) para PACIENTES.
- [x] Crear migraciones SQL no destructivas para PACIENTES: columnas `*_hash`, `*_enc` (idempotentes en bootstrap).
- [x] Backfill incremental y reversible para PACIENTES (`scripts/crypto_migrate_patients.py`).

## Repositorios y casos de uso
- [ ] Canonicalizar dato antes de hash/cifrado (trim, casefold, normalización local definida).
- [x] Escribir en dual mode para PACIENTES con flag de activación y fallback legacy de lectura.
- [x] Leer preferentemente de protegido y fallback controlado a claro.
- [ ] Añadir feature flag `SECURITY_FIELD_PROTECTION_ENABLED`.

## Seguridad operativa
- [ ] Prohibir logging de payloads sensibles en repositorios/casos de uso.
- [ ] Añadir rotación de claves (versión de clave por registro/campo).
- [ ] Definir estrategia de recuperación ante pérdida de clave.

## Calidad y compliance
- [ ] Tests unitarios: determinismo de hash, roundtrip cifrado, key versioning.
- [ ] Tests integración: búsquedas por documento/email/teléfono en modo transición.
- [ ] Test de no-regresión: exportaciones CSV sin filtrar datos cifrados crudos.
- [ ] Checklist DPIA/LOPD-GDD/GDPR interno (base legal, retención, minimización).

---

## 4) Decisiones explícitas para esta fase
- ✅ PACIENTES cifrado implementado (incremental por campo con feature flag).
- ✅ Escritura endurecida en modo cifrado: en PACIENTES solo se persiste `*_enc + *_hash` para `documento/email/telefono/direccion`.
- No se introduce SQLCipher todavía.
- No se agregan dependencias criptográficas pesadas en este PR.
- Este PR documenta política y valida precondiciones de transformación ya existentes para facilitar la implementación del cifrado real en el siguiente ciclo.

---

## 5) How-to migrate (PACIENTES)

### Prerrequisitos
- Exportar clave de cifrado de campo (`CLINICDESK_CRYPTO_KEY`).
- Activar modo de cifrado por campo (`CLINICDESK_FIELD_CRYPTO=1`).
- Ejecutar sobre una base con esquema aplicado (el bootstrap añade columnas `*_enc`/`*_hash` en `pacientes`).

### Paso 1 — Backfill seguro (dual-write)
Este paso rellena `documento_enc/documento_hash`, `telefono_enc/telefono_hash`, `email_enc/email_hash`, `direccion_enc/direccion_hash` sin borrar legado.

```bash
python -m scripts.crypto_migrate_patients \
  --db-path ./data/clinicdesk.sqlite
```

### Paso 2 — Limpieza de columnas legacy (opcional, irreversible)
Solo permitido para rutas dentro de `./data` y requiere confirmación explícita.

```bash
python -m scripts.crypto_migrate_patients \
  --db-path ./data/clinicdesk.sqlite \
  --wipe-legacy \
  --confirm-wipe WIPE-LEGACY
```

### Controles de seguridad del script
- Nunca emite payloads sensibles por consola (solo métricas agregadas por logging).
- Si se solicita `--wipe-legacy`, bloquea rutas fuera de `./data`.
- Si falta `CLINICDESK_FIELD_CRYPTO=1` o `CLINICDESK_CRYPTO_KEY`, aborta antes de escribir.
