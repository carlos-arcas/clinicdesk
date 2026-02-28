# Índices SQLite para búsquedas y filtros

## Objetivo
Optimizar listados/búsquedas con filtros y ordenaciones frecuentes sobre:
- `nombre`
- `apellidos`
- `documento`
- `estado`
- `fecha` / `fecha_hora` / `inicio`

## Columnas detectadas en WHERE / ORDER BY

### Pacientes (`pacientes`)
- `WHERE activo = ?`
- filtros por texto que incluyen `nombre`, `apellidos`, `documento`
- `ORDER BY apellidos, nombre`

### Médicos (`medicos`)
- `WHERE activo = ?`
- filtros por texto que incluyen `nombre`, `apellidos`, `documento`
- `ORDER BY apellidos, nombre`

### Personal (`personal`)
- `WHERE activo = ?`
- filtros por texto que incluyen `nombre`, `apellidos`, `documento`
- `ORDER BY apellidos, nombre`

### Citas (`citas`)
- `WHERE activo = 1`
- filtro por `estado`
- filtros de fecha sobre `inicio`
- `ORDER BY inicio`

### Recetas (`recetas`)
- `WHERE activo = 1`
- filtro por `estado`
- rangos por `fecha`
- `ORDER BY fecha DESC`

### Incidencias (`incidencias`)
- `WHERE activo = 1`
- filtro por `estado`
- rangos por `fecha_hora`
- `ORDER BY fecha_hora DESC`

## Índices añadidos

Se añadieron índices compuestos para cubrir patrones `WHERE + ORDER BY`:

- `idx_pacientes_activo_apellidos_nombre` en `(activo, apellidos, nombre)`
- `idx_medicos_activo_apellidos_nombre` en `(activo, apellidos, nombre)`
- `idx_personal_activo_apellidos_nombre` en `(activo, apellidos, nombre)`
- `idx_citas_activo_estado_inicio` en `(activo, estado, inicio)`
- `idx_recetas_activo_estado_fecha` en `(activo, estado, fecha DESC)`
- `idx_incidencias_activo_estado_fecha` en `(activo, estado, fecha_hora DESC)`

## Aplicación en bootstrap/migración

Para no romper bases existentes:

1. Se declararon en `schema.sql` con `CREATE INDEX IF NOT EXISTS`.
2. Además se ejecutan explícitamente en bootstrap/migración mediante `_migrate_performance_indexes(...)` tanto en:
   - `clinicdesk/app/bootstrap.py`
   - `clinicdesk/app/infrastructure/sqlite/db.py`

Esto permite que una DB ya creada reciba los índices al reiniciar la app aunque no se recree la estructura desde cero.
