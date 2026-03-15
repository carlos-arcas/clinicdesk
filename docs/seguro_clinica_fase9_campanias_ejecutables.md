# Seguro clínica fase 9: campañas ejecutables, lote congelado y atribución operativa

## Qué se añade

Esta fase convierte las campañas sugeridas en **entidades ejecutables** con trazabilidad real:

- `CampaniaSeguro` como unidad de trabajo comercial por lote.
- `ItemCampaniaSeguro` por oportunidad objetivo.
- `CriterioCampaniaSeguro` congelado al crear la campaña.
- resultado agregado de campaña con avance y conversión.
- persistencia SQLite dedicada para campañas e items.

## Flujo operativo

1. Seleccionar una campaña sugerida en panel ejecutivo.
2. Crear campaña ejecutable (se congela snapshot de ids objetivo).
3. Trabajar cada item del lote registrando acción, estado y resultado.
4. Consultar resultado agregado para medir avance y conversión.

## Qué se mide (atribución prudente)

- items trabajados,
- convertidos,
- rechazados,
- pendientes,
- ratio de conversión de trabajados,
- ratio de avance sobre lote.

Esto permite comparar qué campaña funcionó mejor sin inferir causalidad fuerte.

## Qué NO concluye automáticamente

- No se afirma causalidad clínica/comercial absoluta.
- No se ejecuta mensajería masiva automática.
- No se mezcla la campaña con la cola operativa individual; conviven y se relacionan por `id_oportunidad`.

## Preparación para ML y optimización

La traza de `criterio + snapshot + secuencia de resultados por item` habilita futuras fases para:

- ranking de campañas por efectividad,
- análisis de cohortes accionables con feedback real,
- diseño de siguiente mejor acción comercial por segmento.

## Mini guía

### Cómo pasar de cohorte/sugerencia a campaña

- usar la sugerencia actual del panel ejecutivo,
- crear campaña ejecutable,
- validar tamaño del lote congelado.

### Cómo trabajar un lote

- abrir campaña,
- seleccionar item,
- registrar estado + resultado + nota,
- repetir hasta cerrar lote.

### Cómo leer resultado de campaña

- `ratio_avance`: cobertura operativa del lote,
- `ratio_conversion`: efectividad sobre items trabajados.

### Cómo reutilizar en cola operativa

- mantener gestión diaria en cola existente,
- usar campaña para objetivos tácticos por cohortes,
- correlacionar ambas trazas por `id_oportunidad`.
