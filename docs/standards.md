# Engineering Standards (Core-First)

Este documento consolida el estándar técnico del repositorio para evolución mantenible y preparada para ML.

## Reglas obligatorias
- CI bloqueante sobre **core** con coverage >= 85%.
- Clean Architecture estricta: domain/application/infrastructure/presentation con dependencias correctas.
- Evitar monolitos y duplicación.
- Registrar avances en `docs/progress_log.md`.

## Documentos fuente
- Contrato de arquitectura: `docs/architecture_contract.md`.
- Quality gate: `docs/ci_quality_gate.md`.
- Roadmap incremental codificado en prompts: `docs/ml_roadmap_codex.md`.
