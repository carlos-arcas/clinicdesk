# Seguro clínica fase 7: cola comercial accionable y trabajo diario

## Qué añade esta fase

Se incorpora una **cola operativa diaria** para seguros que cierra el bucle:
recomendación → prioridad → acción → seguimiento → reanudación.

### Capacidades nuevas

- Cola tipada (`ItemColaComercialSeguro`, `ColaTrabajoSeguro`) con prioridad y motivo explicable.
- Estados operativos diarios (`PENDIENTE`, `EN_CURSO`, `POSPUESTO`, `PENDIENTE_DOCUMENTACION`, `RESUELTO`, `DESCARTADO`).
- Registro de acción operativa con trazabilidad (acción, nota, siguiente paso, timestamp).
- Priorización operativa que combina scoring comercial, riesgo de renovación y vencimientos.
- Enfoque explícito de renovaciones para no esconder casos críticos.
- Vista UI de bandeja con filtros y acciones rápidas.

## Cómo leer prioridades

- **MUY_PRIORITARIA**: actuar hoy. Suele implicar renovación vencida o riesgo alto.
- **PRIORITARIA**: actuar en este turno de trabajo.
- **SECUNDARIA**: mantener seguimiento sin desplazar casos calientes.
- **NO_PRIORITARIA**: observar; no invertir esfuerzo activo por ahora.

Cada item explica el porqué (ej.: scoring alto + seguimiento vencido + riesgo renovación alto).

## Cómo usar la cola comercial

1. Refrescar cartera para cargar ranking operativo.
2. Filtrar por estado operativo cuando se quiera trabajar por lotes.
3. Revisar `motivo` y `siguiente acción` de cada item.
4. Registrar acción rápida con nota corta y siguiente paso.
5. Volver más tarde y retomar desde historial operativo reciente.

## Guía rápida de trabajo diario

### Qué hacer primero cada día

- Atender items `MUY_PRIORITARIA`.
- Resolver seguimientos vencidos.
- Validar renovaciones próximas con riesgo alto.

### Cómo leer una renovación prioritaria

- Si el item marca vencido o riesgo alto, priorizar llamada/revisión.
- Registrar resultado operativo, incluso si no hay cierre comercial definitivo.

### Cómo trabajar oportunidades con objeciones

- Usar la acción sugerida como guía.
- Registrar nota de objeción y siguiente paso concreto para continuidad.

### Cómo no perder seguimiento

- No dejar item sin estado operativo.
- Si falta documentación, marcar `PENDIENTE_DOCUMENTACION`.
- Si se pospone, registrar fecha/acción de reactivación en siguiente paso.

## Límites actuales

- La cola no automatiza decisiones comerciales finales.
- El scoring sigue siendo orientativo y prudente.
- Esta fase prioriza operativa diaria; no reemplaza estrategia comercial.
