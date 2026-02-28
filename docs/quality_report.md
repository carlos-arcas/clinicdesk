# Structural Quality Report

## 1) Resumen
- total_files_scanned: **214**
- violations_count: **38**
- blocking_violations_count: **38**
- top_hotspots: **10**

### Umbrales aplicados
- max_file_loc: 400
- max_function_loc: 60
- max_class_loc: 200
- max_cc: 10
- max_avg_cc_per_file: 6
- max_hotspots: 0

## 2) Violaciones por tipo

### Files over LOC
- `clinicdesk/app/application/csv/csv_service.py` :: `<file>` -> 490.00 > 400.00 (allowlisted: no)
- `clinicdesk/app/domain/modelos.py` :: `<file>` -> 416.00 > 400.00 (allowlisted: no)
- `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py` :: `<file>` -> 412.00 > 400.00 (allowlisted: no)
- `clinicdesk/app/pages/demo_ml/page.py` :: `<file>` -> 418.00 > 400.00 (allowlisted: no)
- `scripts/ml_cli.py` :: `<file>` -> 463.00 > 400.00 (allowlisted: no)
- `scripts/structural_gate.py` :: `<file>` -> 418.00 > 400.00 (allowlisted: no)

### Functions over LOC
- `clinicdesk/app/application/usecases/ajustar_stock_material.py` :: `AjustarStockMaterialUseCase.execute` -> 97.00 > 60.00 (allowlisted: no)
- `clinicdesk/app/application/usecases/ajustar_stock_medicamento.py` :: `AjustarStockMedicamentoUseCase.execute` -> 95.00 > 60.00 (allowlisted: no)
- `clinicdesk/app/application/usecases/crear_cita.py` :: `CrearCitaUseCase.execute` -> 81.00 > 60.00 (allowlisted: no)
- `clinicdesk/app/application/usecases/dispensar_medicamento.py` :: `DispensarMedicamentoUseCase.execute` -> 113.00 > 60.00 (allowlisted: no)
- `clinicdesk/app/application/usecases/seed_demo_data.py` :: `SeedDemoData.execute` -> 65.00 > 60.00 (allowlisted: no)
- `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py` :: `DemoDataSeeder.persist` -> 71.00 > 60.00 (allowlisted: no)
- `clinicdesk/app/infrastructure/sqlite/repos_incidencias.py` :: `IncidenciasRepository.search` -> 65.00 > 60.00 (allowlisted: no)
- `clinicdesk/app/pages/incidencias/page.py` :: `PageIncidencias._build_ui` -> 63.00 > 60.00 (allowlisted: no)
- `clinicdesk/app/queries/dispensaciones_queries.py` :: `DispensacionesQueries.list` -> 86.00 > 60.00 (allowlisted: no)
- `clinicdesk/app/queries/incidencias_queries.py` :: `IncidenciasQueries.list` -> 98.00 > 60.00 (allowlisted: no)
- `scripts/structural_gate.py` :: `analyze_repo` -> 82.00 > 60.00 (allowlisted: no)
- `scripts/structural_gate.py` :: `generate_report` -> 85.00 > 60.00 (allowlisted: no)

### Classes over LOC
- `clinicdesk/app/application/csv/csv_service.py` :: `CsvService` -> 458.00 > 200.00 (allowlisted: no)
- `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py` :: `DemoDataSeeder` -> 307.00 > 200.00 (allowlisted: no)
- `clinicdesk/app/infrastructure/sqlite/repos_citas.py` :: `CitasRepository` -> 233.00 > 200.00 (allowlisted: no)
- `clinicdesk/app/infrastructure/sqlite/repos_incidencias.py` :: `IncidenciasRepository` -> 208.00 > 200.00 (allowlisted: no)
- `clinicdesk/app/infrastructure/sqlite/repos_pacientes.py` :: `PacientesRepository` -> 261.00 > 200.00 (allowlisted: no)
- `clinicdesk/app/infrastructure/sqlite/repos_personal.py` :: `PersonalRepository` -> 216.00 > 200.00 (allowlisted: no)
- `clinicdesk/app/infrastructure/sqlite/repos_recetas.py` :: `RecetasRepository` -> 219.00 > 200.00 (allowlisted: no)
- `clinicdesk/app/pages/demo_ml/page.py` :: `PageDemoML` -> 362.00 > 200.00 (allowlisted: no)
- `clinicdesk/app/pages/materiales/page.py` :: `PageMateriales` -> 246.00 > 200.00 (allowlisted: no)
- `clinicdesk/app/pages/medicamentos/page.py` :: `PageMedicamentos` -> 248.00 > 200.00 (allowlisted: no)

### Functions over CC
- `clinicdesk/app/application/csv/csv_io.py` :: `read_csv` -> 13.00 > 10.00 (allowlisted: no)
- `clinicdesk/app/application/csv/csv_service.py` :: `CsvService._format_row_error` -> 11.00 > 10.00 (allowlisted: no)
- `clinicdesk/app/application/usecases/ajustar_stock_material.py` :: `AjustarStockMaterialUseCase.execute` -> 25.00 > 10.00 (allowlisted: no)
- `clinicdesk/app/application/usecases/ajustar_stock_medicamento.py` :: `AjustarStockMedicamentoUseCase.execute` -> 27.00 > 10.00 (allowlisted: no)
- `clinicdesk/app/application/usecases/crear_cita.py` :: `CrearCitaUseCase.execute` -> 17.00 > 10.00 (allowlisted: no)
- `clinicdesk/app/application/usecases/dispensar_medicamento.py` :: `DispensarMedicamentoUseCase.execute` -> 26.00 > 10.00 (allowlisted: no)
- `clinicdesk/app/infrastructure/sqlite/repos_incidencias.py` :: `IncidenciasRepository.search` -> 13.00 > 10.00 (allowlisted: no)
- `clinicdesk/app/pages/incidencias/page.py` :: `PageIncidencias._load_detail` -> 11.00 > 10.00 (allowlisted: no)
- `scripts/structural_gate.py` :: `analyze_repo` -> 24.00 > 10.00 (allowlisted: no)
- `scripts/structural_gate.py` :: `generate_report` -> 15.00 > 10.00 (allowlisted: no)

## 3) Hotspots (top 10)

| file | file_loc | max_cc | avg_cc | worst_function | score | allowlisted? |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| `scripts/structural_gate.py` | 418 | 24 | 3.17 | analyze_repo (cc=24, loc=82) | 1.86 | no |
| `clinicdesk/app/application/usecases/ajustar_stock_medicamento.py` | 183 | 27 | 5.33 | AjustarStockMedicamentoUseCase.execute (cc=27, loc=95) | 1.80 | no |
| `clinicdesk/app/application/usecases/dispensar_medicamento.py` | 207 | 26 | 4.57 | DispensarMedicamentoUseCase.execute (cc=26, loc=113) | 1.77 | no |
| `clinicdesk/app/application/usecases/ajustar_stock_material.py` | 185 | 25 | 5.00 | AjustarStockMaterialUseCase.execute (cc=25, loc=97) | 1.69 | no |
| `clinicdesk/app/application/usecases/crear_cita.py` | 203 | 17 | 3.44 | CrearCitaUseCase.execute (cc=17, loc=81) | 1.22 | no |
| `clinicdesk/app/application/csv/csv_service.py` | 490 | 11 | 4.08 | CsvService._format_row_error (cc=11, loc=18) | 1.15 | no |
| `clinicdesk/app/infrastructure/sqlite/repos_incidencias.py` | 261 | 13 | 3.40 | IncidenciasRepository.search (cc=13, loc=65) | 1.04 | no |
| `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py` | 412 | 9 | 4.07 | DemoDataSeeder._persist_incidences (cc=9, loc=48) | 0.95 | no |
| `scripts/ml_cli.py` | 463 | 8 | 1.84 | main (cc=8, loc=24) | 0.94 | no |
| `clinicdesk/app/application/csv/csv_io.py` | 114 | 13 | 4.60 | read_csv (cc=13, loc=47) | 0.89 | no |

## 4) Recomendaciones automáticas

- `scripts/structural_gate.py` / `analyze_repo`: extrae funciones puras para separar ramas condicionales y bajar CC.
- `scripts/structural_gate.py`: divide el módulo en submódulos cohesivos por bounded context para reducir LOC del archivo.
- `scripts/structural_gate.py` / `analyze_repo`: introduce use cases/ports para desacoplar orquestación de detalles de infraestructura.
- `clinicdesk/app/application/usecases/ajustar_stock_medicamento.py` / `AjustarStockMedicamentoUseCase.execute`: extrae funciones puras para separar ramas condicionales y bajar CC.
- `clinicdesk/app/application/usecases/ajustar_stock_medicamento.py`: divide el módulo en submódulos cohesivos por bounded context para reducir LOC del archivo.
- `clinicdesk/app/application/usecases/ajustar_stock_medicamento.py` / `AjustarStockMedicamentoUseCase.execute`: introduce use cases/ports para desacoplar orquestación de detalles de infraestructura.
- `clinicdesk/app/application/usecases/dispensar_medicamento.py` / `DispensarMedicamentoUseCase.execute`: extrae funciones puras para separar ramas condicionales y bajar CC.
- `clinicdesk/app/application/usecases/dispensar_medicamento.py`: divide el módulo en submódulos cohesivos por bounded context para reducir LOC del archivo.
- `clinicdesk/app/application/usecases/dispensar_medicamento.py` / `DispensarMedicamentoUseCase.execute`: introduce use cases/ports para desacoplar orquestación de detalles de infraestructura.
- `clinicdesk/app/application/usecases/ajustar_stock_material.py` / `AjustarStockMaterialUseCase.execute`: extrae funciones puras para separar ramas condicionales y bajar CC.
- `clinicdesk/app/application/usecases/ajustar_stock_material.py`: divide el módulo en submódulos cohesivos por bounded context para reducir LOC del archivo.
- `clinicdesk/app/application/usecases/ajustar_stock_material.py` / `AjustarStockMaterialUseCase.execute`: introduce use cases/ports para desacoplar orquestación de detalles de infraestructura.
- `clinicdesk/app/application/usecases/crear_cita.py` / `CrearCitaUseCase.execute`: extrae funciones puras para separar ramas condicionales y bajar CC.
- `clinicdesk/app/application/usecases/crear_cita.py`: divide el módulo en submódulos cohesivos por bounded context para reducir LOC del archivo.
- `clinicdesk/app/application/usecases/crear_cita.py` / `CrearCitaUseCase.execute`: introduce use cases/ports para desacoplar orquestación de detalles de infraestructura.
- `clinicdesk/app/application/csv/csv_service.py` / `CsvService._format_row_error`: extrae funciones puras para separar ramas condicionales y bajar CC.
- `clinicdesk/app/application/csv/csv_service.py`: divide el módulo en submódulos cohesivos por bounded context para reducir LOC del archivo.
- `clinicdesk/app/application/csv/csv_service.py` / `CsvService._format_row_error`: introduce use cases/ports para desacoplar orquestación de detalles de infraestructura.
- `clinicdesk/app/infrastructure/sqlite/repos_incidencias.py` / `IncidenciasRepository.search`: extrae funciones puras para separar ramas condicionales y bajar CC.
- `clinicdesk/app/infrastructure/sqlite/repos_incidencias.py`: divide el módulo en submódulos cohesivos por bounded context para reducir LOC del archivo.
- `clinicdesk/app/infrastructure/sqlite/repos_incidencias.py` / `IncidenciasRepository.search`: introduce use cases/ports para desacoplar orquestación de detalles de infraestructura.
- `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py` / `DemoDataSeeder._persist_incidences`: extrae funciones puras para separar ramas condicionales y bajar CC.
- `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py`: divide el módulo en submódulos cohesivos por bounded context para reducir LOC del archivo.
- `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py` / `DemoDataSeeder._persist_incidences`: introduce use cases/ports para desacoplar orquestación de detalles de infraestructura.
- `scripts/ml_cli.py` / `main`: extrae funciones puras para separar ramas condicionales y bajar CC.
- `scripts/ml_cli.py`: divide el módulo en submódulos cohesivos por bounded context para reducir LOC del archivo.
- `scripts/ml_cli.py` / `main`: introduce use cases/ports para desacoplar orquestación de detalles de infraestructura.
- `clinicdesk/app/application/csv/csv_io.py` / `read_csv`: extrae funciones puras para separar ramas condicionales y bajar CC.
- `clinicdesk/app/application/csv/csv_io.py`: divide el módulo en submódulos cohesivos por bounded context para reducir LOC del archivo.
- `clinicdesk/app/application/csv/csv_io.py` / `read_csv`: introduce use cases/ports para desacoplar orquestación de detalles de infraestructura.
