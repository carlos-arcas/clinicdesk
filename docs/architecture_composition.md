# Capa de composición (`clinicdesk.app.composicion`)

La composición de dependencias de la app se concentra en módulos pequeños bajo `clinicdesk/app/composicion/`.

## Objetivo

- Mantener `container.py` como orquestador fino.
- Reducir acoplamiento entre wiring e implementación concreta.
- Facilitar cambios por contexto sin tocar todo el contenedor.

## Módulos actuales

- `composicion_repositorios_sqlite.py`: construye repositorios SQLite.
- `composicion_proveedores.py`: construye proveedores transversales de infraestructura (ej. conexión SQLite por hilo).
- `composicion_queries.py`: construye queries de lectura.
- `composicion_demo_ml.py`: construye la fachada de demo ML.
- `composicion_prediccion_ausencias.py`: construye la fachada de predicción de ausencias.
- `composicion_prediccion_operativa.py`: construye la fachada de predicción operativa.
- `composicion_recordatorios.py`: construye la fachada de recordatorios.

## Contrato recomendado

Cada módulo expone funciones `build_*` con entradas mínimas (por ejemplo `connection` o `proveedor_conexion`) y retorna objetos listos para usar.

`clinicdesk/app/container.py` solo debe:

1. Ajustar configuración básica de conexión.
2. Invocar `build_*` por contexto.
3. Ensamblar el `AppContainer`.

Con esto, dominio y aplicación siguen aislados de detalles de UI y wiring de infraestructura.


## Proveedores transversales

Los proveedores de infraestructura compartidos entre fachadas se construyen en módulos dedicados de composición para evitar lógica inline en `container.py`.

Regla práctica:
- si un proveedor se reutiliza por dos o más composiciones, su construcción vive en `composicion_proveedores.py`;
- `container.py` únicamente invoca builders y conecta resultados.

## Ports & Adapters en Recordatorios

El contexto de recordatorios aplica inversión de dependencias así:

- **Application** define el puerto `GatewayRecordatoriosCitas` en `clinicdesk/app/application/recordatorios/puertos.py`.
- **Infrastructure** implementa ese contrato con `RecordatoriosCitasSqliteGateway`.
- **Composición** (`composicion_recordatorios.py`) decide el adaptador concreto (SQLite) y lo inyecta a los casos de uso tipado como puerto.

Regla: los casos de uso de `application/usecases/recordatorios_citas.py` dependen del protocolo y no importan infraestructura concreta.

## Relación con Architecture Contract

Las reglas globales de capas, importaciones permitidas y política legacy se definen en `docs/architecture_contract.md`.
La composición debe respetar ese contrato y es el único lugar donde se decide infraestructura concreta.

