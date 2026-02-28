from __future__ import annotations

from datetime import datetime

import pytest

from clinicdesk.app.application.citas_usecases import CrearCita, ListarCitas
from clinicdesk.app.application.pacientes_usecases import CrearPaciente, ListarPacientes
from clinicdesk.app.domain.modelos import Cita, Paciente
from clinicdesk.app.domain.repositorios import RepositorioCitas, RepositorioPacientes


class PacientesRepoFake(RepositorioPacientes):
    def __init__(self, pacientes: list[Paciente] | None = None) -> None:
        self.pacientes = pacientes or []
        self.creados: list[tuple[str, str]] = []

    def listar_todos(self) -> list[Paciente]:
        return self.pacientes

    def crear(self, nombre: str, telefono: str) -> int:
        self.creados.append((nombre, telefono))
        return len(self.creados)


class CitasRepoFake(RepositorioCitas):
    def __init__(self, citas: list[Cita] | None = None) -> None:
        self.citas = citas or []
        self.creadas: list[tuple[int, datetime, str]] = []

    def listar_todas(self) -> list[Cita]:
        return self.citas

    def crear(self, id_paciente: int, fecha_hora: datetime, motivo: str) -> int:
        self.creadas.append((id_paciente, fecha_hora, motivo))
        return len(self.creadas)


def test_listar_pacientes_devuelve_lo_que_retorna_el_contrato() -> None:
    repo = PacientesRepoFake(pacientes=[Paciente(id=1, nombre="Ana")])

    result = ListarPacientes(repo=repo).ejecutar()

    assert len(result) == 1
    assert result[0].id == 1


def test_crear_paciente_normaliza_entradas_y_valida_nombre() -> None:
    repo = PacientesRepoFake()
    use_case = CrearPaciente(repo=repo)

    created_id = use_case.ejecutar(nombre="  Ana  ", telefono="  600123123  ")

    assert created_id == 1
    assert repo.creados == [("Ana", "600123123")]

    with pytest.raises(ValueError, match="nombre es obligatorio"):
        use_case.ejecutar(nombre="  ", telefono="600000000")


def test_listar_citas_devuelve_lo_que_retorna_el_contrato() -> None:
    repo = CitasRepoFake(citas=[Cita(id=10, motivo="Revision")])

    result = ListarCitas(repo=repo).ejecutar()

    assert len(result) == 1
    assert result[0].id == 10


def test_crear_cita_valida_motivo_y_existencia_de_paciente() -> None:
    fecha_hora = datetime(2024, 1, 1, 10, 0, 0)
    repo_pacientes = PacientesRepoFake(pacientes=[Paciente(id=2, nombre="Ana")])
    repo_citas = CitasRepoFake()
    use_case = CrearCita(repo_citas=repo_citas, repo_pacientes=repo_pacientes)

    cita_id = use_case.ejecutar(id_paciente=2, fecha_hora=fecha_hora, motivo="  Control  ")

    assert cita_id == 1
    assert repo_citas.creadas == [(2, fecha_hora, "Control")]

    with pytest.raises(ValueError, match="motivo es obligatorio"):
        use_case.ejecutar(id_paciente=2, fecha_hora=fecha_hora, motivo="  ")

    with pytest.raises(ValueError, match="paciente no existe"):
        use_case.ejecutar(id_paciente=999, fecha_hora=fecha_hora, motivo="Control")
