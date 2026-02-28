from __future__ import annotations

from datetime import datetime

import pytest

from clinicdesk.app.application.security import Role
from clinicdesk.app.application.usecases.crear_cita import CrearCitaRequest, CrearCitaUseCase
from clinicdesk.app.application.usecases.dispensar_medicamento import (
    DispensarMedicamentoRequest,
    DispensarMedicamentoUseCase,
)
from clinicdesk.app.application.usecases.eliminar_cita import EliminarCitaUseCase
from clinicdesk.app.application.usecases.pacientes_crud import (
    CrearPacienteUseCase,
    DesactivarPacienteUseCase,
    EditarPacienteUseCase,
)
from clinicdesk.app.domain.enums import EstadoCita, TipoDocumento
from clinicdesk.app.domain.exceptions import AuthorizationError
from clinicdesk.app.domain.modelos import Cita, Paciente


def _readonly(container) -> None:
    container.user_context.role = Role.READONLY


def test_crear_paciente_bloqueado_sin_permiso(container) -> None:
    _readonly(container)
    usecase = CrearPacienteUseCase(container.pacientes_repo, container.user_context)

    paciente = Paciente(
        tipo_documento=TipoDocumento.DNI,
        documento="55555555",
        nombre="Solo",
        apellidos="Lectura",
        telefono=None,
        email=None,
        fecha_nacimiento=None,
        direccion=None,
        activo=True,
        num_historia=None,
        alergias=None,
        observaciones=None,
    )

    with pytest.raises(AuthorizationError):
        usecase.execute(paciente)


def test_editar_paciente_bloqueado_sin_permiso(container, seed_data) -> None:
    _readonly(container)
    usecase = EditarPacienteUseCase(container.pacientes_repo, container.user_context)

    paciente = container.pacientes_repo.get_by_id(seed_data["paciente_activo_id"])
    assert paciente is not None
    paciente.telefono = "600000000"

    with pytest.raises(AuthorizationError):
        usecase.execute(paciente)


def test_desactivar_paciente_bloqueado_sin_permiso(container, seed_data) -> None:
    _readonly(container)
    usecase = DesactivarPacienteUseCase(container.pacientes_repo, container.user_context)

    with pytest.raises(AuthorizationError):
        usecase.execute(seed_data["paciente_activo_id"])


def test_crear_cita_bloqueado_sin_permiso(container, seed_data) -> None:
    _readonly(container)
    usecase = CrearCitaUseCase(container)

    req = CrearCitaRequest(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2024-05-20 13:00:00",
        fin="2024-05-20 13:30:00",
        motivo="Control",
        estado=EstadoCita.PROGRAMADA.value,
    )

    with pytest.raises(AuthorizationError):
        usecase.execute(req)


def test_eliminar_cita_bloqueado_sin_permiso(container, seed_data) -> None:
    cita_id = container.citas_repo.create(
        Cita(
            id=None,
            paciente_id=seed_data["paciente_activo_id"],
            medico_id=seed_data["medico_activo_id"],
            sala_id=seed_data["sala_activa_id"],
            inicio=datetime(2024, 5, 20, 14, 0, 0),
            fin=datetime(2024, 5, 20, 14, 30, 0),
            motivo="Eliminar",
            notas=None,
            estado=EstadoCita.PROGRAMADA,
        )
    )
    _readonly(container)
    usecase = EliminarCitaUseCase(container.citas_repo, container.user_context)

    with pytest.raises(AuthorizationError):
        usecase.execute(cita_id)


def test_dispensar_bloqueado_sin_permiso(container, seed_data) -> None:
    _readonly(container)
    usecase = DispensarMedicamentoUseCase(container)

    req = DispensarMedicamentoRequest(
        receta_id=seed_data["receta_id"],
        receta_linea_id=seed_data["receta_linea_id"],
        medicamento_id=seed_data["medicamento_activo_id"],
        personal_id=seed_data["personal_activo_id"],
        cantidad=1,
    )

    with pytest.raises(AuthorizationError):
        usecase.execute(req)
