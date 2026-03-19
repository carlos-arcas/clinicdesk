# ClinicDesk

![Python >=3.11](https://img.shields.io/badge/python-%3E%3D3.11-3776AB?logo=python&logoColor=white)

ClinicDesk es una aplicación desktop en Python + PySide6 para la operación clínica diaria. El repositorio incluye una API HTTP opcional y de solo lectura para integraciones puntuales, pero el producto principal es la aplicación de escritorio.

## Producto real
- Agenda clínica, pacientes, confirmaciones, farmacia, auditoría y módulos operativos.
- Arquitectura limpia con separación entre dominio, aplicación, infraestructura y presentación.
- Logging estructurado y gates de calidad para trazabilidad operativa.

## Arranque de la aplicación desktop
### Preparación del entorno
```bash
python scripts/setup.py
```

### Ejecución
```bash
python scripts/run_app.py
```

## Comandos canónicos de calidad
- Gate rápido: `python -m scripts.gate_rapido`
- Gate completo PR/CI: `python -m scripts.gate_pr`
- Doctor de entorno: `python -m scripts.doctor_entorno_calidad`
- Lint: `python -m scripts.lint_all`
- Formato: `python -m scripts.format_all`

CI debe ejecutar exactamente `python -m scripts.gate_pr`.

## API opcional de solo lectura
La API no redefine el producto. Solo expone healthcheck e integraciones de consulta.

### Arranque local
```bash
python -m clinicdesk.web.api.serve
```

### Healthcheck mínimo
```bash
python -m clinicdesk.web.serve_health
```

Variables relevantes:
- `CLINICDESK_API_KEY`: clave para endpoints `/api/*`.
- `CLINICDESK_DB_PATH`: ruta SQLite usada por la API.
- `CLINICDESK_WEB_MODE=api|healthz`: modo HTTP auxiliar.
- `CLINICDESK_WEB_PORT`: puerto HTTP auxiliar.

## Documentación útil
- Arquitectura: [docs/architecture_contract.md](docs/architecture_contract.md)
- Pruebas: [docs/TESTING.md](docs/TESTING.md)
- Gate y CI: [docs/ci_quality_gate.md](docs/ci_quality_gate.md)
- Seguridad: [docs/security_hardening.md](docs/security_hardening.md)
- Checklist funcional: [docs/features.md](docs/features.md)
