# ClinicDesk ML Architecture Case Study

Arquitectura ML reproducible para predicción de riesgo en citas clínicas, con gobernanza de artefactos y exportación de datos estable para consumo en Power BI.

## 🎯 Problema
En operación clínica, anticipar citas de riesgo (p. ej., potencial no-show o cita con fricción operativa) permite priorizar seguimiento y capacidad de respuesta. Este proyecto aborda ese problema con foco en gobernanza técnica:

- Predicción offline de riesgo a nivel cita.
- Reproducibilidad del pipeline de datos/features/modelo.
- Versionado explícito de datasets y modelos.
- Control de drift entre versiones de features.
- Exportación contractual de datos para analítica ejecutiva.

## 🧱 Arquitectura

```text
Data → Dataset → Features → Feature Store → Train → Model Store → Scoring → Drift → CSV → Power BI
```

### Separación por capas (Clean Architecture)
- **Domain**: reglas y modelos de negocio sin dependencias técnicas.
- **Application**: casos de uso, puertos y orquestación.
- **Infrastructure**: adaptadores (SQLite, filesystem JSON, CLI).
- **Presentation**: UI/entrypoints desacoplados de la lógica de negocio.

### Ports & Adapters
- Los casos de uso dependen de contratos (`ports`) y no de implementaciones concretas.
- Feature Store y Model Store se inyectan como puertos, con adaptadores locales JSON para persistencia versionada.

### CI y cobertura
- El proyecto define quality gate automatizado para tests y coverage del core.
- Existe documentación explícita de reglas de arquitectura e imports permitidos.

### Versionado con hashes
- Feature artifacts guardan `content_hash` y `schema_hash` para trazabilidad de datos y contrato.
- Model artifacts guardan hash de payload y metadata de entrenamiento/evaluación.

## 🔁 Flujo reproducible (CLI)
Comandos operativos principales:

```bash
PYTHONPATH=. python scripts/ml_cli.py build-features --demo-fake --version v_demo --store-path ./data/feature_store
PYTHONPATH=. python scripts/ml_cli.py train --dataset-version v_demo --model-version m_demo --feature-store-path ./data/feature_store --model-store-path ./data/model_store
PYTHONPATH=. python scripts/ml_cli.py score --dataset-version v_demo --predictor trained --model-version m_demo --feature-store-path ./data/feature_store --model-store-path ./data/model_store --limit 10
PYTHONPATH=. python scripts/ml_cli.py drift --from-version v_demo --to-version v_demo2 --feature-store-path ./data/feature_store
PYTHONPATH=. python scripts/ml_cli.py export features --dataset-version v_demo --output ./exports --feature-store-path ./data/feature_store
PYTHONPATH=. python scripts/ml_cli.py export metrics --model-name citas_nb_v1 --model-version m_demo --dataset-version v_demo --output ./exports --model-store-path ./data/model_store
PYTHONPATH=. python scripts/ml_cli.py export scoring --dataset-version v_demo --predictor trained --model-version m_demo --output ./exports --feature-store-path ./data/feature_store --model-store-path ./data/model_store
PYTHONPATH=. python scripts/ml_cli.py export drift --from-version v_demo --to-version v_demo2 --output ./exports --feature-store-path ./data/feature_store
```

Qué hace cada etapa:
- `build-features`: construye dataset de features y genera artifacts versionados (rows/schema/metadata).
- `train`: entrena modelo Naive Bayes, evalúa train/test temporal y registra modelo + metadata.
- `score`: ejecuta scoring (baseline o modelo entrenado) sobre versión de dataset.
- `drift`: calcula PSI por feature entre dos versiones y emite bandera global.
- `export`: genera CSV contractuales (`features`, `metrics`, `scoring`, `drift`) para BI.

## 📊 Evaluación del modelo
- **Holdout temporal**: split determinista por tiempo (`test_ratio=0.2`, `time_field=inicio_ts`) para evitar fuga temporal.
- **Métricas Train vs Test**: accuracy, precision y recall para comparar generalización.
- **Calibración de threshold**: selección de umbral según política explícita (`min_recall` con objetivo 0.80).
- **Persistencia de metadata**: split config, métricas, threshold calibrado y nota de evaluación quedan registrados con el modelo.

## 📉 Drift Detection
- Drift calculado con **PSI** por feature categórica de `citas_features`.
- Umbral de alerta configurado en **PSI ≥ 0.2**.
- `overall_flag` se activa si alguna feature supera el umbral.

## 📁 Artefactos versionados

### Feature artifacts
Por versión de dataset se almacenan:
- `vX.json` con filas de features.
- `vX.schema.json` con schema versionado.
- `vX.metadata.json` con `row_count`, `content_hash`, `schema_hash`, `quality`.

### Model artifacts
Por versión de modelo se almacenan:
- `vY.model.json` (payload entrenado).
- `vY.metadata.json` con dataset de origen, hashes, split config, métricas y threshold calibrado.

### CSV contracts estables
Exports con columnas fijas y orden estable:
- `features_export.csv`
- `model_metrics_export.csv`
- `scoring_export.csv`
- `drift_export.csv`

## 📊 Integración con Power BI
- La CLI exporta CSV listos para ingestión en Power BI sin dependencias de `pandas`.
- Los contratos estables permiten construir dashboards ejecutivos sin romper transformaciones al cambiar versión.
- `dataset_version` y `model_version` habilitan comparabilidad histórica entre ejecuciones.

## 🛠 Stack técnico
- Python
- Clean Architecture
- Ports & Adapters contract-first
- Versionado determinista con hashes
- CLI operativa para pipeline ML
- Power BI (vía contratos CSV)

## 🧠 Decisiones técnicas clave
- **Proxy label documentada**: la etiqueta offline deriva de señales operativas (`has_incidencias` / `is_suspicious`).
- **Determinismo de artefactos**: serialización JSON canónica + hashing SHA-256.
- **Sin dependencias externas de serving**: modelo y scoring ejecutan en código Python del proyecto.
- **Holdout temporal**: evaluación respetando orden cronológico.
- **Calibración basada en objetivo**: threshold seleccionado por política explícita de recall mínimo.
- **Gobernanza de artefactos**: separación formal entre feature store, model store y exports BI.

## 🚀 Qué demuestra este proyecto
En contexto de entrevista senior, este proyecto evidencia:
- Diseño arquitectónico con límites claros entre dominio, casos de uso y adaptadores.
- Implementación ML reproducible, versionada y auditable.
- Data governance aplicada a datasets, modelos y contratos de salida.
- Backend Python orientado a mantenibilidad operativa.
- Integración pragmática con BI empresarial (Power BI ready por CSV contractual).

## Demo & ML desde UI (Paso 15)

La app incluye la pantalla **Demo & ML** en el menú lateral para ejecutar el flujo completo sin scripts:

1. **Seed Demo**: configura seed, volúmenes y rango, luego pulsa `Ejecutar SeedDemoData`.
2. **Exploración**: usa la caja de búsqueda y revisa tabs de Médicos, Pacientes, Citas e Incidencias.
3. **ML actions**:
   - `build-features` con rango fecha.
   - `train` con `dataset_version` y `model_version`.
   - `score` (`baseline` o `trained`) con límite.
   - `drift` entre dos versiones.
   - `export` para generar CSV de features/métricas/scoring/drift en `./exports` (o ruta indicada).
4. **Resultados**: logs en tiempo real + tabla de salida para score/drift.

> La UI solo consume `application.services.DemoMLFacade`; no accede a SQLite ni stores desde la capa de presentación.

## Demo en 60s (Paso 16: One-click)

En **Demo & ML** ahora existe el botón **Run Full Demo** que ejecuta en un click:
`seed -> build-features -> train -> score -> drift -> export`.

1. Ajusta seed/volúmenes/rango y carpeta `Export dir`.
2. Pulsa **Run Full Demo**.
3. Revisa la barra de progreso por pasos y logs en tiempo real.
4. Si necesitas abortar, usa **Cancel** (cancelación segura).
5. Al finalizar verás `dataset_version`, `model_version`, rutas CSV y lista de comandos CLI equivalentes (botón **Copy CLI commands**).

CSV listos para Power BI:
- `features_export.csv`
- `model_metrics_export.csv`
- `scoring_export.csv`
- `drift_export.csv`

Comandos CLI equivalentes (referencia):

```bash
PYTHONPATH=. python scripts/ml_cli.py seed-demo --seed 123 --doctors 10 --patients 80 --appointments 300 --from 2026-01-01 --to 2026-02-28 --incidence-rate 0.15
PYTHONPATH=. python scripts/ml_cli.py build-features --version demo_ui_<timestamp> --from 2026-01-01 --to 2026-02-28 --store-path ./data/feature_store
PYTHONPATH=. python scripts/ml_cli.py train --dataset-version demo_ui_<timestamp> --model-version m_demo_ui_<timestamp> --feature-store-path ./data/feature_store --model-store-path ./data/model_store
PYTHONPATH=. python scripts/ml_cli.py score --dataset-version demo_ui_<timestamp> --predictor trained --model-version m_demo_ui_<timestamp> --feature-store-path ./data/feature_store --model-store-path ./data/model_store --limit 20
PYTHONPATH=. python scripts/ml_cli.py drift --from-version <prev_or_same> --to-version demo_ui_<timestamp> --feature-store-path ./data/feature_store
PYTHONPATH=. python scripts/ml_cli.py export features --dataset-version demo_ui_<timestamp> --output ./exports --feature-store-path ./data/feature_store
PYTHONPATH=. python scripts/ml_cli.py export metrics --model-name citas_nb_v1 --model-version m_demo_ui_<timestamp> --dataset-version demo_ui_<timestamp> --output ./exports --model-store-path ./data/model_store
PYTHONPATH=. python scripts/ml_cli.py export scoring --dataset-version demo_ui_<timestamp> --predictor trained --model-version m_demo_ui_<timestamp> --output ./exports --feature-store-path ./data/feature_store --model-store-path ./data/model_store
PYTHONPATH=. python scripts/ml_cli.py export drift --from-version <prev_or_same> --to-version demo_ui_<timestamp> --output ./exports --feature-store-path ./data/feature_store
```

### Demo rápida por CLI (alternativa)

```bash
PYTHONPATH=. python scripts/ml_cli.py seed-demo --seed 123 --doctors 10 --patients 80 --appointments 300 --from 2026-01-01 --to 2026-02-28 --incidence-rate 0.15
PYTHONPATH=. python scripts/ml_cli.py build-features --from 2026-01-01 --to 2026-02-28 --store-path ./data/feature_store
PYTHONPATH=. python scripts/ml_cli.py train --dataset-version <version> --model-version m_demo --feature-store-path ./data/feature_store --model-store-path ./data/model_store
PYTHONPATH=. python scripts/ml_cli.py score --dataset-version <version> --predictor trained --model-version m_demo --feature-store-path ./data/feature_store --model-store-path ./data/model_store --limit 20
PYTHONPATH=. python scripts/ml_cli.py drift --from-version <v1> --to-version <v2> --feature-store-path ./data/feature_store
```

## 💾 Storage único SQLite (app + seed-demo)

- Fuente única por defecto: `./data/clinicdesk.db`.
- La DB activa se controla por `CLINICDESK_DB_PATH` (si no está definida, se usa el default oficial).
- La app (`clinicdesk.app.main`), `seed_demo_data.py` y `scripts/ml_cli.py seed-demo` usan el mismo `resolve_db_path()` del bootstrap de SQLite.
- Override soportado:
  - CLI: `--sqlite-path /ruta/al/archivo.db`
  - Variable de entorno: `CLINICDESK_DB_PATH=/ruta/al/archivo.db`

Ejemplo:

```bash
CLINICDESK_DB_PATH=./data/clinicdesk.db PYTHONPATH=. python scripts/ml_cli.py seed-demo --appointments 5000 --batch-size 500
```

## Demo para usuarios no técnicos

Para poblar la aplicación con datos realistas de demostración (incluyendo farmacia, recetas/líneas, dispensaciones, materiales, movimientos, turnos y ausencias):

```bash
python -m scripts.ml_cli seed-demo --reset --meds 200 --materials 120 --recipes 400 --movements 2000 --turns-months 2 --absences 60
```

Después del seed, las pantallas muestran datos visibles y, si alguna queda vacía, la UI ofrece estado vacío con botón **"Generar datos demo"**.
