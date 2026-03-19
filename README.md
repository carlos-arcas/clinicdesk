# ClinicDesk

![Python >=3.11](https://img.shields.io/badge/python-%3E%3D3.11-3776AB?logo=python&logoColor=white)

ClinicDesk es una aplicación de escritorio en Python + PySide6 para operación clínica diaria. El repositorio mantiene una API HTTP opcional y de solo lectura para integraciones puntuales, pero el producto principal es la app desktop.

## Qué incluye el producto
- Agenda clínica, pacientes, confirmaciones, farmacia, auditoría y módulos operativos.
- Clean Architecture con separación entre dominio, aplicación, infraestructura y presentación.
- Quality gates, controles de seguridad y logging estructurado para trazabilidad operativa.

## Ejecutar la aplicación desktop
### Setup
```bash
python scripts/setup.py
```

### Arranque
```bash
python scripts/run_app.py
```

## Calidad y mantenimiento
Comandos canónicos:

- Gate rápido: `python -m scripts.gate_rapido`
- Gate completo de PR/CI: `python -m scripts.gate_pr`
- Doctor de entorno: `python -m scripts.doctor_entorno_calidad`
- Lint: `python -m scripts.lint_all`
- Formato: `python -m scripts.format_all`

CI debe ejecutar exactamente `python -m scripts.gate_pr`.

## API opcional de solo lectura
La API no redefine el producto. Existe para healthcheck e integraciones puntuales de consulta.

### Arranque local
```bash
python -m clinicdesk.web.api.serve
```

### Healthcheck mínimo
```bash
python -m clinicdesk.web.serve_health
```

### Arranque con Docker
```bash
docker compose up --build
```

Variables relevantes:
- `CLINICDESK_API_KEY`: clave para endpoints `/api/*`.
- `CLINICDESK_DB_PATH`: ruta SQLite usada por la API.
- `CLINICDESK_WEB_MODE=api|healthz`: modo del contenedor raíz.
- `CLINICDESK_WEB_PORT`: puerto HTTP del contenedor raíz.

## Documentación útil
- Arquitectura: [docs/architecture_contract.md](docs/architecture_contract.md)
- Gate y CI: [docs/ci_quality_gate.md](docs/ci_quality_gate.md)
- Pruebas: [docs/TESTING.md](docs/TESTING.md)
- Seguridad: [docs/security_hardening.md](docs/security_hardening.md)
- Checklist funcional: [docs/features.md](docs/features.md)
