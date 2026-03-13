from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from clinicdesk.app.infrastructure.sqlite.demo_seed import orchestration


@dataclass(slots=True)
class _Resultado:
    payload: dict[str, int]


class _SeederFake:
    def __init__(self) -> None:
        self._connection = object()
        self.batch_recibido = 0

    def _normalize_persist_params(self, batch_size: int, from_date: date | None, to_date: date | None):
        self.batch_recibido = batch_size
        return 3, date(2026, 1, 1), date(2026, 2, 1)

    def _persist_people(self, doctors, patients, staff):
        return [10], [20], [30]

    def _ensure_salas(self):
        return [40]

    def _persist_appointments(self, appointments, patient_ids, doctor_ids, room_ids, *, batch_size: int):
        assert batch_size == 3
        return {"ext_1": 99}

    def _persist_incidences(self, incidences_by_appointment, appointment_ids, staff_ids, *, batch_size: int):
        assert batch_size == 3
        return 7

    def _build_result(self, **kwargs):
        return _Resultado(payload=kwargs)


def test_persist_demo_data_pasa_agenda_y_conteos_tipados(monkeypatch) -> None:
    seeder = _SeederFake()

    monkeypatch.setattr(orchestration, "seed_inventory", lambda *_args: (1, 2))
    monkeypatch.setattr(orchestration, "seed_recetas_dispensaciones", lambda *_args: (3, 4, 5))
    monkeypatch.setattr(orchestration, "seed_movimientos", lambda *_args: (6, 7))
    monkeypatch.setattr(orchestration, "seed_turnos_y_calendario", lambda *_args: 8)
    monkeypatch.setattr(orchestration, "seed_ausencias", lambda *_args: 9)

    result = orchestration.persist_demo_data(
        seeder=seeder,
        doctors=[],
        patients=[],
        staff=[],
        appointments=[],
        incidences_by_appointment={},
        seed=123,
        from_date=None,
        to_date=None,
        n_medicamentos=10,
        n_materiales=20,
        n_recetas=30,
        n_movimientos=40,
        turns_months=2,
        n_ausencias=3,
        batch_size=50,
    )

    assert seeder.batch_recibido == 50
    assert result.payload["meds_count"] == 1
    assert result.payload["recipes_count"] == 3
    assert result.payload["turnos_count"] == 8
    assert result.payload["doctor_ids"] == [10]
    assert result.payload["appointment_id_map"] == {"ext_1": 99}
