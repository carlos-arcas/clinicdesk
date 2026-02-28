# CI Quality Gate (Core)

## Objetivo
Asegurar calidad continua sin bloquear por UI. El gate bloqueante aplica al **core clínico bajo control en Paso 2** (flujo de citas end-to-end).

## Comando único (local y CI)
- `python scripts/quality_gate.py`

## Qué ejecuta el gate
1. **Lint/format opcional (solo si ya existe configuración)**
   - Detecta `pyproject.toml` con sección `[tool.ruff]`.
   - Si existe, ejecuta `ruff check .` y `ruff format --check .`.
2. **Tests bloqueantes**
   - Ejecuta `pytest` con `-m "not ui"`.
3. **Coverage SOLO core**
   - Calcula cobertura mediante trazado de ejecución sobre los módulos core definidos en el script.
4. **Umbral**
   - Falla si cobertura core `< 85%`.

## Definición de “core” (Paso 2)
Módulos incluidos en cobertura bloqueante:
- `clinicdesk/app/domain/enums.py`
- `clinicdesk/app/domain/exceptions.py`
- `clinicdesk/app/application/usecases/crear_cita.py`
- `clinicdesk/app/infrastructure/sqlite/repos_citas.py`
- `clinicdesk/app/queries/citas_queries.py`

Módulos excluidos del gate bloqueante en este paso:
- UI/presentation (`clinicdesk/app/ui`, `clinicdesk/app/pages`)
- scripts de soporte y tests
- resto de módulos legacy que se incorporarán gradualmente al gate en pasos siguientes.

## Notas de operación
- Los tests de UI deben declararse con marker `ui` para no bloquear este gate.
- El script devuelve `exit code != 0` si falla lint configurado, tests o cobertura.

## Demo ML CLI (30s)
Con `PYTHONPATH=.` puedes ejecutar el flujo ML end-to-end sin UI:

1. Build features + artifacts:
   - `PYTHONPATH=. python scripts/ml_cli.py build-features --demo-fake --version v_demo --store-path ./data/feature_store`
2. Train (split temporal + calibración + model store):
   - `PYTHONPATH=. python scripts/ml_cli.py train --dataset-version v_demo --model-version m_demo --feature-store-path ./data/feature_store --model-store-path ./data/model_store`
3. Score (baseline o trained):
   - `PYTHONPATH=. python scripts/ml_cli.py score --dataset-version v_demo --predictor trained --model-version m_demo --feature-store-path ./data/feature_store --model-store-path ./data/model_store --limit 10`
4. Drift (comparar versiones):
   - `PYTHONPATH=. python scripts/ml_cli.py drift --from-version v_demo --to-version v_demo2 --feature-store-path ./data/feature_store`

## Power BI Integration (CSV Contracts)
La CLI ML incluye exportación CSV estable (orden fijo de columnas) para integrar dashboards externos (ej. Power BI) sin depender de `pandas`.

Comandos:
- `PYTHONPATH=. python scripts/ml_cli.py export features --dataset-version v_demo --output ./exports --feature-store-path ./data/feature_store`
- `PYTHONPATH=. python scripts/ml_cli.py export metrics --model-name citas_nb_v1 --model-version m_demo --dataset-version v_demo --output ./exports --model-store-path ./data/model_store`
- `PYTHONPATH=. python scripts/ml_cli.py export scoring --dataset-version v_demo --predictor trained --model-version m_demo --output ./exports --feature-store-path ./data/feature_store --model-store-path ./data/model_store`
- `PYTHONPATH=. python scripts/ml_cli.py export drift --from-version v_demo --to-version v_demo2 --output ./exports --feature-store-path ./data/feature_store`

Archivos generados en `./exports/`:
- `features_export.csv`
- `model_metrics_export.csv`
- `scoring_export.csv`
- `drift_export.csv`


## Demo dataset reproducible (SQLite real, sin demo-fake)
Flujo recomendado para demos ML + Power BI con datos coherentes:

1. Seed de demo:
   - `PYTHONPATH=. python scripts/ml_cli.py seed-demo --seed 123 --doctors 10 --patients 80 --appointments 300 --from 2026-01-01 --to 2026-02-28 --incidence-rate 0.15`
2. Build features desde SQLite real:
   - `PYTHONPATH=. python scripts/ml_cli.py build-features --from 2026-01-01 --to 2026-02-28 --store-path ./data/feature_store`
3. Train:
   - `PYTHONPATH=. python scripts/ml_cli.py train --dataset-version <version> --model-version m_demo --feature-store-path ./data/feature_store --model-store-path ./data/model_store`
4. Export para Power BI:
   - `PYTHONPATH=. python scripts/ml_cli.py export features --dataset-version <version> --output ./exports --feature-store-path ./data/feature_store`

Secuencia completa para operación: `seed-demo -> build-features -> train -> export -> Power BI`.
