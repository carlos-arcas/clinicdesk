# Índices SQLite para búsquedas y filtros

## Objetivo
Optimizar búsquedas y listados frecuentes sobre columnas usadas en filtros (`WHERE`) y ordenación (`ORDER BY`), con foco en:

- `nombre`
- `apellidos`
- `documento`
- `estado`
- `fecha` (`inicio` / `fecha_hora`)

## Queries observadas
Los listados y búsquedas de:

- pacientes, médicos y personal filtran por `activo` y ordenan por `apellidos, nombre`.
- citas filtran por `activo`, `estado` y rango temporal en `inicio`; además ordenan por `inicio`.
- incidencias filtran por `activo`, `estado` y rango de `fecha_hora`; además ordenan por `fecha_hora`.

## Índices añadidos
Se agregaron índices idempotentes (`CREATE INDEX IF NOT EXISTS`) en `schema.sql`:

- `idx_pacientes_activo_apellidos_nombre` sobre `pacientes(activo, apellidos, nombre)`.
- `idx_medicos_activo_apellidos_nombre` sobre `medicos(activo, apellidos, nombre)`.
- `idx_personal_activo_apellidos_nombre` sobre `personal(activo, apellidos, nombre)`.
- `idx_citas_activo_estado_inicio` sobre `citas(activo, estado, inicio)`.
- `idx_incidencias_activo_estado_fecha` sobre `incidencias(activo, estado, fecha_hora)`.

## Compatibilidad y migración
No se rompe DB existente porque:

- El esquema usa `CREATE INDEX IF NOT EXISTS`.
- El bootstrap actual ejecuta `schema.sql` de forma idempotente, por lo que los índices se crean automáticamente también para bases ya existentes en el próximo arranque con `apply_schema=True`.

## Verificación
En tests se valida la existencia de los índices en una DB de pruebas mediante:

- `PRAGMA index_list('<tabla>')`
