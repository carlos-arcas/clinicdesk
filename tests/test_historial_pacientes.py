from __future__ import annotations

from datetime import date, datetime

from clinicdesk.app.application.services.pacientes_listado_contrato import ContratoListadoPacientesService
from clinicdesk.app.application.usecases.obtener_historial_paciente import ObtenerHistorialPaciente
from clinicdesk.app.domain.citas import Cita, EstadoCita
from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Medico, Paciente, Sala
from clinicdesk.app.domain.enums import TipoSala
from clinicdesk.app.infrastructure.sqlite.repos_citas import CitasRepository
from clinicdesk.app.queries.historial_paciente_queries import HistorialPacienteQueries
from clinicdesk.app.queries.recetas_queries import RecetasQueries


def test_listado_enmascara_campos_personales_y_sensibles() -> None:
    contrato = ContratoListadoPacientesService()

    assert contrato.formatear_valor_listado("nombre", "Eva") == "Eva"
    assert contrato.formatear_valor_listado("documento", "12345678") == "******78"
    assert contrato.formatear_valor_listado("telefono", "600123456") == "*** *** 456"
    assert contrato.formatear_valor_listado("num_historia", "HIST-0123") != "HIST-0123"


def test_obtener_historial_paciente_devuelve_detalle_full_y_citas_filtradas(container) -> None:
    paciente_1 = Paciente(
        tipo_documento=TipoDocumento.DNI,
        documento="11111111",
        nombre="Ana",
        apellidos="Ruiz",
        telefono="612345678",
        email="ana@example.com",
        fecha_nacimiento=date(1992, 2, 3),
        direccion="Calle A",
        activo=True,
        num_historia=None,
        alergias="Penicilina",
        observaciones="Observación privada",
    )
    paciente_2 = Paciente(
        tipo_documento=TipoDocumento.DNI,
        documento="22222222",
        nombre="Luis",
        apellidos="Sanz",
        telefono="623456789",
        email=None,
        fecha_nacimiento=None,
        direccion=None,
        activo=True,
        num_historia=None,
        alergias=None,
        observaciones=None,
    )
    paciente_1_id = container.pacientes_repo.create(paciente_1)
    paciente_2_id = container.pacientes_repo.create(paciente_2)
    medico_id = container.medicos_repo.create(
        Medico(
            tipo_documento=TipoDocumento.DNI,
            documento="99999999",
            nombre="Elena",
            apellidos="Mora",
            telefono="644444444",
            email=None,
            fecha_nacimiento=None,
            direccion=None,
            activo=True,
            num_colegiado="COL-1",
            especialidad="General",
        )
    )
    sala_id = container.salas_repo.create(Sala(nombre="Consulta 1", tipo=TipoSala.CONSULTA, ubicacion=None, activa=True))
    citas_repo = CitasRepository(container.connection)
    citas_repo.create(
        Cita(
            paciente_id=paciente_1_id,
            medico_id=medico_id,
            sala_id=sala_id,
            inicio=datetime.fromisoformat("2024-06-12 09:00:00"),
            fin=datetime.fromisoformat("2024-06-12 09:30:00"),
            estado=EstadoCita.PROGRAMADA,
            motivo="Control",
            notas="Paciente estable",
        )
    )
    citas_repo.create(
        Cita(
            paciente_id=paciente_2_id,
            medico_id=medico_id,
            sala_id=sala_id,
            inicio=datetime.fromisoformat("2024-06-13 10:00:00"),
            fin=datetime.fromisoformat("2024-06-13 10:30:00"),
            estado=EstadoCita.PROGRAMADA,
            motivo="Otra",
            notas="No debe aparecer",
        )
    )
    uc = ObtenerHistorialPaciente(
        pacientes_gateway=container.pacientes_repo,
        citas_gateway=HistorialPacienteQueries(container.connection),
        recetas_gateway=RecetasQueries(container.connection),
    )

    resultado = uc.execute(paciente_1_id)

    assert resultado is not None
    assert resultado.paciente_detalle.documento == "11111111"
    assert resultado.paciente_detalle.telefono == "612345678"
    assert len(resultado.citas) == 1
    assert resultado.citas[0].medico == "Elena Mora"
