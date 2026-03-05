# Recruiter Kit (ClinicDesk)

## Qué enseñar en 3 minutos

### 0:00 - 0:30 · Contexto
- "ClinicDesk ayuda a operación clínica a priorizar citas con riesgo y exportar resultados listos para BI".
- Mensaje clave: no es solo ML, es producto mantenible (arquitectura + calidad + seguridad).

### 0:30 - 1:10 · Setup y arranque
- Normal: `python scripts/setup.py` y luego `python scripts/run_app.py`.
- Sandbox: `python scripts/setup_sandbox.py` y `python -m scripts.gate_sandbox`.
- (añadir captura aquí: pantalla inicial de la app)

### 1:10 - 2:15 · Flujo demo end-to-end
- Ejecutar demo reproducible en módulo Demo & ML:
  - `seed -> build-features -> train -> score -> drift -> export`.
- Mostrar que el flujo deja artefactos versionados y auditables.
- (añadir captura aquí: progreso del pipeline)

### 2:15 - 2:45 · Resultado de negocio
- Abrir `exports/` y enseñar CSV contractuales para Power BI:
  - `features_export.csv`
  - `model_metrics_export.csv`
  - `scoring_export.csv`
  - `drift_export.csv`
- (añadir captura aquí: carpeta exports o preview de CSV)

### 2:45 - 3:00 · Cierre técnico
- Enseñar comando de gate estricto: `python -m scripts.gate_pr`.
- Cierre: "arquitectura limpia + quality gates + seguridad/privacidad + datos exportables".

## Qué decisiones técnicas resaltar
- **Clean Architecture estricta**: dominio y casos de uso desacoplados de frameworks.
- **Ports & Adapters**: infraestructura intercambiable sin romper contratos de aplicación.
- **Determinismo**: pipeline y artefactos versionados con hashing para trazabilidad.
- **Contrato de calidad canónico**: CI y PR validan con `python -m scripts.gate_pr`.
- **Seguridad aplicada**: guardrails de logging, escaneo de secretos y auditoría de dependencias.

## Qué trade-offs comentar
- **Velocidad vs robustez**: más checks en gate completo, pero menos riesgo de regresiones.
- **Simplicidad local vs extensibilidad**: SQLite/JSON facilitan demo y portabilidad, a cambio de límites de escala.
- **Separación por capas vs curva inicial**: más estructura al inicio, mayor mantenibilidad en crecimiento.
- **Pipeline offline reproducible vs serving online**: foco en trazabilidad y entregables BI antes de inferencia en tiempo real.

## Frases cortas para entrevista
- "Este repo demuestra criterio de ingeniería, no solo un modelo que corre".
- "El valor está en la reproducibilidad y en contratos estables para negocio".
- "Puedo explicar decisiones, límites y cómo escalarlo sin romper arquitectura".
