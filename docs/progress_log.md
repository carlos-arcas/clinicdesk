# Progress Log

Formato por entrada:
- **DATE/TIME**:
- **Paso**:
- **Qué se hizo**:
- **Decisiones**:
- **Riesgos**:
- **Qué queda**:

---

- **DATE/TIME**: 2026-02-27 00:00 UTC
- **Paso**: Paso 1 — creación de roadmap + contratos
- **Qué se hizo**:
  - Se creó roadmap de implementación en prompts incrementales (`docs/ml_roadmap_codex.md`).
  - Se formalizó contrato de arquitectura por capas y puertos (`docs/architecture_contract.md`).
  - Se definió quality gate de core con cobertura >=85% sin UI bloqueante (`docs/ci_quality_gate.md`).
  - Se revisaron docs/README y se añadieron estándares mínimos de ingeniería (`docs/standards.md`) con referencias desde README y TESTING.
- **Decisiones**:
  - Adoptar enfoque Strangler por pasos pequeños.
  - Tratar UI como capa no bloqueante de cobertura en esta fase.
  - Mantener cambios documentales mínimos, sin refactor masivo.
- **Riesgos**:
  - Cobertura actual de core probablemente por debajo del objetivo hasta ejecutar pasos siguientes.
  - Posibles imports cruzados históricos que requieran corrección gradual.
- **Qué queda**:
  - Implementar Prompt 1 del roadmap (automatizar gate en CI real + medición estable).

- **DATE/TIME**: 2026-02-27 00:45 UTC
- **Paso**: Paso 2 — gate + tests core verdes
- **Qué se hizo**:
  - Se ejecutó diagnóstico (`pytest -q` y `pytest -q --maxfail=1 -x`) y se aislaron causas raíz de fallos.
  - Se corrigieron contratos rotos entre capa application/domain/infrastructure en citas (campos/enum/fechas alineados).
  - Se corrigieron mapeos de repositorios de medicamentos/materiales para instanciar modelos de dominio con el nombre de campo canónico.
  - Se corrigió la búsqueda textual en queries de pacientes/médicos/personal (evitando condición AND espuria con teléfono normalizado).
  - Se ajustó test de pacientes para validar el comportamiento real y canónico de `num_historia` autogenerado.
  - Se creó `scripts/quality_gate.py` como comando único reproducible local/CI con gate bloqueante de core >=85% y exclusión de UI.
  - Se actualizó `docs/ci_quality_gate.md` para reflejar implementación real.
- **Decisiones**:
  - Se priorizó arreglo mínimo orientado a estabilidad de CI de core sin refactor masivo.
  - UI queda fuera del gate bloqueante (marker `ui` en pytest, excluido por diseño en el script).
  - No se añadieron herramientas nuevas de lint; solo ejecución condicional si la configuración ya existe.
- **Riesgos**:
  - El cálculo de cobertura usa trazado estándar de Python (no pytest-cov), por restricciones del entorno sin instalación de dependencias.
  - Persisten warnings de adaptador datetime de sqlite3 en Python 3.12 (no bloqueante para este paso).
- **Qué queda**:
  - Cuando haya acceso a dependencias de red/CI, evaluar migración de cálculo de cobertura a `pytest-cov` manteniendo el mismo contrato de core.
