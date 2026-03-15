# Seguro clínica fase 8: panel ejecutivo, cohortes y campañas accionables

## Qué añade esta fase

Esta fase incorpora una capa **ejecutiva comercial operativa** sobre el módulo de seguros:

- Resumen global de cartera con foco en funnel, conversiones y renovaciones.
- Cohortes accionables por segmento, plan, fit, objeción, sensibilidad y origen.
- Campañas por lotes explicables con IDs de oportunidad asociados.
- Integración en la pantalla de seguros para pasar de lectura analítica a acción.

## Cómo interpretar el panel ejecutivo

### 1) Qué mirar primero

1. **Ratio de conversión global** (si hay muestra suficiente).
2. **Pospuestas y rechazadas** para detectar atascos del embudo.
3. **Renovaciones en riesgo** (<= 21 días) para proteger cartera activa.

### 2) Cohortes que suelen merecer atención

- Objeción `PRECIO_PERCIBIDO_ALTO` con tamaño relevante.
- Sensibilidad `ALTA` cuando hay oferta enviada o seguimiento abierto.
- Fit `ALTO` sin cierre comercial.

### 3) Uso prudente de campañas

Las campañas de esta fase no automatizan mensajes: devuelven lotes priorizados y explicables.

- **Seguimiento de fit alto sin cierre**.
- **Sensibles a precio con oferta activa**.
- **Renovaciones críticas de la semana**.
- **Oportunidades estancadas con potencial**.

## Enlace con operativa diaria

1. Refrescar cartera para recalcular resumen y cohortes.
2. Elegir campaña sugerida.
3. Aplicar campaña para cargar oportunidad activa del lote.
4. Registrar gestión en cola operativa.

## Decisiones que habilita

- Dónde invertir esfuerzo comercial esta semana.
- Qué objeciones atacar con argumentario específico.
- Qué renovaciones escalar primero para evitar fuga.

## Limitaciones honestas

- Ratios se bloquean con muestra insuficiente (guardrail de prudencia).
- No hay automatización masiva de contacto en esta fase.
- No sustituye BI histórico; es panel operativo para acción comercial inmediata.
