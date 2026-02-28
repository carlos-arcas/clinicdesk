# Structural Quality Report

## 1) Resumen
- total_files_scanned: **128**
- violations_count: **5**
- blocking_violations_count: **5**
- top_hotspots: **3**

### Umbrales aplicados
- max_file_loc: 400
- max_function_loc: 60
- max_class_loc: 200
- max_cc: 10
- max_avg_cc_per_file: 6
- max_hotspots: 0

## 2) Violaciones por tipo

### Files over LOC
- `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py` :: `<file>` -> 409.00 > 400.00 (allowlisted: no)

### Functions over LOC
- `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py` :: `_persist_demo_data` -> 65.00 > 60.00 (allowlisted: no)

### Classes over LOC
- `clinicdesk/app/infrastructure/sqlite/repos_pacientes.py` :: `PacientesRepository` -> 261.00 > 200.00 (allowlisted: no)
- `clinicdesk/app/infrastructure/sqlite/repos_personal.py` :: `PersonalRepository` -> 216.00 > 200.00 (allowlisted: no)
- `clinicdesk/app/infrastructure/sqlite/repos_recetas.py` :: `RecetasRepository` -> 219.00 > 200.00 (allowlisted: no)

### Functions over CC
- Ninguna.

## 3) Hotspots (top 10)

| file | file_loc | max_cc | avg_cc | worst_function | score | allowlisted? |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| `scripts/structural_gate.py` | 418 | 24 | 3.17 | analyze_repo (cc=24, loc=82) | 1.86 | sí |
| `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py` | 409 | 9 | 2.31 | persist_incidences_rows (cc=9, loc=48) | 0.95 | no |
| `scripts/ml_cli.py` | 463 | 8 | 1.84 | main (cc=8, loc=24) | 0.94 | sí |

## 4) Recomendaciones automáticas

- `scripts/structural_gate.py` / `analyze_repo`: extrae funciones puras para separar ramas condicionales y bajar CC.
- `scripts/structural_gate.py`: divide el módulo en submódulos cohesivos por bounded context para reducir LOC del archivo.
- `scripts/structural_gate.py` / `analyze_repo`: introduce use cases/ports para desacoplar orquestación de detalles de infraestructura.
- `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py` / `persist_incidences_rows`: extrae funciones puras para separar ramas condicionales y bajar CC.
- `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py`: divide el módulo en submódulos cohesivos por bounded context para reducir LOC del archivo.
- `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py` / `persist_incidences_rows`: introduce use cases/ports para desacoplar orquestación de detalles de infraestructura.
- `scripts/ml_cli.py` / `main`: extrae funciones puras para separar ramas condicionales y bajar CC.
- `scripts/ml_cli.py`: divide el módulo en submódulos cohesivos por bounded context para reducir LOC del archivo.
- `scripts/ml_cli.py` / `main`: introduce use cases/ports para desacoplar orquestación de detalles de infraestructura.

## Allowlist / deuda controlada

- `scripts/structural_gate.py` -> overrides: max_cc=30, max_function_loc=100, max_class_loc=None, max_file_loc=500, max_avg_cc_per_file=None; reason: Deuda temporal aceptada: script de tooling, fuera del core clínico
- `scripts/ml_cli.py` -> overrides: max_cc=None, max_function_loc=None, max_class_loc=None, max_file_loc=500, max_avg_cc_per_file=None; reason: Deuda temporal aceptada: CLI de soporte para flujos ML
