from __future__ import annotations

from datetime import datetime

import pytest

from clinicdesk.app.application.usecases.obtener_detalle_cita import DetalleCitaNoEncontradaError, ObtenerDetalleCita
from clinicdesk.app.domain.citas import Cita, EstadoCita
from clinicdesk.app.domain.enums import TipoDocumento, TipoSala
from clinicdesk.app.domain.modelos import Medico, Paciente, Personal, Sala
from clinicdesk.app.infrastructure.sqlite.repos_citas import CitasRepository
from clinicdesk.app.queries.historial_paciente_queries import HistorialPacienteQueries


def _crear_cita_base(container, sufijo: str = "A") -> int:
    paciente_id = container.pacientes_repo.create(
        Paciente(
            tipo_documento=TipoDocumento.DNI,
            documento=f"3333333{sufijo}",
            nombre="Rosa",
            apellidos="Luna",
            telefono="611111111",
            email="rosa@example.com",
            fecha_nacimiento=None,
            direccion=None,
            activo=True,
            num_historia=None,
            alergias=None,
            observaciones=None,
        )
    )
    medico_id = container.medicos_repo.create(
        Medico(
            tipo_documento=TipoDocumento.DNI,
            documento=f"4444444{sufijo}",
            nombre="Mario",
            apellidos="Gil",
            telefono="622222222",
            email=None,
            fecha_nacimiento=None,
            direccion=None,
            activo=True,
            num_colegiado=f"COL-44-{sufijo}",
            especialidad="General",
        )
    )
    sala_id = container.salas_repo.create(
        Sala(nombre=f"Consulta D {sufijo}", tipo=TipoSala.CONSULTA, ubicacion="P2", activa=True)
    )
    cita_repo = CitasRepository(container.connection)
    return cita_repo.create(
        Cita(
            paciente_id=paciente_id,
            medico_id=medico_id,
            sala_id=sala_id,
            inicio=datetime.fromisoformat("2025-02-10 11:00:00"),
            fin=datetime.fromisoformat("2025-02-10 11:30:00"),
            estado=EstadoCita.EN_CURSO,
            motivo="Revisión",
            notas="Informe completo de la cita para seguimiento clínico.",
        )
    )


def test_obtener_detalle_cita_devuelve_informe_completo_y_joins(container) -> None:
    cita_id = _crear_cita_base(container)

    queries = HistorialPacienteQueries(container.connection)
    detalle = queries.obtener_detalle_cita(cita_id)

    assert detalle is not None
    assert detalle.id == cita_id
    assert detalle.paciente == "Rosa Luna"
    assert detalle.medico == "Mario Gil"
    assert detalle.sala == "Consulta D A"
    assert detalle.informe == "Informe completo de la cita para seguimiento clínico."


def test_obtener_detalle_cita_incidencias_filtra_por_cita_id(container) -> None:
    cita_id = _crear_cita_base(container, "A")
    otra_cita_id = _crear_cita_base(container, "B")
    personal_id = container.personal_repo.create(
        Personal(
            tipo_documento=TipoDocumento.DNI,
            documento="55555555",
            nombre="Nora",
            apellidos="Paz",
            telefono="633333333",
            email=None,
            fecha_nacimiento=None,
            direccion=None,
            activo=True,
            puesto="Administración",
            turno="Mañana",
        )
    )
    con = container.connection
    con.execute(
        """
        INSERT INTO incidencias (
            tipo, severidad, estado, fecha_hora, descripcion,
            medico_id, personal_id, cita_id, confirmado_por_personal_id, nota_override, activo
        ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, 1)
        """,
        (
            "CITA",
            "MEDIA",
            "ABIERTA",
            "2025-02-10 11:05:00",
            "Paciente llegó tarde",
            personal_id,
            cita_id,
            personal_id,
            "validado",
        ),
    )
    con.execute(
        """
        INSERT INTO incidencias (
            tipo, severidad, estado, fecha_hora, descripcion,
            medico_id, personal_id, cita_id, confirmado_por_personal_id, nota_override, activo
        ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, 1)
        """,
        (
            "CITA",
            "BAJA",
            "CERRADA",
            "2025-02-10 11:06:00",
            "Incidencia de otra cita",
            personal_id,
            otra_cita_id,
            personal_id,
            "validado",
        ),
    )
    con.commit()

    detalle = HistorialPacienteQueries(con).obtener_detalle_cita(cita_id)

    assert detalle is not None
    assert detalle.total_incidencias == 1
    assert len(detalle.incidencias) == 1
    assert detalle.incidencias[0].resumen == "Paciente llegó tarde"


def test_obtener_detalle_cita_usecase_devuelve_dto(container) -> None:
    cita_id = _crear_cita_base(container)
    uc = ObtenerDetalleCita(HistorialPacienteQueries(container.connection))

    dto = uc.execute(cita_id)

    assert dto.id == cita_id
    assert dto.informe.startswith("Informe completo")


def test_obtener_detalle_cita_usecase_lanza_error_si_no_existe(container) -> None:
    uc = ObtenerDetalleCita(HistorialPacienteQueries(container.connection))

    with pytest.raises(DetalleCitaNoEncontradaError):
        uc.execute(999_999)
