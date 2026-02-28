"""Servicio CSV de importación/exportación con orquestación fina."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

from clinicdesk.app.application.csv.csv_errors import CsvErrorMixin
from clinicdesk.app.application.csv.csv_io import CsvRowError, read_csv, write_csv
from clinicdesk.app.application.csv.csv_mapping import CsvMappingMixin
from clinicdesk.app.application.csv.csv_parsing import CsvParsingMixin
from clinicdesk.app.application.csv.csv_resolver import CsvResolverMixin
from clinicdesk.app.container import AppContainer


@dataclass(slots=True)
class CsvImportResult:
    created: int
    updated: int
    errors: List[CsvRowError]


class CsvService(CsvResolverMixin, CsvMappingMixin, CsvParsingMixin, CsvErrorMixin):
    def __init__(self, container: AppContainer) -> None:
        self._c = container

    def export_pacientes(self, path: str) -> None:
        headers = [
            "id", "tipo_documento", "documento", "nombre", "apellidos",
            "telefono", "email", "fecha_nacimiento", "direccion", "activo",
            "num_historia", "alergias", "observaciones",
        ]
        self._export_entities(path, headers, self._c.pacientes_repo.list_all(solo_activos=False), self._paciente_to_row)

    def export_medicos(self, path: str) -> None:
        headers = [
            "id", "tipo_documento", "documento", "nombre", "apellidos",
            "telefono", "email", "fecha_nacimiento", "direccion", "activo",
            "num_colegiado", "especialidad",
        ]
        self._export_entities(path, headers, self._c.medicos_repo.list_all(solo_activos=False), self._medico_to_row)

    def export_personal(self, path: str) -> None:
        headers = [
            "id", "tipo_documento", "documento", "nombre", "apellidos",
            "telefono", "email", "fecha_nacimiento", "direccion", "activo",
            "puesto", "turno",
        ]
        self._export_entities(path, headers, self._c.personal_repo.list_all(solo_activos=False), self._personal_to_row)

    def export_medicamentos(self, path: str) -> None:
        headers = ["id", "nombre_compuesto", "nombre_comercial", "cantidad_en_almacen", "activo"]
        self._export_entities(path, headers, self._c.medicamentos_repo.list_all(solo_activos=False), self._medicamento_to_row)

    def export_materiales(self, path: str) -> None:
        headers = ["id", "nombre", "fungible", "cantidad_en_almacen", "activo"]
        self._export_entities(path, headers, self._c.materiales_repo.list_all(solo_activos=False), self._material_to_row)

    def export_salas(self, path: str) -> None:
        headers = ["id", "nombre", "tipo", "ubicacion", "activa"]
        self._export_entities(path, headers, self._c.salas_repo.list_all(solo_activas=False), self._sala_to_row)

    def import_pacientes(self, path: str) -> CsvImportResult:
        return self._import_entities(
            path=path,
            required=["tipo_documento", "documento", "nombre", "apellidos"],
            row_to_model=self._row_to_paciente,
            resolver=lambda row: self._resolve_person_id("pacientes", row),
            updater=self._c.pacientes_repo.update,
            creator=self._c.pacientes_repo.create,
        )

    def import_medicos(self, path: str) -> CsvImportResult:
        return self._import_entities(
            path=path,
            required=["tipo_documento", "documento", "nombre", "apellidos"],
            row_to_model=self._row_to_medico,
            resolver=self._resolve_medico_id,
            updater=self._c.medicos_repo.update,
            creator=self._c.medicos_repo.create,
        )

    def import_personal(self, path: str) -> CsvImportResult:
        return self._import_entities(
            path=path,
            required=["tipo_documento", "documento", "nombre", "apellidos"],
            row_to_model=self._row_to_personal,
            resolver=lambda row: self._resolve_person_id("personal", row),
            updater=self._c.personal_repo.update,
            creator=self._c.personal_repo.create,
        )

    def import_medicamentos(self, path: str) -> CsvImportResult:
        return self._import_entities(
            path=path,
            required=["nombre_compuesto", "nombre_comercial"],
            row_to_model=self._row_to_medicamento,
            resolver=self._resolve_medicamento_id,
            updater=self._c.medicamentos_repo.update,
            creator=self._c.medicamentos_repo.create,
        )

    def import_materiales(self, path: str) -> CsvImportResult:
        return self._import_entities(
            path=path,
            required=["nombre", "fungible"],
            row_to_model=self._row_to_material,
            resolver=self._resolve_material_id,
            updater=self._c.materiales_repo.update,
            creator=self._c.materiales_repo.create,
        )

    def import_salas(self, path: str) -> CsvImportResult:
        return self._import_entities(
            path=path,
            required=["nombre", "tipo"],
            row_to_model=self._row_to_sala,
            resolver=self._resolve_sala_id,
            updater=self._c.salas_repo.update,
            creator=self._c.salas_repo.create,
        )

    def _export_entities(self, path: str, headers: list[str], entities, serializer: Callable[[object], Dict[str, object]]) -> None:
        write_csv(path, headers=headers, rows=[serializer(entity) for entity in entities])

    def _import_entities(
        self,
        *,
        path: str,
        required: list[str],
        row_to_model: Callable[[Dict[str, str]], object],
        resolver: Callable[[Dict[str, str]], int | None],
        updater: Callable[[object], object],
        creator: Callable[[object], object],
    ) -> CsvImportResult:
        data = read_csv(path, required_headers=required)
        created = 0
        updated = 0
        errors = list(data.errors)

        for row_number, row in enumerate(data.rows, start=2):
            try:
                entity = row_to_model(row)
                existing_id = resolver(row)
                if existing_id:
                    entity.id = existing_id
                    updater(entity)
                    updated += 1
                else:
                    creator(entity)
                    created += 1
            except Exception as exc:  # noqa: BLE001
                errors.append(CsvRowError(row_number, self._format_row_error(exc), row))

        return CsvImportResult(created=created, updated=updated, errors=errors)
