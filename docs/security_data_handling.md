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
- Estado incremental (actual): `pacientes.documento/email/telefono/direccion` ya soporta cifrado por campo con feature-flag `CLINICDESK_FIELD_CRYPTO` y hashes de lookup exacto.
- Ya existen transformaciones de higiene útiles para la política:
  - normalización de strings opcionales por `strip`;
  - validación básica de teléfono/email;
  - normalización de parámetros de búsqueda.

Estas transformaciones no cifran ni hashean, pero son precondiciones para que hashing/cifrado sea consistente (canonicalización antes de proteger).

---

## 3) Checklist accionable para el PR de cifrado real

## Diseño y migración
- [x] Definido módulo `clinicdesk/app/common/crypto_field_protection.py` con `encrypt/decrypt/hash_lookup`.
- [x] Secret management por entorno: `CLINICDESK_FIELD_KEY`, `CLINICDESK_FIELD_HASH_KEY` (nunca en repo).
- [x] Migración incremental no destructiva para `pacientes`: `documento/email/telefono/direccion` con columnas `*_enc` y `*_hash` requeridas para lookup exacto.
- [ ] Backfill incremental y reversible (batch + checkpoints).

## Repositorios y casos de uso
- [x] Canonicalización antes de hash (trim/casefold/NFKC y normalización de teléfono para lookup).
- [x] Escritura dual de columnas protegidas (`*_enc` + `*_hash`) con fallback legacy por feature-flag.
- [x] Lectura preferente de `*_enc` cuando el flag está activo; fallback a columnas legacy si no.
- [x] Feature-flag activo: `CLINICDESK_FIELD_CRYPTO=0/1`.

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
- No se introduce SQLCipher todavía.
- No se agregan dependencias criptográficas pesadas en este PR.
- Este PR documenta política y valida precondiciones de transformación ya existentes para facilitar la implementación del cifrado real en el siguiente ciclo.


## 5) Limitaciones conocidas de esta fase incremental
- Búsqueda libre (`LIKE`) se mantiene sin romper, pero cuando `CLINICDESK_FIELD_CRYPTO=1` pierde coincidencia parcial sobre `documento/email/telefono` porque esas columnas quedan sin plaintext.
- Búsquedas exactas de `documento/email/telefono` migran a `*_hash` para mantener funcionalidad sin exponer PII en reposo.
