# CI Quality Gate (Core)

## Objetivo
Asegurar calidad continua sin bloquear por UI. El gate bloqueante aplica al **core** (domain, application, infrastructure).

## Qué ejecuta el gate
1. **Format/Lint básico**
   - Recomendado: `ruff check .` (y `ruff format --check .` cuando se incorpore).
2. **Tests unitarios/integración de core**
   - `python -m pytest -q`.
3. **Coverage de core**
   - `python -m pytest --cov=clinicdesk/app/domain --cov=clinicdesk/app/application --cov=clinicdesk/app/infrastructure --cov-report=term-missing --cov-fail-under=85`.

## Qué se ignora explícitamente
- UI/presentation fuera del gate bloqueante:
  - `clinicdesk/app/ui/**`
  - `clinicdesk/app/pages/**`
  - bootstrap puramente visual.

## Definición de “core” para coverage
- **Incluidos**:
  - `clinicdesk/app/domain`
  - `clinicdesk/app/application`
  - `clinicdesk/app/infrastructure`
- **Excluidos**:
  - `clinicdesk/app/ui`
  - `clinicdesk/app/pages`
  - utilidades de lanzamiento de app visual.

## Umbral
- Coverage mínimo bloqueante en CI para core: **85%**.

## Fast local run (developer)
1. Instalar dependencias:
   - `pip install -r requirements.txt -r requirements-dev.txt`
2. Ejecutar checks rápidos:
   - `python -m pytest -q`
3. Ejecutar gate de cobertura core:
   - `python -m pytest --cov=clinicdesk/app/domain --cov=clinicdesk/app/application --cov=clinicdesk/app/infrastructure --cov-report=term-missing --cov-fail-under=85`

## Alineación con scripts actuales
- Actualmente no existe script dedicado de quality gate en el repositorio.
- Mientras se incorpora CI formal, este documento define el contrato operativo mínimo para PRs.
