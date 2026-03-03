# CI Quality Gate (Core)

## Objetivo
Asegurar calidad continua sin bloquear por UI. El gate bloqueante aplica al **core clínico bajo control en Paso 2** (flujo de citas end-to-end).

## Comando canónico (local y CI)
- Gate rápido: `python -m scripts.gate_rapido`
- Gate completo PR/CI: `python -m scripts.gate_pr`

Regla de CI: ejecutar exactamente `python -m scripts.gate_pr`.

## Qué ejecuta el gate
1. **Lint/format obligatorio con Ruff**
   - Configuración central en `pyproject.toml` (`[tool.ruff]` y `[tool.ruff.format]`).
   - El gate ejecuta siempre `ruff check .` y `ruff format --check .`.
   - Si Ruff no está instalado, el gate falla con error explícito (sin skips silenciosos).
2. **Tests bloqueantes**
   - Ejecuta `pytest` con `-m "not ui"`.
3. **Coverage SOLO core + artefacto en docs/**
   - Calcula cobertura core mediante trazado de ejecución sobre los módulos core definidos en el script.
   - Además genera `docs/coverage.xml` usando `pytest-cov` para publicar artefactos en CI.
4. **Structural gate (LOC + CC + hotspots)**
   - Analiza Python con `ast` (sin dependencias externas) excluyendo `app/ui/**`, `tests/**`, `migrations/**` y `sql/**`.
   - Detecta monolitos por tamaño de archivo/función/clase.
   - Calcula complejidad ciclomática (CC) por función/método.
   - Calcula hotspots por score combinado de tamaño y CC.
   - Genera siempre `docs/quality_report.md`.
5. **Umbral de cobertura core**
   - Falla si cobertura core `< 85%`.



## Seguridad de dependencias y secretos (bloqueante)

El gate canónico `python -m scripts.gate_pr` ahora ejecuta además:

6. **`pip-audit` bloqueante**
   - Comando: `python -m pip_audit --progress-spinner off --output docs/pip_audit_report.txt --format columns`
   - Si existen vulnerabilidades, el gate falla.
   - Allowlist opcional y controlada: `docs/pip_audit_allowlist.json` con `id` y `motivo` por vulnerabilidad.
7. **Escaneo de secretos con Gitleaks**
   - Comando: `gitleaks detect --source . --no-git --report-format json --report-path docs/secrets_scan_report.txt`
   - Reporte: `docs/secrets_scan_report.txt`.
   - Si no existe `gitleaks` en `PATH`, el gate falla con guía de instalación (sin skips silenciosos).
8. **Guardrail básico de PII en logging**
   - Escaneo AST de llamadas `logger.*` para strings hardcodeados con tokens sensibles (`dni`, `nif`, `email`, `telefono`, `direccion`, `historia_clinica`).
   - Allowlist mínima: `docs/pii_logging_allowlist.json` con `clave` y `motivo` explícito.

### Ejecución local exacta
1. `python -m pip install --upgrade pip`
2. `pip install -r requirements-dev.txt`
3. Instalar Gitleaks (ejemplo Ubuntu):
   - `sudo apt-get update`
   - `sudo apt-get install -y gitleaks`
4. Ejecutar gate completo: `python -m scripts.gate_pr`

### Cómo resolver fallos
- **Fallo de `pip-audit` por CVEs**:
  1. Actualizar dependencia vulnerable en `requirements*.txt` / lock correspondiente.
  2. Reinstalar y repetir gate.
  3. Solo si es falso positivo real/no mitigable temporalmente: añadir entrada en `docs/pip_audit_allowlist.json` con `id` y `motivo` verificable.
- **Fallo de secrets scan**:
  1. Revocar/rotar secreto comprometido.
  2. Eliminar del historial/código y reemplazar por variables de entorno/secret manager.
  3. Reejecutar gate hasta reporte limpio.
- **Fallo de guardrail PII/logging**:
  1. Quitar tokens sensibles del mensaje hardcodeado.
  2. Mantener detalle técnico sin PII (usar IDs anonimizados).
  3. Si es test explícito, documentar allowlist con motivo.

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

## Instalación para desarrollo
1. `python -m pip install --upgrade pip`
2. `pip install -r requirements-dev.txt`

## Notas de operación
- Los tests de UI deben declararse con marker `ui` para no bloquear este gate.
- El script devuelve `exit code != 0` si falla Ruff, tests, cobertura core o generación de reportes.
- El reporte estructural se mantiene en `docs/quality_report.md` y la cobertura en `docs/coverage.xml`.
- Los comandos de tests desde raíz ya no requieren `PYTHONPATH=.`.

## Demo ML CLI (30s)
Puedes ejecutar el flujo ML end-to-end sin UI (ya no requiere `PYTHONPATH=.`):

1. Build features + artifacts:
   - `python scripts/ml_cli.py build-features --demo-fake --version v_demo --store-path ./data/feature_store`
2. Train (split temporal + calibración + model store):
   - `python scripts/ml_cli.py train --dataset-version v_demo --model-version m_demo --feature-store-path ./data/feature_store --model-store-path ./data/model_store`
3. Score (baseline o trained):
   - `python scripts/ml_cli.py score --dataset-version v_demo --predictor trained --model-version m_demo --feature-store-path ./data/feature_store --model-store-path ./data/model_store --limit 10`
4. Drift (comparar versiones):
   - `python scripts/ml_cli.py drift --from-version v_demo --to-version v_demo2 --feature-store-path ./data/feature_store`

## Power BI Integration (CSV Contracts)
La CLI ML incluye exportación CSV estable (orden fijo de columnas) para integrar dashboards externos (ej. Power BI) sin depender de `pandas`.

Comandos:
- `python scripts/ml_cli.py export features --dataset-version v_demo --output ./exports --feature-store-path ./data/feature_store`
- `python scripts/ml_cli.py export metrics --model-name citas_nb_v1 --model-version m_demo --dataset-version v_demo --output ./exports --model-store-path ./data/model_store`
- `python scripts/ml_cli.py export scoring --dataset-version v_demo --predictor trained --model-version m_demo --output ./exports --feature-store-path ./data/feature_store --model-store-path ./data/model_store`
- `python scripts/ml_cli.py export drift --from-version v_demo --to-version v_demo2 --output ./exports --feature-store-path ./data/feature_store`

Archivos generados en `./exports/`:
- `features_export.csv`
- `model_metrics_export.csv`
- `scoring_export.csv`
- `drift_export.csv`


## Demo dataset reproducible (SQLite real, sin demo-fake)
Flujo recomendado para demos ML + Power BI con datos coherentes:

1. Seed de demo:
   - `python scripts/ml_cli.py seed-demo --seed 123 --doctors 10 --patients 80 --appointments 300 --from 2026-01-01 --to 2026-02-28 --incidence-rate 0.15`
2. Build features desde SQLite real:
   - `python scripts/ml_cli.py build-features --from 2026-01-01 --to 2026-02-28 --store-path ./data/feature_store`
3. Train:
   - `python scripts/ml_cli.py train --dataset-version <version> --model-version m_demo --feature-store-path ./data/feature_store --model-store-path ./data/model_store`
4. Export para Power BI:
   - `python scripts/ml_cli.py export features --dataset-version <version> --output ./exports --feature-store-path ./data/feature_store`

Secuencia completa para operación: `seed-demo -> build-features -> train -> export -> Power BI`.

## Logging & Crash files
- El bootstrap de logging unificado usa `logging` de stdlib y crea en cada ejecución:
  - `logs/app.log` (operacional)
  - `logs/crash_soft.log` (errores esperables capturados)
  - `logs/crash_fatal.log` (excepciones no controladas / critical)
- Se agregó una validación bloqueante en `scripts/quality_gate.py` para fallar si aparece `print` en archivos Python fuera de allowlist mínima.
- Todos los scripts CLI deben enrutar salida de consola por `logging` (handler de consola a `stderr`), no por `print`.

## Seed demo rápido y seguro
Para poblar dataset demo grande con feedback real de progreso por batch + ETA, turbo SQLite y reset seguro:

- `CLINICDESK_DB_PATH=./data/clinicdesk.db python scripts/ml_cli.py seed-demo --appointments 5000 --batch-size 500 --turbo --reset`

Notas:
- `--turbo` activa PRAGMAs de rendimiento solo durante el seed.
- `--reset` solo borra automáticamente en rutas consideradas seguras de demo (por defecto se auto-activa únicamente en rutas seguras).
- Si la ruta no es segura, se bloquea el borrado con error explícito para evitar pérdida de datos.


## Structural Gate (detalle)

### Definición de CC
CC por función/método se calcula como:
- Base `1`
- `+1` por `if`, `for`, `async for`, `while`, `if` ternario (`IfExp`)
- `+N` por `try` según cantidad de `except`
- `+ (n-1)` por operadores booleanos `and/or` (`BoolOp`)
- `+N` por `match` según cantidad de `case`
- `+N` por `ifs` en comprensiones

No suma por `with`, `raise` ni `assert`.

### Umbrales y configuración
Los umbrales viven en `scripts/quality_thresholds.json`:
- `max_file_loc = 400`
- `max_function_loc = 60`
- `max_class_loc = 200`
- `max_cc = 10`
- `max_avg_cc_per_file = 6`
- `max_hotspots = 0`

Se puede pasar archivo alterno con `--thresholds`.

### Allowlist / deuda controlada
`allowlist` permite override por ruta con motivo explícito:

```json
{
  "path": "clinicdesk/app/legacy/*.py",
  "max_cc": 15,
  "max_function_loc": 90,
  "reason": "deuda temporal planificada"
}
```

Cada override aparece en `docs/quality_report.md` para facilitar su reducción gradual.

#### Baseline allowlisted vigente (structural gate)

| Archivo | Motivo |
| --- | --- |
| `scripts/structural_gate.py` | Script de tooling fuera del core clínico; refactor pendiente por tamaño/CC. |
| `scripts/ml_cli.py` | CLI de soporte ML con flujo operativo amplio; deuda temporal controlada. |
| `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py` | Seeder demo legado concentrado en un módulo único. |
| `clinicdesk/app/infrastructure/sqlite/repos_pacientes.py` | Repositorio legacy pendiente de partición por mixins/cohesión. |
| `clinicdesk/app/infrastructure/sqlite/repos_personal.py` | Repositorio legacy pendiente de segmentación por responsabilidades. |
| `clinicdesk/app/infrastructure/sqlite/repos_recetas.py` | Refactor diferido por compatibilidad con UI actual. |
| `clinicdesk/app/queries/medicos_queries.py` | Deuda preexistente en búsqueda avanzada (filtros + paginación + ordenación en una sola función). |
| `clinicdesk/app/queries/personal_queries.py` | Deuda preexistente en búsqueda avanzada análoga; requiere extracción de helpers por criterio. |

#### Plan de reducción de deuda

- Mantener `--strict` como modo esperado en CI sin subir umbrales globales.
- Objetivo operativo: retirar **1–2 entradas de allowlist por sprint**.
- Priorización sugerida:
  1. `clinicdesk/app/queries/medicos_queries.py` y `clinicdesk/app/queries/personal_queries.py` (impacto directo en violaciones activas de LOC/CC/avg-CC).
  2. `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py` (alto LOC y hotspot).
  3. Repositorios legacy `repos_*` por partición incremental de clases grandes.

### Estrategia de reducción gradual de deuda
1. Ejecutar en `--report-only` para obtener baseline.
2. Priorizar top hotspots del reporte y bajar CC/LOC por módulo.
3. Reducir allowlist iterativamente (subir exigencia por sprint).
4. Mantener `--strict` como gate final en CI.
