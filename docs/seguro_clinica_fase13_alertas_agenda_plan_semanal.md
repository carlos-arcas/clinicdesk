# ClinicDesk Seguros · Fase 13 · Alertas proactivas, agenda comercial y plan semanal

## Qué añade esta fase

Esta fase incorpora una capa operativa que transforma la analítica comercial existente en trabajo accionable para el equipo:

- alertas proactivas explicables,
- agenda comercial semanal,
- plan de prioridades diarias,
- control de tareas vencidas y en riesgo,
- acciones rápidas para no perder foco.

## Reglas de alerta activas

El motor genera alertas con reglas prudentes para evitar ruido:

1. **Renovación vencida sin gestión** (`RENOVACION_VENCIDA_SIN_GESTION`).
2. **Renovación próxima en <= 7 días** (`RENOVACION_MENOR_7_DIAS`).
3. **Oportunidad caliente sin toque operativo** (`OPORTUNIDAD_ALTA_PRIORIDAD_PENDIENTE`).
4. **Objetivo comercial en desvío relevante** (`DESVIO_OBJETIVO_RELEVANTE`).
5. **Campaña en ejecución sin avance** (`CAMPANIA_EN_EJECUCION_SIN_AVANCE`).
6. **Campaña recomendada no lanzada** (`SUGERENCIA_CAMPANIA_NO_EJECUTADA`).

Cada alerta incluye: tipo, prioridad, motivo, fecha objetivo, contexto y acción sugerida.

## Cómo se construye la agenda

La agenda combina de forma orquestada:

- cola operativa,
- renovaciones y recordatorios,
- forecast y desvíos de objetivos,
- campañas ejecutables y estado de avance.

De ese cruce salen:

- prioridades de hoy,
- tareas vencidas,
- tareas de semana,
- acciones rápidas de ejecución.

## Uso operativo sugerido

### Qué mirar al empezar la semana

1. Bloque de **tareas vencidas**.
2. Alertas **críticas** (renovación vencida / objetivo en riesgo).
3. Acciones rápidas propuestas.

### Qué alertas no deberías ignorar

- Renovaciones vencidas.
- Objetivos comerciales en estado `POR_DEBAJO`.
- Campañas en ejecución sin un solo item trabajado.

### Cómo priorizar entre renovación, campaña y oportunidad

Orden recomendado:

1. Renovaciones vencidas o con desfase.
2. Oportunidades calientes sin toque.
3. Campañas en ejecución sin avance.
4. Campañas sugeridas aún no lanzadas.

### Cómo usar esto sin duplicar trabajo

- Registrar estado de ejecución solo una vez desde el flujo operativo.
- Usar la agenda para decidir foco y no para replicar reportes.
- Resolver primero vencidas y después expansión de campaña.

## Limitaciones honestas

- No hay automatización de correo o conectores externos en esta fase.
- Las acciones rápidas son recomendaciones y no auto-ejecuciones.
- La trazabilidad de resolución es mínima y centrada en estado/comentario.
