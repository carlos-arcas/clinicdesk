# Contrato de arquitectura

Este repositorio mantiene una aplicación desktop en Python + PySide6. Las reglas de arquitectura se validan automáticamente en `tests/test_architecture_contract.py`.

## Capas oficiales
- `domain`: entidades, value objects, invariantes y errores de dominio.
- `application`: casos de uso, DTOs, puertos y orquestación.
- `infrastructure`: adaptadores técnicos como SQLite, filesystem e integraciones.
- `ui/pages`: presentación y wiring visual; sin lógica de negocio.

## Reglas bloqueantes de dependencias
1. `domain` no puede importar `application`, `infrastructure`, `ui` ni `pages`.
2. `application` no puede importar `infrastructure`, `ui` ni `pages`.
3. `infrastructure` no puede importar `ui` ni `pages`.
4. `ui/pages` no puede importar `domain` directamente.

## Regla de composición
La elección de infraestructura concreta solo se permite en:
- `clinicdesk/app/container.py`
- `clinicdesk/app/composicion/**`

## Política de allowlist temporal
Si aparece un acoplamiento heredado:
1. Debe registrarse en `docs/architecture_allowlist.json`.
2. Cada entrada debe indicar `rule`, `path`, `imports` y `reason`.
3. La allowlist es temporal, de mínimo alcance y debe reducirse con cada refactor.
