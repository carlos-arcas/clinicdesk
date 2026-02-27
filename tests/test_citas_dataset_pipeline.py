from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pytest

from clinicdesk.app.application.pipelines.build_citas_dataset import (
    BuildCitasDataset,
    CitasDatasetBuildError,
    InvalidCitaTimeRangeError,
)
from clinicdesk.app.application.ports.citas_read_port import CitaReadModel
from clinicdesk.app.domain.enums import EstadoCita
from clinicdesk.app.domain.modelos import Cita
from clinicdesk.app.infrastructure.sqlite.citas_read_adapter import SqliteCitasReadAdapter


class FakeCitasReadPort:
    def __init__(self, rows: list[CitaReadModel]) -> None:
        self._rows = rows

    def list_in_range(self, desde: datetime, hasta: datetime) -> list[CitaReadModel]:
        return list(self._rows)


def test_build_citas_dataset_happy_path() -> None:
    desde = datetime(2024, 5, 20, 0, 0)
    hasta = datetime(2024, 5, 21, 23, 59)
    port = FakeCitasReadPort(
        rows=[
            CitaReadModel(
                cita_id="1",
                paciente_id=10,
                medico_id=20,
                inicio=datetime(2024, 5, 20, 9, 0),
                fin=datetime(2024, 5, 20, 9, 30),
                estado="PROGRAMADA",
                notas="Control anual",
                has_incidencias=False,
            ),
            CitaReadModel(
                cita_id="2",
                paciente_id=11,
                medico_id=20,
                inicio=datetime(2024, 5, 21, 10, 0),
                fin=datetime(2024, 5, 21, 10, 45),
                estado="REALIZADA",
                notas="Revisión",
                has_incidencias=True,
            ),
        ]
    )

    dataset = BuildCitasDataset(port).execute(desde=desde, hasta=hasta)

    assert len(dataset) == 2
    assert dataset[0].duracion_min == 30
    assert dataset[1].duracion_min == 45
    assert dataset[1].has_incidencias is True


def test_build_citas_dataset_raises_when_fin_before_inicio() -> None:
    port = FakeCitasReadPort(
        rows=[
            CitaReadModel(
                cita_id="broken",
                paciente_id=1,
                medico_id=2,
                inicio=datetime(2024, 5, 20, 10, 0),
                fin=datetime(2024, 5, 20, 9, 0),
                estado="PROGRAMADA",
            )
        ]
    )

    with pytest.raises(InvalidCitaTimeRangeError, match="anterior a inicio"):
        BuildCitasDataset(port).execute(
            desde=datetime(2024, 5, 20, 0, 0),
            hasta=datetime(2024, 5, 20, 23, 59),
        )


def test_build_citas_dataset_controls_null_notes_and_empty_incidencias() -> None:
    port = FakeCitasReadPort(
        rows=[
            CitaReadModel(
                cita_id="3",
                paciente_id=3,
                medico_id=4,
                inicio=datetime(2024, 5, 20, 11, 0),
                fin=datetime(2024, 5, 20, 11, 20),
                estado="PROGRAMADA",
                notas=None,
                has_incidencias=False,
            )
        ]
    )

    row = BuildCitasDataset(port).execute(
        desde=datetime(2024, 5, 20, 0, 0),
        hasta=datetime(2024, 5, 20, 23, 59),
    )[0]

    assert row.notas_len == 0
    assert row.has_incidencias is False


def test_build_citas_dataset_applies_date_filter_even_with_noisy_port() -> None:
    port = FakeCitasReadPort(
        rows=[
            CitaReadModel(
                cita_id="in",
                paciente_id=1,
                medico_id=1,
                inicio=datetime(2024, 5, 20, 9, 0),
                fin=datetime(2024, 5, 20, 9, 20),
                estado="PROGRAMADA",
            ),
            CitaReadModel(
                cita_id="out",
                paciente_id=1,
                medico_id=1,
                inicio=datetime(2024, 6, 1, 9, 0),
                fin=datetime(2024, 6, 1, 9, 20),
                estado="PROGRAMADA",
            ),
        ]
    )

    dataset = BuildCitasDataset(port).execute(
        desde=datetime(2024, 5, 20, 0, 0),
        hasta=datetime(2024, 5, 20, 23, 59),
    )

    assert [row.cita_id for row in dataset] == ["in"]


def test_build_citas_dataset_rejects_invalid_requested_range() -> None:
    port = FakeCitasReadPort(rows=[])

    with pytest.raises(CitasDatasetBuildError, match="Rango inválido"):
        BuildCitasDataset(port).execute(
            desde=datetime(2024, 5, 21, 0, 0),
            hasta=datetime(2024, 5, 20, 0, 0),
        )


@dataclass(slots=True)
class FakeCitasRepo:
    citas: list[Cita]
    called_with: tuple[datetime, datetime] | None = None

    def list_in_range(self, *, desde: datetime, hasta: datetime) -> list[Cita]:
        self.called_with = (desde, hasta)
        return self.citas


@dataclass(slots=True)
class FakeIncidenciasRepo:
    cita_ids_with_incidencias: set[int]

    def search(self, *, cita_id: int | None = None, **_) -> list[object]:
        if cita_id is None:
            return []
        return [object()] if cita_id in self.cita_ids_with_incidencias else []


def test_sqlite_adapter_contract_maps_repositories_to_port_model() -> None:
    cita = Cita(
        id=101,
        paciente_id=77,
        medico_id=88,
        sala_id=1,
        inicio=datetime(2024, 5, 20, 8, 0),
        fin=datetime(2024, 5, 20, 8, 30),
        estado=EstadoCita.PROGRAMADA,
        notas="Observación",
    )
    citas_repo = FakeCitasRepo(citas=[cita])
    incidencias_repo = FakeIncidenciasRepo(cita_ids_with_incidencias={101})

    adapter = SqliteCitasReadAdapter(citas_repo=citas_repo, incidencias_repo=incidencias_repo)
    desde = datetime(2024, 5, 20, 0, 0)
    hasta = datetime(2024, 5, 20, 23, 59)

    rows = adapter.list_in_range(desde=desde, hasta=hasta)

    assert citas_repo.called_with == (desde, hasta)
    assert len(rows) == 1
    assert rows[0].cita_id == "101"
    assert rows[0].estado == "PROGRAMADA"
    assert rows[0].has_incidencias is True
