# Pruebas y quality gate

## Preparar entorno
```bash
python scripts/setup.py
```

Si prefieres hacerlo manualmente:

```bash
python -m venv .venv
. .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Comandos canónicos
- Suite rápida: `pytest -q`
- Gate rápido: `python -m scripts.gate_rapido`
- Gate completo: `python -m scripts.gate_pr`

## Subconjuntos útiles
### Core sin UI
```bash
pytest -q -m "not ui"
```

### Guardrails estructurales
```bash
pytest -q tests/guardrails
```

### UI headless
```bash
QT_QPA_PLATFORM=offscreen pytest -q -m "uiqt"
```

## Qué protege el gate
- Lint y formato.
- Typecheck incremental.
- Tests rápidos y cobertura mínima del core.
- Guardrails estructurales, secretos, PII y artefactos.
- Verificación de documentación contractual y checklist funcional.

## Regla operativa
Antes de abrir PR hay que ejecutar `python -m scripts.gate_pr` y repetir el ciclo hasta que quede en verde.
