# Structural Quality Report

## 1) Resumen
- total_files_scanned: **166**
- violations_count: **0**
- blocking_violations_count: **0**
- top_hotspots: **0**

### Umbrales aplicados
- max_file_loc: 400
- max_function_loc: 60
- max_class_loc: 200
- max_cc: 10
- max_avg_cc_per_file: 6
- max_hotspots: 0

## 2) Violaciones por tipo

### Files over LOC
- Ninguna.

### Functions over LOC
- Ninguna.

### Classes over LOC
- Ninguna.

### Functions over CC
- Ninguna.

## 3) Hotspots (top 10)

| file | file_loc | max_cc | avg_cc | worst_function | score | allowlisted? |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| n/a | 0 | 0 | 0.00 | n/a | 0.00 | no |

## 4) Recomendaciones automáticas

- No hay hotspots activos.

## Allowlist / deuda controlada

- `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py` -> overrides: max_cc=None, max_function_loc=80, max_class_loc=None, max_file_loc=450, max_avg_cc_per_file=None; reason: Deuda temporal aceptada: seeding demo concentrado en un módulo legado
- `clinicdesk/app/infrastructure/sqlite/repos_pacientes.py` -> overrides: max_cc=None, max_function_loc=None, max_class_loc=300, max_file_loc=None, max_avg_cc_per_file=None; reason: Deuda temporal aceptada: repositorio legacy mientras se completa partición por mixins
- `clinicdesk/app/infrastructure/sqlite/repos_personal.py` -> overrides: max_cc=None, max_function_loc=None, max_class_loc=240, max_file_loc=None, max_avg_cc_per_file=None; reason: Deuda temporal aceptada: repositorio legacy pendiente de segmentación
- `clinicdesk/app/infrastructure/sqlite/repos_recetas.py` -> overrides: max_cc=None, max_function_loc=None, max_class_loc=230, max_file_loc=None, max_avg_cc_per_file=None; reason: Deuda temporal aceptada: refactor diferido por compatibilidad con UI
