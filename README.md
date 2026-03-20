# ClinicDesk

![Python >=3.11](https://img.shields.io/badge/python-%3E%3D3.11-3776AB?logo=python&logoColor=white)

ClinicDesk es una aplicación desktop en Python + PySide6 para la operación clínica diaria. El repositorio soporta exclusivamente la experiencia de escritorio y sus flujos de calidad asociados.

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

## Variables relevantes
- `CLINICDESK_DB_PATH`: ruta SQLite usada por la aplicación desktop y utilidades de soporte.

## Documentación útil
- Arquitectura: [docs/architecture_contract.md](docs/architecture_contract.md)
- Pruebas: [docs/TESTING.md](docs/TESTING.md)
- Gate y CI: [docs/ci_quality_gate.md](docs/ci_quality_gate.md)
- Seguridad: [docs/security_hardening.md](docs/security_hardening.md)
- Checklist funcional: [docs/features.md](docs/features.md)
