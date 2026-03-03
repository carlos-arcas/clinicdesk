from __future__ import annotations

from datetime import datetime

from clinicdesk.app.application.citas.filtros import FiltrosCitasDTO
from clinicdesk.app.application.usecases.crear_cita import CrearCitaRequest, CrearCitaUseCase
from clinicdesk.app.domain.enums import EstadoCita
from clinicdesk.app.pages.citas.estado_cita_presentacion import etiqueta_estado_cita
from clinicdesk.app.pages.citas.riesgo_ausencia_ui import construir_dtos_desde_listado
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


def test_citas_listado_incluye_ids_para_prediccion(container, seed_data) -> None:
    cita_id = _crear_cita(
        container,
        seed_data,
        inicio="2024-05-22 09:00:00",
        fin="2024-05-22 09:30:00",
        estado=EstadoCita.PROGRAMADA.value,
        motivo="Control agenda",
    )

    rows = CitasQueries(container).search_listado(
        desde="2024-05-20",
        hasta="2024-05-31",
        texto="",
        estado="TODOS",
    )

    assert rows[0].id == cita_id
    assert rows[0].paciente_id == seed_data["paciente_activo_id"]
    assert rows[0].medico_id == seed_data["medico_activo_id"]

    dtos = construir_dtos_desde_listado(rows, hoy=datetime(2024, 5, 20, 8, 0, 0))
    assert dtos[0].id == cita_id
    assert dtos[0].paciente_id == seed_data["paciente_activo_id"]


def test_buscar_citas_listado_filtra_por_calidad_datos(container, seed_data) -> None:
    cita_sin_checkin = _crear_cita(
        container,
        seed_data,
        inicio="2024-05-20 09:00:00",
        fin="2024-05-20 09:30:00",
        estado=EstadoCita.REALIZADA.value,
        motivo="Sin checkin",
    )
    cita_sin_inicio_fin = _crear_cita(
        container,
        seed_data,
        inicio="2024-05-20 10:00:00",
        fin="2024-05-20 10:30:00",
        estado=EstadoCita.NO_PRESENTADO.value,
        motivo="Sin inicio fin",
    )
    cita_sin_salida = _crear_cita(
        container,
        seed_data,
        inicio="2024-05-20 11:00:00",
        fin="2024-05-20 11:30:00",
        estado=EstadoCita.CANCELADA.value,
        motivo="Sin salida",
    )

    con = container.connection
    con.execute(
        "UPDATE citas SET consulta_inicio_at=?, consulta_fin_at=?, check_out_at=? WHERE id=?",
        ("2024-05-20 09:05:00", "2024-05-20 09:20:00", "2024-05-20 09:25:00", cita_sin_checkin),
    )
    con.execute(
        "UPDATE citas SET check_in_at=?, check_out_at=? WHERE id=?",
        ("2024-05-20 09:55:00", "2024-05-20 10:35:00", cita_sin_inicio_fin),
    )
    con.execute(
        "UPDATE citas SET check_in_at=?, consulta_inicio_at=?, consulta_fin_at=? WHERE id=?",
        ("2024-05-20 10:55:00", "2024-05-20 11:00:00", "2024-05-20 11:20:00", cita_sin_salida),
    )
    con.commit()

    queries = CitasQueries(container)
    columnas = ("estado",)

    def _buscar(filtro_calidad: str) -> list[int]:
        rows, _ = queries.buscar_citas_listado(
            FiltrosCitasDTO(
                rango_preset="PERSONALIZADO",
                desde=datetime(2024, 5, 20, 0, 0, 0),
                hasta=datetime(2024, 5, 20, 23, 59, 59),
                filtro_calidad=filtro_calidad,
            ),
            columnas,
            100,
            0,
        )
        return [int(item["cita_id"]) for item in rows]

    assert _buscar("SIN_CHECKIN") == [cita_sin_checkin]
    assert _buscar("SIN_INICIO_FIN") == [cita_sin_inicio_fin]
    assert _buscar("SIN_SALIDA") == [cita_sin_salida]
