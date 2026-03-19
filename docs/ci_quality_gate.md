# Quality gate de CI y PR

## Comando canónico
- Gate rápido: `python -m scripts.gate_rapido`
- Gate completo PR/CI: `python -m scripts.gate_pr`

CI debe ejecutar exactamente `python -m scripts.gate_pr`.

## Qué valida el gate completo
1. Ruff (`check` y `format --check`).
2. Typecheck incremental con mypy.
3. `pytest -q` en el scope bloqueante.
4. Cobertura mínima del core (`>= 85%`).
5. Guardrails estructurales: arquitectura, tamaño, complejidad y residuos prohibidos.
6. Seguridad: `pip-audit`, escaneo de secretos y control básico de PII en logs.
7. Documentación contractual y checklist funcional.

## Artefactos generados por el gate
- `docs/coverage.xml`
- `docs/quality_report.md`
- `docs/mypy_report.txt`
- `docs/pip_audit_report.txt`
- `docs/secrets_scan_report.txt`

## Ejecución local mínima
```bash
pip install -r requirements-dev.txt
python -m scripts.gate_pr
```

## Si falla
- Corregir el problema real.
- Reejecutar el gate completo.
- No bajar umbrales ni desactivar checks para “pasar”.
