# ClinicDesk

[![Quality Gate](https://github.com/<OWNER>/<REPO>/actions/workflows/quality_gate.yml/badge.svg)](https://github.com/<OWNER>/<REPO>/actions/workflows/quality_gate.yml)
[![Release](https://github.com/<OWNER>/<REPO>/actions/workflows/release.yml/badge.svg)](https://github.com/<OWNER>/<REPO>/actions/workflows/release.yml)
![Python >=3.11](https://img.shields.io/badge/python-%3E%3D3.11-3776AB?logo=python&logoColor=white)

Arquitectura ML reproducible para predicción de riesgo en citas clínicas, con gobernanza de artefactos y exportación contractual para Power BI.

## Qué es
- App clínica de escritorio (PySide6) orientada a operación diaria.
- Incluye agenda, confirmaciones, farmacia, auditoría y módulos analíticos operativos integrados.
- Mantiene Clean Architecture, quality gates estrictos y controles de seguridad/privacidad.

## Para quién
- **No técnico**: liderazgo de operación clínica que necesita priorizar citas, reducir fricción y visualizar indicadores.
- **Técnico**: equipos de ingeniería que buscan separación por capas, puertos/adaptadores y validación fuerte en CI.

## Ejecutar el producto
- **Camino normal**
  - Setup: `python scripts/setup.py`
  - App: `python scripts/run_app.py`
- **Camino sandbox**
  - Setup sandbox: `python scripts/setup_sandbox.py`
  - Gate sandbox (entrypoint): `python -m scripts.gate_sandbox`

## Calidad
En CI también se ejecuta `gate_sandbox` como verificación no bloqueante.

Branch protections recomendadas: ver [docs/branch_protection_recommended.md](docs/branch_protection_recommended.md).

- Gate estricto (PR/CI):

```bash
python -m scripts.gate_pr
```

- Gate rápido (report-only, sandbox por defecto si no hay coverage):

```bash
python -m scripts.gate_rapido
```

- Gate sandbox (entornos restringidos):

```bash
python -m scripts.gate_sandbox
```

- Doctor de entorno de calidad (preflight reproducible):

```bash
python -m scripts.doctor_entorno_calidad
```

- Lint canónico de repositorio (Python + structural gate):

```bash
python -m scripts.lint_all
```

- Formato canónico de repositorio:

```bash
python -m scripts.format_all
```

- Lint canónico de Python (Ruff check + format --check):

```bash
python -m scripts.lint_py
```

- Formato canónico de Python:

```bash
python -m scripts.format_py
```

Nota: `lint_all`/`format_all` no formatean Markdown/YAML; Python sí.

`gate_pr` es el contrato estricto y canónico para CI/PR (el que usa CI).  
`gate_sandbox` mantiene señal de calidad en entornos sin todas las dependencias disponibles.

## Seguridad / Privacidad
- **PII encryption** opcional en reposo para columnas sensibles (SQLite + variables de entorno).
- **Logging guardrails** para evitar exposición de PII en auditoría y trazas.
- **Secrets scan** integrado en gate completo (gitleaks).
- **Dependency scanning** con `pip-audit` y política explícita de allowlist.

## Arquitectura (C4 mínimo)
Diagrama rápido (contexto + contenedores):

```mermaid
flowchart LR
    subgraph Personas
        recepcion[Recepción]
        coordinacion[Coordinación médica]
        analista[Analista BI]
    end

    subgraph ClinicDesk
        ui[Presentación\nPySide6 + CLI]
        app[Aplicación\nCasos de uso + puertos]
        domain[Dominio\nReglas de negocio]
        infra[Infraestructura\nSQLite/JSON adapters]
    end

    pbi[Power BI]
    recepcion --> ui
    coordinacion --> ui
    ui --> app --> domain
    app --> infra
    infra --> pbi
    analista --> pbi
```

Decisiones técnicas clave:
- Clean Architecture estricta (dependencias desde presentación/infra hacia aplicación/dominio).
- Puertos/adaptadores para desacoplar casos de uso de persistencia concreta.
- Artefactos versionados con hashes para trazabilidad y reproducibilidad.

Más detalle C4 (contexto, contenedores y componentes): [docs/arquitectura_c4.md](docs/arquitectura_c4.md).

## Release bundle (atajo)
- Bundle reproducible disponible con `python -m scripts.build_release`.

## 🚀 Getting Started

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

### Ejecutar la app

```bash
python scripts/run_app.py
```

### Deploy con Docker (API opcional)

```bash
docker compose up --build
```

Verifica healthcheck:

```bash
curl http://localhost:8000/healthz
```


## Docker (API opcional)

Esta API REST opcional es **read-only** y no forma parte del flujo principal de escritorio. No expone PII en claro: documento/teléfono/email y nombre de paciente se devuelven redaccionados.

Levantar entorno local con un comando:

```bash
docker compose up --build
```

Verificación rápida:

```bash
curl http://localhost:8000/healthz
curl -H "X-API-Key: dev_key_local" "http://localhost:8000/api/v1/citas?desde=2026-01-01&hasta=2026-01-31&estado=PENDIENTE&texto=control"
```

Variables por defecto en `docker-compose.yml`:
- `CLINICDESK_API_KEY=dev_key_local`
- `CLINICDESK_DB_PATH=/data/clinicdesk.sqlite3`

## API opcional

También puedes arrancar sin Docker:

- Arranque API: `python -m clinicdesk.web.api.serve`
- Arranque health mínimo legacy (solo `/healthz`): `python -m clinicdesk.web.serve_health`

Configura autenticación con `X-API-Key`:

```bash
export CLINICDESK_API_KEY=mi_clave_local
python -m clinicdesk.web.api.serve
```

Ejemplos `curl`:

```bash
curl http://localhost:8000/healthz
curl -H "X-API-Key: mi_clave_local" "http://localhost:8000/api/v1/citas?desde=2026-01-01&hasta=2026-01-31&estado=PENDIENTE&texto=control"
curl -H "X-API-Key: mi_clave_local" "http://localhost:8000/api/v1/pacientes?texto=ana"
```

Si `CLINICDESK_API_KEY` no está definida, la API arranca pero `/api/*` responderá `503` con mensaje de configuración.



### Evaluation Summary / Model Card ligera
El comando `export summary` genera un artefacto textual versionable para demo/CI:
- `evaluation_summary.json`: contrato estable (`schema_version=ml_eval_summary_v1`) con contexto, métricas y notas de interpretación.
- `evaluation_summary.md`: lectura rápida para entrevista (dataset, predictor, métricas test y limitaciones).

Qué mirar primero en demo técnica:
1. `context` (dataset/model/predictor y trazabilidad).
2. `metrics.test` vs `metrics.test_calibrated` para explicar calibración de threshold.
3. `interpretation` y `limitations` para comunicar alcance real y no sobre-vender resultados.
