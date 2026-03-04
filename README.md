# ClinicDesk ML Architecture Case Study

[![Quality Gate](https://github.com/<OWNER>/<REPO>/actions/workflows/quality_gate.yml/badge.svg)](https://github.com/<OWNER>/<REPO>/actions/workflows/quality_gate.yml)

Arquitectura ML reproducible para predicción de riesgo en citas clínicas, con gobernanza de artefactos y exportación de datos estable para consumo en Power BI.


## Qué es / Para quién
- **Qué es**: producto de escritorio (PySide6) para operación clínica con analítica de riesgo en citas y exportación contractual a BI.
- **Para quién (no técnico)**: responsables de operación/gestión que necesitan priorizar citas y monitorear riesgo con indicadores claros.
- **Para quién (técnico)**: equipos de ingeniería que valoran Clean Architecture, quality gates estrictos y mantenibilidad en Python.

## Demo rápida (3 min)
- Guion de demo para entrevista/reclutamiento: [docs/recruiter_kit.md](docs/recruiter_kit.md).
- Objetivo: mostrar el flujo end-to-end (seed, features, train, score, drift, export) en 3 minutos.

## Arquitectura (C4)
- Diagramas C4 en Mermaid (contexto, contenedores y componentes): [docs/arquitectura_c4.md](docs/arquitectura_c4.md).

## Calidad
- Comando canónico de calidad para PR (local y CI):

```bash
python -m scripts.gate_pr
```

## Seguridad / Privacidad
- Sanitización y redacción de metadata para evitar PII en auditoría/logs.
- Cifrado opcional de columnas sensibles en SQLite vía variables de entorno.
- Escaneo de secretos con **gitleaks** dentro del gate completo.
- Escaneo de dependencias con **pip-audit** (con política de allowlist explícita).
- Documentación de threat model y hardening para operación responsable.

## Release bundle (atajo)
- Bundle reproducible disponible con `python -m scripts.build_release`.
- Detalle de uso en la sección [Release bundle](#release-bundle).


## 🚀 Getting Started (1 comando)

### Requisitos
- Python **3.11** o superior.
- `pip` disponible en la instalación de Python.

### Setup reproducible
Desde la raíz del repo:

- **Windows (CMD/PowerShell):**

```bat
scripts\setup.bat
```

- **Linux/macOS (bash):**

```bash
./scripts/setup.sh
```

- **Alternativa multiplataforma:**

```bash
python scripts/setup.py
```

El setup crea `.venv/` si no existe, instala `requirements.txt` + `requirements-dev.txt`, y valida `ruff`, `pytest`, `pip-audit` y `mypy`.

### Ejecutar la app

```bash
python scripts/run_app.py
```

### Ejecutar gate de PR

```bash
python -m scripts.gate_pr
```

### Dependencias deterministas (lock con pip-tools)

- Las dependencias directas se editan en `requirements.in` (runtime) y `requirements-dev.in` (dev).
- Los locks versionados son `requirements.txt` y `requirements-dev.txt`.
- Para regenerar locks:

```bash
python -m scripts.lock_deps
```

Política de actualización:
- Cualquier bump de dependencias debe ir en PR separado del cambio funcional.
- Nunca editar a mano `requirements*.txt`: siempre regenerar desde los `.in`.
- El quality gate/CI falla si detecta líneas no pinneadas (`==`) en `requirements*.txt`.


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
python scripts/ml_cli.py build-features --demo-fake --version v_demo --store-path ./data/feature_store
python scripts/ml_cli.py train --dataset-version v_demo --model-version m_demo --feature-store-path ./data/feature_store --model-store-path ./data/model_store
python scripts/ml_cli.py score --dataset-version v_demo --predictor trained --model-version m_demo --feature-store-path ./data/feature_store --model-store-path ./data/model_store --limit 10
python scripts/ml_cli.py drift --from-version v_demo --to-version v_demo2 --feature-store-path ./data/feature_store
python scripts/ml_cli.py export features --dataset-version v_demo --output ./exports --feature-store-path ./data/feature_store
python scripts/ml_cli.py export metrics --model-name citas_nb_v1 --model-version m_demo --dataset-version v_demo --output ./exports --model-store-path ./data/model_store
python scripts/ml_cli.py export scoring --dataset-version v_demo --predictor trained --model-version m_demo --output ./exports --feature-store-path ./data/feature_store --model-store-path ./data/model_store
python scripts/ml_cli.py export drift --from-version v_demo --to-version v_demo2 --output ./exports --feature-store-path ./data/feature_store
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
- `kpi_overview.csv`
- `kpi_scores_by_bucket.csv`
- `kpi_drift_by_feature.csv`
- `kpi_training_metrics.csv`

Comandos CLI equivalentes (referencia):

```bash
python scripts/ml_cli.py seed-demo --seed 123 --doctors 10 --patients 80 --appointments 300 --from 2026-01-01 --to 2026-02-28 --incidence-rate 0.15
python scripts/ml_cli.py build-features --version demo_ui_<timestamp> --from 2026-01-01 --to 2026-02-28 --store-path ./data/feature_store
python scripts/ml_cli.py train --dataset-version demo_ui_<timestamp> --model-version m_demo_ui_<timestamp> --feature-store-path ./data/feature_store --model-store-path ./data/model_store
python scripts/ml_cli.py score --dataset-version demo_ui_<timestamp> --predictor trained --model-version m_demo_ui_<timestamp> --feature-store-path ./data/feature_store --model-store-path ./data/model_store --limit 20
python scripts/ml_cli.py drift --from-version <prev_or_same> --to-version demo_ui_<timestamp> --feature-store-path ./data/feature_store
python scripts/ml_cli.py export features --dataset-version demo_ui_<timestamp> --output ./exports --feature-store-path ./data/feature_store
python scripts/ml_cli.py export metrics --model-name citas_nb_v1 --model-version m_demo_ui_<timestamp> --dataset-version demo_ui_<timestamp> --output ./exports --model-store-path ./data/model_store
python scripts/ml_cli.py export scoring --dataset-version demo_ui_<timestamp> --predictor trained --model-version m_demo_ui_<timestamp> --output ./exports --feature-store-path ./data/feature_store --model-store-path ./data/model_store
python scripts/ml_cli.py export drift --from-version <prev_or_same> --to-version demo_ui_<timestamp> --output ./exports --feature-store-path ./data/feature_store
```

### Demo rápida por CLI (alternativa)

```bash
python scripts/ml_cli.py seed-demo --seed 123 --doctors 10 --patients 80 --appointments 300 --from 2026-01-01 --to 2026-02-28 --incidence-rate 0.15
python scripts/ml_cli.py build-features --from 2026-01-01 --to 2026-02-28 --store-path ./data/feature_store
python scripts/ml_cli.py train --dataset-version <version> --model-version m_demo --feature-store-path ./data/feature_store --model-store-path ./data/model_store
python scripts/ml_cli.py score --dataset-version <version> --predictor trained --model-version m_demo --feature-store-path ./data/feature_store --model-store-path ./data/model_store --limit 20
python scripts/ml_cli.py drift --from-version <v1> --to-version <v2> --feature-store-path ./data/feature_store
```


## 📈 Power BI KPIs (CSV)

Además de los exports detallados, el flujo **Analítica (Demo)** genera 4 contratos agregados para tableros ejecutivos:

- `kpi_overview.csv`: 1 fila por ejecución (`citas_count`, `% riesgo alto`, `threshold`, `drift_severity`, `drift_psi_max`).
- `kpi_scores_by_bucket.csv`: distribución de etiquetas de scoring (`label`, `count`, `pct`).
- `kpi_drift_by_feature.csv`: PSI por feature con severidad semafórica (`GREEN/AMBER/RED`).
- `kpi_training_metrics.csv`: métricas de entrenamiento/test en formato long (`metric_name`, `metric_value`).

Sugerencia de páginas en Power BI:
1. **Resumen ejecutivo**: tarjetas con volumen, riesgo alto y severidad de drift.
2. **Riesgo y distribución**: barras por bucket de scoring y tendencia por versión.
3. **Salud del modelo**: comparativa train/test de accuracy, precision, recall y f1.
4. **Monitoreo de drift**: matriz de PSI por feature con semáforo.

## 💾 Storage único SQLite (app + seed-demo)

- Fuente única por defecto: `./data/clinicdesk.db`.
- La DB activa se controla por `CLINICDESK_DB_PATH` (si no está definida, se usa el default oficial).
- La app (`clinicdesk.app.main`), `seed_demo_data.py` y `scripts/ml_cli.py seed-demo` usan el mismo `resolve_db_path()` del bootstrap de SQLite.
- Override soportado:
  - CLI: `--sqlite-path /ruta/al/archivo.db`
  - Variable de entorno: `CLINICDESK_DB_PATH=/ruta/al/archivo.db`

Ejemplo:

```bash
CLINICDESK_DB_PATH=./data/clinicdesk.db python scripts/ml_cli.py seed-demo --appointments 5000 --batch-size 500
```


## 🔐 Protección de PII en reposo (SQLite)

Se implementó **cifrado por columnas sensibles** (opción B) para tablas de personas:

- `pacientes`: `telefono`, `email`, `direccion`, `alergias`, `observaciones`
- `medicos`: `telefono`, `email`, `direccion`
- `personal`: `telefono`, `email`, `direccion`

### Flags por entorno

- `CLINICDESK_PII_ENCRYPTION_ENABLED` → `true/false` (default: `false`)
- `CLINICDESK_PII_ENCRYPTION_KEY` → clave de cifrado (obligatoria si el flag está en `true`)

Ejemplo:

```bash
export CLINICDESK_PII_ENCRYPTION_ENABLED=true
export CLINICDESK_PII_ENCRYPTION_KEY='cambia-esta-clave-en-tu-entorno'
python -m clinicdesk.app.main
```

### Compatibilidad con DB existente

- Si el cifrado está desactivado, el comportamiento no cambia.
- Si se activa el cifrado, al arrancar se migra automáticamente PII legado en claro hacia formato cifrado (`enc:v1:...`).
- Lecturas mantienen compatibilidad: datos en claro antiguos también se pueden leer sin romper flujos.

### UX cuando falta la clave

Si `CLINICDESK_PII_ENCRYPTION_ENABLED=true` y no existe `CLINICDESK_PII_ENCRYPTION_KEY`, la app falla temprano con mensaje explícito para configurar el entorno (sin loguear secretos).

## Demo para usuarios no técnicos

Para poblar la aplicación con datos realistas de demostración (incluyendo farmacia, recetas/líneas, dispensaciones, materiales, movimientos, turnos y ausencias):

```bash
python -m scripts.ml_cli seed-demo --reset --meds 200 --materials 120 --recipes 400 --movements 2000 --turns-months 2 --absences 60
```

Después del seed, las pantallas muestran datos visibles y, si alguna queda vacía, la UI ofrece estado vacío con botón **"Generar datos demo"**.

## Demo no técnica (2 minutos)

En la pantalla **Analítica (Demo)** un usuario no técnico puede ejecutar el flujo completo sin términos de ingeniería:

1. Revisa rango de fechas y activa (opcional) **Generar datos demo si faltan**.
2. Pulsa **Ejecutar Demo Completa**.
3. Observa el diálogo de progreso con pasos humanos:
   - Preparar datos para análisis
   - Crear modelo de predicción
   - Analizar citas y estimar riesgo
   - Detectar cambios en comportamiento
4. Si lo necesitas, usa **Cancelar** en cualquier momento.
5. Al terminar, revisa **Último análisis** y exporta para Power BI.

Notas UX:
- Las versiones internas (`dataset_version`, `model_version`) están ocultas por defecto dentro de **Avanzado**.
- La UI no ejecuta lógica técnica; delega el flujo al `AnalyticsWorkflowService`.

## Release bundle

Para construir un paquete reproducible de distribución:

```bash
python -m scripts.build_release
```

Esto genera `dist/clinicdesk-<version>.zip` con el contenido mínimo ejecutable (código, scripts, requisitos, README y guías de seguridad), excluyendo caches, logs y bases de datos.

Uso recomendado del zip:

1. Descomprimir el archivo en una carpeta de trabajo.
2. Crear entorno e instalar dependencias:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
3. Inicializar y ejecutar:
   ```bash
   python -m scripts.setup
   python -m scripts.run_app
   ```
