from __future__ import annotations

from datetime import date

from clinicdesk.app.application.usecases.crear_cita import CrearCitaRequest, CrearCitaUseCase
from clinicdesk.app.domain.enums import EstadoCita
from clinicdesk.app.queries.calidad_datos_queries import CalidadDatosQueries


def _crear_cita(container, seed_data, *, inicio: str, fin: str, estado: str) -> int:
    req = CrearCitaRequest(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio=inicio,
        fin=fin,
        motivo="Control",
        observaciones="",
        estado=estado,
        override=True,
        nota_override="Ajuste pruebas",
        confirmado_por_personal_id=seed_data["personal_activo_id"],
    )
    return CrearCitaUseCase(container).execute(req).cita_id


def test_calidad_datos_queries_cuenta_completas_y_faltantes(container, seed_data) -> None:
    cita_completa = _crear_cita(
        container,
        seed_data,
        inicio="2024-05-20 09:00:00",
        fin="2024-05-20 09:30:00",
        estado=EstadoCita.REALIZADA.value,
    )
    cita_sin_inicio_fin = _crear_cita(
        container,
        seed_data,
        inicio="2024-05-20 10:00:00",
        fin="2024-05-20 10:30:00",
        estado=EstadoCita.NO_PRESENTADO.value,
    )
    cita_cancelada_sin_checkin = _crear_cita(
        container,
        seed_data,
        inicio="2024-05-20 11:00:00",
        fin="2024-05-20 11:30:00",
        estado=EstadoCita.CANCELADA.value,
    )

    con = container.connection
    con.execute(
        """
        UPDATE citas
        SET check_in_at=?, consulta_inicio_at=?, consulta_fin_at=?, check_out_at=?
        WHERE id=?
        """,
        ("2024-05-20 08:55:00", "2024-05-20 09:00:00", "2024-05-20 09:20:00", "2024-05-20 09:25:00", cita_completa),
    )
    con.execute(
        """
        UPDATE citas
        SET check_in_at=?, check_out_at=?
        WHERE id=?
        """,
        ("2024-05-20 09:55:00", "2024-05-20 10:15:00", cita_sin_inicio_fin),
    )
    con.execute(
        """
        UPDATE citas
        SET consulta_inicio_at=?, consulta_fin_at=?, check_out_at=?
        WHERE id=?
        """,
        ("2024-05-20 11:05:00", "2024-05-20 11:20:00", "2024-05-20 11:25:00", cita_cancelada_sin_checkin),
    )
    con.commit()

    queries = CalidadDatosQueries(container.connection)
    total = queries.contar_citas_cerradas(desde=date(2024, 5, 20), hasta=date(2024, 5, 20))
    completas = queries.contar_completas(desde=date(2024, 5, 20), hasta=date(2024, 5, 20))
    faltantes = queries.contar_faltantes(desde=date(2024, 5, 20), hasta=date(2024, 5, 20))

    assert total == 3
    assert completas == 1
    assert faltantes.faltan_check_in == 1
    assert faltantes.faltan_inicio_fin == 1
    assert faltantes.faltan_check_out == 0
