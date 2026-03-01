from __future__ import annotations

from datetime import datetime

from clinicdesk.app.application.usecases.obtener_historial_paciente import ObtenerHistorialPaciente
from clinicdesk.app.domain.citas import Cita, EstadoCita
from clinicdesk.app.domain.enums import TipoDocumento, TipoSala
from clinicdesk.app.domain.modelos import Medico, Medicamento, Paciente, Receta, RecetaLinea, Sala
from clinicdesk.app.infrastructure.sqlite.repos_citas import CitasRepository
from clinicdesk.app.queries.historial_paciente_queries import HistorialPacienteQueries
from clinicdesk.app.queries.recetas_queries import RecetasQueries


def _seed_historial(container) -> tuple[int, int, int]:
    paciente_id = container.pacientes_repo.create(
        Paciente(
            tipo_documento=TipoDocumento.DNI,
            documento="45556666",
            nombre="Ana",
            apellidos="Rivas",
            telefono="622222222",
            email="ana@test.local",
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
            documento="78889999",
            nombre="Elena",
            apellidos="Mora",
            telefono=None,
            email=None,
            fecha_nacimiento=None,
            direccion=None,
            activo=True,
            num_colegiado="COL-998",
            especialidad="General",
        )
    )
    medicamento_id = container.medicamentos_repo.create(
        Medicamento(
            nombre_compuesto="Ibuprofeno",
            nombre_comercial="Ibuprofeno",
            cantidad_almacen=20,
            activo=True,
        )
    )
    sala_id = container.salas_repo.create(Sala(nombre="Consulta 4", tipo=TipoSala.CONSULTA, ubicacion=None, activa=True))
    CitasRepository(container.connection).create(
        Cita(
            paciente_id=paciente_id,
            medico_id=medico_id,
            sala_id=sala_id,
            inicio=datetime(2024, 6, 12, 9, 0, 0),
            fin=datetime(2024, 6, 12, 9, 30, 0),
            estado=EstadoCita.PROGRAMADA,
            motivo="Control",
            notas=None,
        )
    )
    return paciente_id, medico_id, medicamento_id


def test_obtener_historial_paciente_incluye_recetas_y_lineas(container) -> None:
    paciente_id, medico_id, medicamento_id = _seed_historial(container)
    receta_id = container.recetas_repo.create_receta(
        Receta(paciente_id=paciente_id, medico_id=medico_id, fecha=datetime(2024, 2, 5, 8, 0, 0))
    )
    container.recetas_repo.add_linea(
        RecetaLinea(receta_id=receta_id, medicamento_id=medicamento_id, dosis="1/8h", duracion_dias=7)
    )
    uc = ObtenerHistorialPaciente(
        pacientes_gateway=container.pacientes_repo,
        citas_gateway=HistorialPacienteQueries(container.connection),
        recetas_gateway=RecetasQueries(container.connection),
    )

    resultado = uc.execute(paciente_id)

    assert resultado is not None
    assert len(resultado.recetas) == 1
    assert resultado.recetas[0].num_lineas == 1
    assert resultado.detalle_por_receta[receta_id][0].medicamento == "Ibuprofeno"


def test_obtener_historial_paciente_deriva_activa_y_no_activa(container) -> None:
    paciente_id, medico_id, medicamento_id = _seed_historial(container)
    receta_activa = container.recetas_repo.create_receta(
        Receta(paciente_id=paciente_id, medico_id=medico_id, fecha=datetime(2024, 3, 1, 9, 0, 0))
    )
    receta_no_activa = container.recetas_repo.create_receta(
        Receta(paciente_id=paciente_id, medico_id=medico_id, fecha=datetime(2024, 1, 1, 9, 0, 0))
    )
    linea_activa = container.recetas_repo.add_linea(
        RecetaLinea(receta_id=receta_activa, medicamento_id=medicamento_id, dosis="1/8h", duracion_dias=5)
    )
    linea_no_activa = container.recetas_repo.add_linea(
        RecetaLinea(receta_id=receta_no_activa, medicamento_id=medicamento_id, dosis="1/24h", duracion_dias=2)
    )
    container.connection.execute("UPDATE receta_lineas SET estado='ANULADA' WHERE id=?", (linea_no_activa,))
    container.connection.execute("UPDATE receta_lineas SET estado='ACTIVA' WHERE id=?", (linea_activa,))
    container.connection.commit()

    resultado = ObtenerHistorialPaciente(
        pacientes_gateway=container.pacientes_repo,
        citas_gateway=HistorialPacienteQueries(container.connection),
        recetas_gateway=RecetasQueries(container.connection),
    ).execute(paciente_id)

    assert resultado is not None
    mapa = {receta.id: receta.activa for receta in resultado.recetas}
    assert mapa[receta_activa] is True
    assert mapa[receta_no_activa] is False
