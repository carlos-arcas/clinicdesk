# ClinicDesk — Portfolio one-pager

> Caso de estudio de producto clínico con foco en operación real, analítica ML y calidad verificable.

## Qué problema resuelve
- Prioriza citas con mayor riesgo operativo para mejorar continuidad asistencial.
- Reduce fricción en recepción/coordinación con una UI de escritorio orientada a flujo diario.
- Entrega exportables contractuales para BI sin romper trazabilidad de datos/artefactos.

## Demo en 3 minutos
- Guion corto para entrevista técnica/mixta: [docs/recruiter_kit.md](docs/recruiter_kit.md).

## Qué demuestra técnicamente
- **Clean Architecture** por capas + puertos/adaptadores ([arquitectura C4](docs/arquitectura_c4.md)).
- **Quality gates** reproducibles (local + CI): `python -m scripts.gate_pr`.
- **Seguridad y privacidad**: cifrado PII en reposo, controles de logging, escaneo de secretos/dependencias.
- **Modo sandbox** para entornos restringidos sin perder señal de calidad.

## Pruebas de calidad
- Workflow CI: [Quality Gate](.github/workflows/quality_gate.yml).
- Evidencias/reportes: [docs/quality_report.md](docs/quality_report.md), [docs/coverage.xml](docs/coverage.xml), [docs/pip_audit_report.txt](docs/pip_audit_report.txt), [docs/secrets_scan_report.txt](docs/secrets_scan_report.txt).

## Arquitectura
- Vista rápida C4: [docs/arquitectura_c4.md](docs/arquitectura_c4.md).
- Contrato de arquitectura y límites: [docs/architecture_contract.md](docs/architecture_contract.md).

## Seguridad / Privacidad
- Resumen técnico: [docs/security_hardening.md](docs/security_hardening.md), [docs/security_data_handling.md](docs/security_data_handling.md).
- Modelo de amenazas: [docs/threat_model.md](docs/threat_model.md).
- Decisión de privacidad de pacientes: [docs/decisiones/privacidad_pacientes.md](docs/decisiones/privacidad_pacientes.md).

## Cómo ejecutarlo rápido
- **Normal**
  - `python scripts/setup.py`
  - `python scripts/run_app.py`
- **Sandbox**
  - `python scripts/setup_sandbox.py`
  - `python -m scripts.gate_sandbox`

## Checklist de entrevista (qué preguntar y qué enseñar)
- **¿Cómo garantizas calidad antes de PR?**
  - Enseñar `python -m scripts.gate_pr` y el workflow `quality_gate.yml`.
- **¿Qué tan desacoplada está la arquitectura?**
  - Abrir C4 + contrato de arquitectura y explicar dependencias por capa.
- **¿Cómo tratas datos sensibles (PII)?**
  - Mostrar docs de hardening/data handling y política de logging sin PII.
- **¿Es reproducible el flujo ML?**
  - Correr demo kit y enseñar artefactos exportados/versionados.
- **¿Qué pasa en entornos limitados?**
  - Mostrar setup + gate en modo sandbox.

## Screenshots (placeholders)
- [Placeholder] Login
- [Placeholder] Agenda / Listado
- [Placeholder] Auditoría
- [Placeholder] Predicción / Export
