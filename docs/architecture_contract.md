# Architecture Contract (Clean Architecture)

## 1) Capas y dependencias permitidas
- **domain**: entidades, value objects, reglas de negocio puras, eventos, excepciones de dominio.
  - **No depende de ninguna otra capa**.
- **application**: casos de uso, puertos (interfaces), DTOs de entrada/salida, orquestación de reglas.
  - Puede depender de **domain** únicamente.
- **infrastructure**: implementaciones técnicas (SQLite, filesystem, integraciones externas).
  - Puede depender de **application + domain**.
- **presentation (UI/controllers)**: pantallas/controladores/handlers.
  - Puede depender de **application**.

### Reglas de importación (ejemplos)
- ✅ `application.usecases.crear_cita` importa `domain.modelos`.
- ✅ `infrastructure.sqlite.repos_citas` importa puertos de `application`.
- ✅ `ui/controllers` importa `application.usecases`.
- ❌ `domain` importando `infrastructure`.
- ❌ `application` importando módulos de `ui`.
- ❌ `ui` llamando directamente a `infrastructure` para reglas de negocio.

## 2) Ports & Adapters estándar
- **Ubicación puertos**:
  - Lectura/escritura de negocio en `clinicdesk/app/domain/repositorios.py` (o submódulos `domain/ports/` al crecer).
  - Puertos de aplicación (feature store, inferencia ML, clock, id generator) en `clinicdesk/app/application/ports/`.
- **Convención de nombres**:
  - Puertos: `<Entidad><Acción>Port` o `<Servicio>Gateway`.
  - Adaptadores infraestructura: `<Tecnologia><Puerto>` (ej. `SqliteCitasRepository`).
- **Regla**: todo caso de uso recibe dependencias por constructor/función mediante puertos, nunca implementaciones concretas.

## 3) Modelado en domain
- **Entidades**: identidad estable + invariantes (`@dataclass(frozen=False)` si muta con método de dominio).
- **Value Objects**: inmutables, validación al construir (`@dataclass(frozen=True)`).
- **Eventos de dominio**: dataclasses inmutables con `event_id`, `occurred_at`, `payload` tipado.
- **Errores**: excepciones de dominio explícitas (sin `Exception` genérica para reglas de negocio).

## 4) Convención Use Cases (application)
- Un archivo por caso de uso, tamaño acotado, responsabilidad única.
- **Input DTO**: `NombreCasoInput` (tipado, validado superficialmente).
- **Output DTO**: `NombreCasoOutput` (sin exponer entidades internas innecesarias).
- **Errores**:
  - de dominio: propagados/controlados según política del caso.
  - de infraestructura: traducidos a errores de aplicación cuando aplique.
- **Firma recomendada**:
  - `execute(input_dto) -> output_dto`.
- **No permitido**:
  - lógica de UI dentro de use cases,
  - acceso directo a SQLite desde use cases,
  - side effects no declarados por puertos.
