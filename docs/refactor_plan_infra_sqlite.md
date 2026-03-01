# Refactor plan baseline: infraestructura SQLite

## Objetivo
Preparar una línea base de refactor para `clinicdesk/app/infrastructure/sqlite` sin alterar lógica de negocio ni comportamiento visible en UI.

## Alcance de esta fase (no intrusiva)
- Documentar puntos de dolor y dependencias actuales.
- Definir estrategia de partición por componentes cohesivos.
- Establecer migración incremental compatible con UI y contratos existentes.
- Mantener quality gate sin introducir cambios funcionales.

## Hotspots priorizados (fuente: `docs/quality_report.md`)
1. `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py`
   - Sobrepasa límites de LOC por archivo.
   - Funciones con tamaño/complejidad elevada en rutas de persistencia.
2. `clinicdesk/app/infrastructure/sqlite/repos_pacientes.py`
   - Clase repositorio con exceso de responsabilidades (CRUD + mapeos + validaciones + cifrado/compatibilidad).
3. `clinicdesk/app/infrastructure/sqlite/repos_personal.py`
   - Patrón similar: agregación de múltiples responsabilidades en una sola clase.
4. `clinicdesk/app/infrastructure/sqlite/repos_recetas.py`
   - Concentración de lógica de acceso y transformación en un único módulo/clase.

## Mapa de dependencias (estado actual resumido)

### Dependencias internas más relevantes
- `demo_data_seeder.py` depende de:
  - repositorios SQLite (`repos_pacientes`, `repos_personal`),
  - DTOs/casos de uso vinculados a seed,
  - utilidades de fecha/hora y persistencia de lotes.
- `repos_pacientes.py`, `repos_personal.py`, `repos_recetas.py` dependen de:
  - contratos/entidades de domain/application,
  - conexión SQLite y utilidades de codificación/decodificación,
  - reglas de compatibilidad con estructura actual de tablas.

### Efecto arquitectónico
- Alta cohesión vertical por archivo (todo en uno), pero baja cohesión por responsabilidad.
- Acoplamiento implícito por utilidades compartidas y convenciones de mapeo dentro de cada repositorio.
- Riesgo de cambios en cascada al tocar validaciones o serialización.

## Estrategia de partición propuesta

### 1) `demo_data_seeder.py` → submódulos por contexto
Particionar en `clinicdesk/app/infrastructure/sqlite/seeder/`:
- `coordinador_seed.py`: orquestación de alto nivel.
- `seed_pacientes.py`: carga/persistencia de pacientes.
- `seed_personal.py`: carga/persistencia de personal.
- `seed_citas.py`: carga/persistencia de citas.
- `seed_incidencias.py`: carga/persistencia de incidencias.
- `normalizadores_seed.py`: funciones puras de transformación.

Regla: mantener API pública estable (fachada `DemoDataSeeder`) durante la migración.

### 2) Repositorios grandes → mixins/helpers/subrepos

#### `repos_pacientes.py`
- `PacienteLecturaMixin`: consultas/listados/búsquedas.
- `PacienteEscrituraMixin`: altas/actualizaciones/bajas lógicas.
- `PacienteCryptoMixin`: cifrado/descifrado/campos sensibles.
- `paciente_mapper.py`: traducción fila SQL <-> entidad/DTO.

#### `repos_personal.py`
- `PersonalLecturaMixin`
- `PersonalEscrituraMixin`
- `PersonalCryptoMixin`
- `personal_mapper.py`

#### `repos_recetas.py`
- `RecetaLecturaMixin`
- `RecetaEscrituraMixin`
- `receta_mapper.py`
- `receta_validaciones_sqlite.py` (solo validaciones de infraestructura)

### 3) Helpers transversales
Crear utilidades explícitas y pequeñas en `infrastructure/sqlite/common/`:
- manejo de cursores y conversión de filas,
- codecs de fecha/hora,
- utilidades de logging estructurado,
- utilidades de paginación/filtros.

## Riesgos y mitigaciones

### Riesgo 1: ruptura de contratos usados por UI
- **Mitigación**: conservar firmas públicas y nombres de clases durante fases 1 y 2.
- **Mitigación**: agregar tests de contrato por repositorio (entradas/salidas observables).

### Riesgo 2: regresiones por mover lógica de mapeo
- **Mitigación**: snapshot tests de serialización/deserialización antes de extraer mappers.
- **Mitigación**: migrar método por método con pruebas de regresión.

### Riesgo 3: divergencia de reglas de cifrado
- **Mitigación**: centralizar crypto en mixins dedicados y reforzar pruebas de campos sensibles.

### Riesgo 4: deuda temporal por clases puente
- **Mitigación**: definir fechas de retiro de puentes y checklist de eliminación al final de fase 3.

## Estrategia de migración incremental sin romper UI

### Fase 0 — Baseline (actual)
- Documentación de hotspots y reglas.
- Suite actual como red de seguridad.

### Fase 1 — Extracción interna sin cambiar API
- Mover funciones privadas a helpers/mappers.
- Reexportar desde módulos originales para mantener imports estables.

### Fase 2 — Composición por mixins/subrepos
- Reestructurar clases grandes en componentes cohesivos.
- Mantener clase pública de entrada (`PacientesRepository`, `PersonalRepository`, `RecetasRepository`).

### Fase 3 — Endurecimiento de contratos
- Añadir validaciones de límites de tamaño/CC y dependencias en quality gate.
- Eliminar código puente deprecado solo cuando no haya consumidores.

### Fase 4 — Consolidación
- Limpiar imports legacy.
- Actualizar documentación técnica y umbrales del quality gate según estado real.

## Tooling no intrusivo recomendado para ejecutar en cada fase
- `python -m compileall -q clinicdesk scripts tests`
- `python -m pytest -q -m "not ui"`
- `python scripts/quality_gate.py --strict`

## Criterios de éxito del plan
- Reducción sostenida de LOC por archivo y tamaño por función en los cuatro hotspots.
- Cero regresiones funcionales observables en UI durante la migración.
- Contratos públicos estables hasta etapa de consolidación.
- Evidencia de avance en `docs/quality_report.md` y `docs/progress_log.md`.
