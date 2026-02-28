from __future__ import annotations

from clinicdesk.app.application.usecases.crear_cita import CrearCitaRequest, CrearCitaUseCase
from clinicdesk.app.pages.citas.estado_cita_presentacion import etiqueta_estado_cita
from clinicdesk.app.domain.enums import EstadoCita
from clinicdesk.app.queries.citas_queries import CitasQueries


def _crear_cita(container, seed_data, *, inicio: str, fin: str, estado: str, motivo: str, notas: str = "") -> int:
    usecase = CrearCitaUseCase(container)
    req = CrearCitaRequest(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio=inicio,
        fin=fin,
        motivo=motivo,
        observaciones=notas,
        estado=estado,
        override=True,
        nota_override="Autorizado por coordinación",
        confirmado_por_personal_id=seed_data["personal_activo_id"],
    )
    return usecase.execute(req).cita_id


def test_citas_search_listado_filtra_por_rango_estado_y_texto(container, seed_data) -> None:
    _crear_cita(
        container,
        seed_data,
        inicio="2024-05-20 09:00:00",
        fin="2024-05-20 09:30:00",
        estado=EstadoCita.PROGRAMADA.value,
        motivo="Control mensual",
    )
    _crear_cita(
        container,
        seed_data,
        inicio="2024-05-21 10:00:00",
        fin="2024-05-21 10:30:00",
        estado=EstadoCita.CANCELADA.value,
        motivo="Cancelada por paciente",
    )
    _crear_cita(
        container,
        seed_data,
        inicio="2024-06-01 11:00:00",
        fin="2024-06-01 11:20:00",
        estado=EstadoCita.REALIZADA.value,
        motivo="Fuera del rango",
    )

    queries = CitasQueries(container)

    rows = queries.search_listado(
        desde="2024-05-20",
        hasta="2024-05-31",
        texto="cancelada",
        estado=EstadoCita.CANCELADA.value,
    )

    assert len(rows) == 1
    assert rows[0].estado == EstadoCita.CANCELADA.value
    assert rows[0].fecha == "2024-05-21"


def test_etiqueta_estado_cita_mapea_no_presentado() -> None:
    assert etiqueta_estado_cita(EstadoCita.NO_PRESENTADO.value) == "No asistió"
