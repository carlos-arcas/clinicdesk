# Seguro clínica fase 15: ciclo de vida de póliza y postventa operativa

## Qué añade esta fase

Esta fase introduce un subcontexto explícito de **postventa de pólizas** separado de la preventa comercial:

- Dominio de póliza activa (`PolizaSeguro`) con estado, vigencia, renovación y relación de asegurados.
- Alta de póliza desde oportunidad convertida (no desde UI directa ni cierre comercial simple).
- Base de incidencias operativas de póliza para trazabilidad postventa.
- Persistencia SQLite específica para pólizas, beneficiarios e incidencias.
- Vista en la pantalla de seguros para cartera postventa, materialización y seguimiento básico.

## Diferencia entre oportunidad comercial y póliza activa

- **Oportunidad comercial**: intención de venta/renovación comercial en pipeline.
- **Póliza activa**: contrato/adherencia materializado, con vigencia y asegurados.

Regla de negocio de esta fase: sólo se materializa póliza desde oportunidades en estado `CONVERTIDA`, `PENDIENTE_RENOVACION` o `RENOVADA`.

## Cómo leer vigencia y renovación

- `vigencia.fecha_inicio` y `vigencia.fecha_fin` representan la vida contractual de la póliza.
- `renovacion.fecha_renovacion_prevista` y `renovacion.estado` representan la renovación real de la póliza.
- En esta fase, la alta inicial crea renovación en `PENDIENTE` para iniciar operativa de seguimiento.

## Cómo usar cartera de pólizas

La cartera postventa permite filtrar por:

- estado de póliza,
- plan,
- pólizas con incidencias,
- renovación pendiente,
- proximidad de vencimiento.

Esto habilita gestión de cartera real para operaciones postventa (no sólo funnel comercial).

## Qué no cubre todavía

- Gestión completa de siniestros.
- Árbol avanzado de familiares/roles de beneficiarios.
- Reglas actuariales de prima y re-cotización en renovación.
- Motor documental integral de adjuntos.
