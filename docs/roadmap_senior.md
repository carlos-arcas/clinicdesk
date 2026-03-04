# Roadmap Senior

## UI/deuda/arquitectura

- `clinicdesk/app/domain/farmacia.py`: **antes 213 LOC**, **después 21 LOC** como fachada de compatibilidad.
- `clinicdesk/app/domain/entities.py`: se mantiene como fachada de API pública (30 LOC), ahora reexportando entidades desde `domain/entidades`.

## Módulos nuevos y motivo

- `clinicdesk/app/domain/entidades/entidades_farmacia_stock.py`: separa entidades de stock (medicamentos/materiales/movimientos) para cohesión y menor acoplamiento.
- `clinicdesk/app/domain/entidades/entidades_recetas.py`: separa entidades de recetas y dispensaciones para bounded context claro y mejor testabilidad.
- `clinicdesk/app/domain/entidades/__init__.py`: punto único de re-export explícito con `__all__` estable.
