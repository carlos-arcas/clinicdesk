# Architecture Contract

Este documento define el contrato de arquitectura obligatorio para `clinicdesk`.
Las reglas se validan automáticamente en `tests/test_architecture_contract.py`.

## 1. Capas oficiales

- `domain`: entidades, value objects, invariantes y errores de dominio.
- `application`: casos de uso, puertos, DTOs y servicios de aplicación.
- `infrastructure`: adaptadores técnicos (SQLite, filesystem, integraciones).
- `ui/pages`: componentes de presentación (`clinicdesk/app/ui` y `clinicdesk/app/pages`).

## 2. Reglas de dependencias (import contract)

Reglas bloqueantes:

1. `domain` **NO** puede importar `application`, `infrastructure`, `ui` ni `pages`.
2. `application` **NO** puede importar `infrastructure`, `ui` ni `pages`.
3. `infrastructure` **NO** puede importar `ui` ni `pages`.
4. `ui/pages` **NO** puede importar `domain` directamente.

Notas:

- `ui/pages` debe depender de `application` (casos de uso/facades), no del dominio.
- `infrastructure` puede depender de `application` y `domain` para implementar puertos.

## 3. Patrón Ports & Adapters (Recordatorios)

En el contexto de Recordatorios:

- **Puerto**: `clinicdesk.app.application.recordatorios.puertos.GatewayRecordatoriosCitas`
- **Adapter**: `clinicdesk.app.infrastructure.sqlite.recordatorios_citas_gateway.RecordatoriosCitasSqliteGateway`
- **Composición**: `clinicdesk.app.composicion.composicion_recordatorios.build_recordatorios_facade`

Regla obligatoria:

- Los casos de uso en `application` consumen el puerto (protocolo/interfaz).
- La implementación concreta se decide fuera de `application`, en composición.

## 4. Regla de composición (wiring)

La elección de infraestructura concreta solo se permite en:

- `clinicdesk/app/container.py`
- `clinicdesk/app/composicion/**`

Ningún módulo de `domain`, `application` o `ui/pages` debe hacer wiring de infraestructura concreta.

## 5. Política legacy y allowlist

Cuando exista acoplamiento histórico que incumpla el contrato:

1. Debe registrarse en `docs/architecture_allowlist.json`.
2. Cada entrada requiere:
   - `rule`: regla incumplida.
   - `path`: archivo afectado.
   - `imports`: módulos permitidos temporalmente.
   - `reason`: motivo explícito.
3. La allowlist es temporal y de **mínimo alcance**.
4. Toda nueva violación fuera de allowlist falla el test.
5. Cada refactor debe reducir entradas de allowlist, nunca ampliarlas sin justificación.
