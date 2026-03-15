# Seguro Clínica Fase 12 — Forecast comercial prudente, escenarios y objetivos

## Qué proyecta esta fase

Se añade una capa ejecutiva para responder con prudencia:

- qué se espera comercialmente en 30/60/90 días,
- qué campañas y cohortes tienen mayor impacto esperado,
- qué estrategia compensa más en este ciclo,
- cómo vamos frente a objetivos operativos simples.

El forecast usa señales existentes: scoring comercial, renovaciones pendientes, campañas accionables, cohortes y priorización por valor. No se introducen modelos opacos.

## Contratos nuevos

En `clinicdesk/app/application/seguros/forecast_comercial.py` se incorporan contratos tipados:

- `ForecastComercialSeguro`
- `EscenarioComercialSeguro`
- `ObjetivoComercialSeguro`
- `DesvioObjetivoSeguro`
- `ProyeccionCampaniaSeguro`
- `ProyeccionCohorteSeguro`
- `RecomendacionEstrategicaSeguro`

## Reglas de proyección (prudentes)

1. Si la muestra es baja, la cautela sube a `ALTA`.
2. Con cautela alta, los objetivos quedan en `EVIDENCIA_INSUFICIENTE`.
3. Los escenarios aplican factores comparables sobre la misma base; no inventan causalidad.
4. La recomendación estratégica es guía operativa, no automatismo de cierre.

## Cómo leer escenarios

- **Priorizar renovaciones**: reduce fuga con menor expansión de volumen.
- **Priorizar migraciones**: busca más altas nuevas con valor más moderado.
- **Priorizar valor alto**: menos población, más valor esperado por foco.
- **Priorizar volumen**: más cobertura comercial con cautela sobre margen.

## Cómo leer desvíos vs objetivo

Estados posibles:

- `EN_LINEA`
- `POR_DEBAJO`
- `POR_ENCIMA`
- `EVIDENCIA_INSUFICIENTE`

El estado se calcula contra brecha porcentual y nivel de cautela del forecast.

## Mini guía ejecutiva

1. Mira primero el bloque de **Forecast comercial prudente**.
2. Si la cautela es alta, evita sobre-reaccionar y valida semanalmente.
3. Elige escenario por tradeoff valor/volumen, no por un único número.
4. Si hay objetivos `POR_DEBAJO`, prioriza cerrar brechas antes de escalar inversión.

## Limitaciones honestas

- No es pricing actuarial ni proyección financiera cerrada.
- No incorpora estacionalidad externa ni elasticidad real de precio.
- Requiere histórico creciente para reducir cautela y ganar estabilidad.
