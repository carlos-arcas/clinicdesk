# Bounded Contexts (DDD estratégico ligero)

Este documento define límites funcionales para `clinicdesk` sin reestructuración masiva.
El objetivo es gobernar dependencias entre contextos y evitar acoplamiento accidental.

## Contextos definidos

### 1) Citas
- **Propósito:** flujo operativo de agenda, confirmaciones y recordatorios.
- **Módulos principales reales:**
  - `clinicdesk/app/application/citas/`
  - `clinicdesk/app/application/confirmaciones/`
  - `clinicdesk/app/application/recordatorios/`

### 2) Pacientes
- **Propósito:** ciclo de vida del paciente e historial clínico aplicado.
- **Módulos principales reales:**
  - `clinicdesk/app/application/pacientes_usecases.py`
  - `clinicdesk/app/application/historial_paciente/`
  - `clinicdesk/app/infrastructure/sqlite/pacientes/`

### 3) Auditoría y Seguridad
- **Propósito:** trazabilidad, autorización y políticas transversales de seguridad.
- **Módulos principales reales:**
  - `clinicdesk/app/application/auditoria/`
  - `clinicdesk/app/application/seguridad/`
  - `clinicdesk/app/application/security.py`

### 4) Preferencias
- **Propósito:** configuración funcional por usuario/sistema sin lógica de negocio clínica.
- **Módulos principales reales:**
  - `clinicdesk/app/application/preferencias/`
  - `clinicdesk/app/infrastructure/preferencias/`

### 5) ML/Demo
- **Propósito:** predicciones, entrenamiento, evaluación y datos demo.
- **Módulos principales reales:**
  - `clinicdesk/app/application/ml/`
  - `clinicdesk/app/application/prediccion_ausencias/`
  - `clinicdesk/app/application/prediccion_operativa/`
  - `clinicdesk/app/application/demo_data/`

### 6) Export
- **Propósito:** serialización/salida de datos (CSV y artefactos exportables).
- **Módulos principales reales:**
  - `clinicdesk/app/application/csv/`
  - `clinicdesk/app/application/use_cases/solicitudes/`

## Reglas de dependencia entre contextos

Reglas mínimas para gobernanza (enforced por tests):

1. `PACIENTES` **no puede importar** `ML_DEMO`.
2. `PACIENTES` **no puede importar** `EXPORT`.
3. `EXPORT` **no puede importar** `ML_DEMO`.
4. `AUDITORIA_SEGURIDAD` **no puede importar** contextos de negocio (`CITAS`, `PACIENTES`, `ML_DEMO`, `EXPORT`, `PREFERENCIAS`).
5. `ML_DEMO -> CITAS` está considerado **acoplamiento de transición** y requiere allowlist explícita con motivo.

Además del contexto, se mantienen guardarraíles globales ya existentes de Clean Architecture
(ejemplo: application/domain sin dependencias hacia UI).

## Traducción entre contextos (DTOs y puertos)

- **Citas → ML/Demo:**
  - `clinicdesk.app.application.features.citas_features` actúa como superficie de datos calculados para modelos.
  - Contrato recomendado: DTOs estables de features (sin exponer entidades UI/ORM).

- **Pacientes → Auditoría/Seguridad:**
  - Los casos de uso de pacientes invocan políticas/servicios de seguridad.
  - Contrato recomendado: puertos de autorización y eventos de auditoría desacoplados del repositorio concreto.

- **Export ↔ otros contextos:**
  - Export solo consume DTOs serializables.
  - No debe conocer controladores UI ni detalles de persistencia.

## Anti-patrones a evitar

- Imports cruzados directos entre contextos sin contrato intermedio.
- Filtración de capas UI (`pages`, `ui`, Qt) dentro de `application` o `domain`.
- Exponer modelos de infraestructura (ORM/SQLite) como contrato entre contextos.
- Reusar módulos `services` como cajón de sastre multi-contexto sin frontera explícita.
- Romper reglas mediante imports tardíos no documentados ni justificados.
