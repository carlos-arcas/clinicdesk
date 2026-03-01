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

## 5) Reglas obligatorias de tamaño y complejidad
Estas reglas son de cumplimiento obligatorio para código nuevo y refactorizaciones:
- **Archivo**: máximo **299 LOC** (`archivo < 300 LOC`).
- **Función o método**: máximo **39 LOC** (`función < 40 LOC`).
- **Complejidad ciclomática (CC)**: máximo **10** por función/método (`CC ≤ 10`).
- **Responsabilidad única**: cada módulo/clase/función debe tener una única razón de cambio. Si una pieza combina lectura/escritura, mapeo, validación y orquestación, debe particionarse.

## 6) Convenciones de naming y lenguaje
- Se usan **nombres en español técnico** consistentes con el dominio clínico.
- Se permiten siglas aceptadas (`DTO`, `SQL`, `UI`, `ML`) cuando mejoran legibilidad.
- Nombres deben ser explícitos sobre intención y contexto (`repositorio_pacientes`, `normalizar_telefono`, `registrar_auditoria`).
- Evitar nombres ambiguos o genéricos (`utils`, `data`, `manager`, `helper`) salvo en casos acotados y documentados.

## 7) i18n centralizada
- Todo literal visible en UI o reportes de usuario debe resolverse desde un **catálogo centralizado de i18n**.
- No hardcodear mensajes en controladores, casos de uso o repositorios.
- Claves de traducción deben seguir namespace por capa/feature (`ui.citas.estado.cancelada`, `errores.validacion.telefono`).

## 8) Logging estructurado y trazabilidad
- El logging debe ser **estructurado** (campos clave-valor), no solo texto libre.
- Campos mínimos recomendados: `evento`, `entidad`, `entidad_id`, `caso_uso`, `resultado`, `duracion_ms`, `correlation_id`.
- No registrar datos sensibles en claro (PII/secretos/tokens).
- Errores deben conservar contexto técnico mínimo para observabilidad sin filtrar información confidencial.

## 9) Política de testing obligatoria
- Todo cambio funcional o de infraestructura debe incluir pruebas automáticas.
- Cobertura mínima esperada en **core (domain + application)**: **≥ 85%**.
- Cada bug corregido debe acompañarse de test de regresión.
- Refactors estructurales deben mantener o mejorar cobertura y no degradar la suite existente.

## 10) Criterio de salida para refactorizaciones
- No se considera terminado un refactor si:
  - rompe contratos públicos sin plan de migración,
  - aumenta acoplamiento entre capas,
  - reduce cobertura en core por debajo de 85%,
  - introduce deuda estructural evitable frente a las reglas de tamaño/CC.
