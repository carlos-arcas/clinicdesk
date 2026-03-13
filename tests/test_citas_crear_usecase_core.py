from __future__ import annotations

import pytest

from clinicdesk.app.application.usecases.crear_cita import (
    CrearCitaRequest,
    CrearCitaUseCase,
    PendingWarningsError,
)
from clinicdesk.app.domain.enums import EstadoCita
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.infrastructure.sqlite.repos_ausencias_medico import AusenciaMedico


def _request_base(
    seed_data: dict[str, int], *, inicio: str = "2024-05-20 09:00:00", fin: str = "2024-05-20 09:30:00"
) -> CrearCitaRequest:
    return CrearCitaRequest(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio=inicio,
        fin=fin,
        motivo="Control clínico",
        estado=EstadoCita.PROGRAMADA.value,
    )


def test_crear_cita_valida_ids_positivos(container, seed_data) -> None:
    usecase = CrearCitaUseCase(container)
    escenarios = (
        ({"paciente_id": 0}, "paciente_id inválido"),
        ({"medico_id": 0}, "medico_id inválido"),
        ({"sala_id": 0}, "sala_id inválido"),
    )

    for cambios, mensaje in escenarios:
        request = _request_base(seed_data)
        for campo, valor in cambios.items():
            setattr(request, campo, valor)
        try:
            usecase.execute(request)
            raise AssertionError(f"Se esperaba ValidationError para: {mensaje}")
        except ValidationError as exc:
            assert mensaje in str(exc)


def test_crear_cita_falla_si_fechas_invalidas(container, seed_data) -> None:
    usecase = CrearCitaUseCase(container)

    with_fecha_invalida = _request_base(seed_data)
    with_fecha_invalida.inicio = "2024/05/20 09:00"

    with pytest.raises(ValidationError, match="Formato de fecha/hora inválido"):
        usecase.execute(with_fecha_invalida)

    with_fin_no_posterior = _request_base(seed_data)
    with_fin_no_posterior.fin = with_fin_no_posterior.inicio

    with pytest.raises(ValidationError, match="fin debe ser posterior a inicio"):
        usecase.execute(with_fin_no_posterior)


def test_crear_cita_falla_si_medico_no_existe_o_esta_inactivo(container, seed_data) -> None:
    usecase = CrearCitaUseCase(container)

    request_no_existe = _request_base(seed_data)
    request_no_existe.medico_id = 999999
    with pytest.raises(ValidationError, match="médico no existe o está inactivo"):
        usecase.execute(request_no_existe)

    request_inactivo = _request_base(seed_data)
    request_inactivo.medico_id = seed_data["medico_inactivo_id"]
    with pytest.raises(ValidationError, match="médico no existe o está inactivo"):
        usecase.execute(request_inactivo)


def test_crear_cita_falla_si_sala_no_existe_o_esta_inactiva(container, seed_data) -> None:
    usecase = CrearCitaUseCase(container)

    request_no_existe = _request_base(seed_data)
    request_no_existe.sala_id = 999999
    with pytest.raises(ValidationError, match="sala no existe o está inactiva"):
        usecase.execute(request_no_existe)

    request_inactiva = _request_base(seed_data)
    request_inactiva.sala_id = seed_data["sala_inactiva_id"]
    with pytest.raises(ValidationError, match="sala no existe o está inactiva"):
        usecase.execute(request_inactiva)


def test_crear_cita_detecta_solape_de_medico_y_sala_ignorando_canceladas(container, seed_data) -> None:
    usecase = CrearCitaUseCase(container)
    base = _request_base(seed_data, inicio="2024-05-20 10:00:00", fin="2024-05-20 10:30:00")
    usecase.execute(base)

    request_solape_medico = _request_base(seed_data, inicio="2024-05-20 10:15:00", fin="2024-05-20 10:45:00")
    with pytest.raises(ValidationError, match="solape con otra cita del médico"):
        usecase.execute(request_solape_medico)

    cita_cancelada = _request_base(seed_data, inicio="2024-05-20 11:00:00", fin="2024-05-20 11:30:00")
    cita_cancelada.estado = EstadoCita.CANCELADA.value
    usecase.execute(cita_cancelada)

    request_sobre_cancelada = _request_base(seed_data, inicio="2024-05-20 11:10:00", fin="2024-05-20 11:20:00")
    result = usecase.execute(request_sobre_cancelada)
    assert result.cita_id > 0


def test_crear_cita_warning_medico_sin_cuadrante_exige_override(container, seed_data) -> None:
    usecase = CrearCitaUseCase(container)
    request = _request_base(seed_data, inicio="2024-05-21 09:00:00", fin="2024-05-21 09:30:00")

    with pytest.raises(PendingWarningsError) as exc_info:
        usecase.execute(request)

    assert exc_info.value.warnings[0].codigo == "MEDICO_SIN_CUADRANTE"


def test_crear_cita_warning_ausencia_exige_override_y_permite_incidencia(container, seed_data) -> None:
    container.ausencias_medico_repo.create(
        AusenciaMedico(
            medico_id=seed_data["medico_activo_id"],
            inicio="2024-05-20 09:00:00",
            fin="2024-05-20 12:00:00",
            tipo="BAJA",
            motivo="Recuperación",
            aprobado_por_personal_id=seed_data["personal_activo_id"],
            creado_en="2024-05-19 08:00:00",
        )
    )
    usecase = CrearCitaUseCase(container)
    request = _request_base(seed_data, inicio="2024-05-20 10:40:00", fin="2024-05-20 11:00:00")

    with pytest.raises(PendingWarningsError) as exc_info:
        usecase.execute(request)

    codigos = {warning.codigo for warning in exc_info.value.warnings}
    assert codigos == {"MEDICO_CON_AUSENCIA"}

    request.override = True
    request.nota_override = "Coordinación confirma atención urgente"
    request.confirmado_por_personal_id = seed_data["personal_activo_id"]
    resultado = usecase.execute(request)

    assert resultado.cita_id > 0
    assert resultado.incidencia_id is not None


def test_crear_cita_override_exige_nota_y_confirmador(container, seed_data) -> None:
    usecase = CrearCitaUseCase(container)
    request = _request_base(seed_data, inicio="2024-05-21 12:00:00", fin="2024-05-21 12:20:00")
    request.override = True

    with pytest.raises(ValidationError, match="nota_override"):
        usecase.execute(request)

    request.nota_override = "Autorizado"
    with pytest.raises(ValidationError, match="confirmado_por_personal_id"):
        usecase.execute(request)


def test_crear_cita_exito_sin_warnings_no_crea_incidencia(container, seed_data) -> None:
    usecase = CrearCitaUseCase(container)
    request = _request_base(seed_data, inicio="2024-05-20 13:00:00", fin="2024-05-20 13:20:00")

    result = usecase.execute(request)

    assert result.cita_id > 0
    assert result.warnings == []
    assert result.incidencia_id is None
