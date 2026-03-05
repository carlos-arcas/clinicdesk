# ClinicDesk — Portfolio one-pager

> Caso de estudio de producto clínico con foco en operación real, analítica ML y calidad verificable.

## Qué problema resuelve
- Prioriza citas con mayor riesgo operativo para mejorar continuidad asistencial.
- Reduce fricción en recepción/coordinación con una UI de escritorio orientada al trabajo diario.
- Entrega exportables contractuales para BI con trazabilidad de datos y artefactos.

## Demo en 3 minutos
- Guion corto para entrevista técnica/mixta: [docs/recruiter_kit.md](docs/recruiter_kit.md).

## Qué demuestra técnicamente
- **Clean Architecture** por capas + puertos/adaptadores ([C4](docs/arquitectura_c4.md)).
- **Quality gates + CI** reproducibles (local y pipeline): `python -m scripts.gate_pr`.
- **PII encryption** en reposo + controles de logging para privacidad.
- **Sandbox mode** para entornos restringidos sin perder señal de calidad.

## Pruebas de calidad
- Workflow CI: [Quality Gate](.github/workflows/quality_gate.yml).
- Artefactos/evidencias: [docs/quality_report.md](docs/quality_report.md), [docs/coverage.xml](docs/coverage.xml), [docs/pip_audit_report.txt](docs/pip_audit_report.txt), [docs/secrets_scan_report.txt](docs/secrets_scan_report.txt).

## Arquitectura
- Vista C4: [docs/arquitectura_c4.md](docs/arquitectura_c4.md).
- Contrato de arquitectura: [docs/architecture_contract.md](docs/architecture_contract.md).

## Seguridad / Privacidad
- Resumen y controles: [docs/security_hardening.md](docs/security_hardening.md), [docs/security_data_handling.md](docs/security_data_handling.md).
- Threat model + decisión de privacidad: [docs/threat_model.md](docs/threat_model.md), [docs/decisiones/privacidad_pacientes.md](docs/decisiones/privacidad_pacientes.md).

## Cómo ejecutarlo rápido
- **Normal:** `python scripts/setup.py` → `python scripts/run_app.py`.
- **Sandbox:** `python scripts/setup_sandbox.py` → `python -m scripts.gate_sandbox`.

## Checklist de entrevista
- **¿Cómo garantizas calidad antes de merge?** Enseña `scripts.gate_pr`, explica que CI ejecuta el mismo contrato y muestra el workflow Quality Gate + artefactos.
- **¿Qué tan desacoplada está la solución?** Abre el C4 y el contrato de arquitectura para justificar límites entre dominio, aplicación, infraestructura y presentación.
- **¿Cómo proteges datos sensibles?** Recorre hardening + data handling y remarca cifrado PII, logging sin PII y escaneo de secretos/dependencias.
- **¿Es reproducible la parte ML?** Corre el demo kit y muestra exportables versionados (`features`, `metrics`, `scoring`, `drift`) listos para BI.

## Screenshots (placeholders)
- [Placeholder] Login
- [Placeholder] Agenda/Listado
- [Placeholder] Auditoría
- [Placeholder] Predicción/Export
