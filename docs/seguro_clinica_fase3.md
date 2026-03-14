# Seguro clínica — Fase 3 (persistencia comercial operativa)

## Qué añade esta fase

- Persistencia SQLite real del funnel comercial de seguros (`seguro_oportunidades`, `seguro_ofertas`, `seguro_seguimientos`, `seguro_renovaciones`).
- Repositorio SQLite para oportunidades, ofertas, seguimientos, cierres y renovaciones.
- Historial trazable por oportunidad y listado de seguimientos recientes.
- Consultas de cartera operativa por estado, plan destino, clasificación y renovación pendiente.
- Read model base (`construir_dataset_ml_comercial`) para futura fase de ML sin introducir predicción todavía.

## Qué NO hace todavía esta fase

- No incluye modelo predictivo comercial.
- No incluye BI avanzado ni dashboards analíticos complejos.
- No implementa event sourcing completo; se usa estado consolidado + historial de seguimientos.

## Cómo trabajar la cartera

1. Crear oportunidad y preparar oferta desde servicio comercial.
2. Registrar seguimientos para trazar ciclo de vida.
3. Cerrar oportunidad con resultado comercial.
4. Consultar cartera:
   - todas las oportunidades,
   - por estado,
   - con renovación pendiente.
5. Revisar seguimientos recientes para priorización operativa.

## Cómo leer estados y seguimientos

- `estado_actual` representa el punto consolidado de la oportunidad.
- `seguro_seguimientos` almacena la secuencia de acciones comerciales con timestamp, nota y siguiente paso.
- `resultado_comercial` captura resultado final del funnel cuando aplique.

## Base preparada para ML futuro

El read model deja disponibles variables históricas de alto valor:

- plan de origen/destino,
- clasificación de motor,
- estado y resultado comercial,
- días de ciclo,
- cantidad de seguimientos,
- señal de renovación y renovación efectiva.

Esto permite en fase posterior construir features para probabilidad de conversión o riesgo de no renovación sin rediseñar persistencia.
