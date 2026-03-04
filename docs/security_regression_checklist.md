# Checklist de regresión de seguridad (PR reviewer)

> Objetivo: revisar cambios de seguridad sin añadir tooling nuevo obligatorio.
> Ejecutar sobre cada PR con evidencia en diff + tests/gates existentes.

## Checklist automatizable

1. [ ] **¿Se añadió logging nuevo?** Verificar ausencia de PII y trazabilidad por `reason_code` en eventos sensibles.  
   Evidencia automática: `python -m scripts.gate_pr` (incluye `check_pii_logging_guardrail`) + `tests/test_quality_gate_security.py`.
2. [ ] **¿Se añadieron `print(...)` en código productivo?** Debe usarse logging estructurado.  
   Evidencia automática: `python -m scripts.gate_pr` (incluye `check_no_print_calls`).
3. [ ] **¿Aparecieron secretos hardcodeados?** Tokens/keys/passwords no deben estar en código ni docs.  
   Evidencia automática: `python -m scripts.gate_pr` (regex secret scan + `gitleaks` en `run_secrets_scan`).
4. [ ] **¿Se añadió persistencia de datos?** Confirmar sanitización y política de minimización.  
   Evidencia automática: `tests/infrastructure/test_repositorio_preferencias_json.py` + `tests/test_seed_demo_security_guardrails.py`.
5. [ ] **¿Se modificó QuickSearch o preferencias?** Debe seguir bloqueando PII en búsquedas persistidas.  
   Evidencia automática: tests de `sanitize_search_text` en `tests/infrastructure/test_repositorio_preferencias_json.py`.
6. [ ] **¿Se añadieron o cambiaron exportaciones?** Verificar RBAC + confirmación explícita + control de PII.  
   Evidencia automática: `tests/test_exportar_auditoria_csv_usecase.py` + `tests/test_seed_demo_rbac.py`.
7. [ ] **¿Se tocó seed/reset?** Confirmar safe paths y confirmación obligatoria para acciones destructivas.  
   Evidencia automática: `tests/test_seed_demo_reset_safety.py` + `tests/test_seed_demo_security_guardrails.py`.
8. [ ] **¿Se añadió CLI nueva/comandos nuevos?** No imprimir secretos/PII; usar salida controlada.  
   Evidencia automática: `tests/test_security_cli.py` + `tests/test_ml_cli_smoke.py`.
9. [ ] **¿Se cambió manejo de claves crypto?** Mantener flujo de rotación/check y validaciones de startup.  
   Evidencia automática: `tests/test_field_crypto_startup_validation.py` + `tests/test_crypto_migrate_patients.py` + `tests/test_crypto_migrate_personal.py`.
10. [ ] **¿Se cambiaron dependencias?** Revisar vulnerabilidades y allowlist justificadas.  
    Evidencia automática: `python -m scripts.gate_pr` (incluye `pip-audit` + reporte en `docs/pip_audit_report.txt`).
11. [ ] **¿Se alteró arquitectura en módulos sensibles?** No romper límites de capas ni controles.  
    Evidencia automática: `python -m scripts.gate_pr` (incluye `scripts/structural_gate.py` y tests de arquitectura).
12. [ ] **¿Se mantiene documentación mínima de seguridad?** Threat model y checklist deben existir.  
    Evidencia automática: `python -m scripts.check_security_docs` (integrado en `python -m scripts.gate_pr`).

## Comando recomendado de verificación completa

```bash
python -m scripts.gate_pr
```
