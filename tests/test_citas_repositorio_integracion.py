from __future__ import annotations

from datetime import datetime

from clinicdesk.app.application.usecases.crear_cita import CrearCitaRequest, CrearCitaUseCase
from clinicdesk.app.domain.enums import EstadoCita
from clinicdesk.app.infrastructure.sqlite.repos_citas import CitasRepository


def _crear_cita(
    container,
    seed_data: dict[str, int],
    *,
    inicio: str,
    fin: str,
    estado: str,
    motivo: str,
) -> int:
    request = CrearCitaRequest(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio=inicio,
        fin=fin,
        motivo=motivo,
        estado=estado,
        override=True,
        nota_override="Coordinación valida warning no crítico",
        confirmado_por_personal_id=seed_data["personal_activo_id"],
    )
    return CrearCitaUseCase(container).execute(request).cita_id


def test_repositorio_citas_filtra_por_rango_y_excluye_borrado_logico(container, seed_data) -> None:
    en_rango = _crear_cita(
        container,
        seed_data,
        inicio="2024-05-21 08:00:00",
        fin="2024-05-21 08:20:00",
        estado=EstadoCita.PROGRAMADA.value,
        motivo="En rango",
    )
    fuera_rango = _crear_cita(
        container,
        seed_data,
        inicio="2024-05-24 08:00:00",
        fin="2024-05-24 08:20:00",
        estado=EstadoCita.PROGRAMADA.value,
        motivo="Fuera de rango",
    )

    repo = CitasRepository(container.connection)
    repo.delete(fuera_rango)

    citas = repo.list_by_medico(
        seed_data["medico_activo_id"],
        desde="2024-05-21 00:00:00",
        hasta="2024-05-21 23:59:59",
    )

    assert [cita.id for cita in citas] == [en_rango]


def test_repositorio_citas_filtra_por_estado_y_preserva_datetime(container, seed_data) -> None:
    programada_id = _crear_cita(
        container,
        seed_data,
        inicio="2024-05-22 10:00:00",
        fin="2024-05-22 10:15:00",
        estado=EstadoCita.PROGRAMADA.value,
        motivo="Programada",
    )
    realizada_id = _crear_cita(
        container,
        seed_data,
        inicio="2024-05-22 11:00:00",
        fin="2024-05-22 11:15:00",
        estado=EstadoCita.REALIZADA.value,
        motivo="Realizada",
    )

    repo = CitasRepository(container.connection)
    realizadas = repo.list_by_estado(EstadoCita.REALIZADA.value)
    ids_realizadas = {cita.id for cita in realizadas}

    assert realizada_id in ids_realizadas
    assert programada_id not in ids_realizadas

    cita = repo.get_by_id(realizada_id)
    assert cita is not None
    assert cita.inicio == datetime(2024, 5, 22, 11, 0, 0)
    assert cita.fin == datetime(2024, 5, 22, 11, 15, 0)
