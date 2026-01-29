from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from clinicdesk.app.domain.modelos import Paciente, Cita, Medico
# Importamos modelos del dominio porque el repositorio devuelve/usa esas entidades.


class RepositorioPacientes(ABC):
    """
    Contrato (interfaz) para repositorios de pacientes.

    ABC + abstractmethod:
    - ABC: marca la clase como base abstracta (no debe instanciarse directamente).
    - abstractmethod: obliga a implementaciones concretas (SQLite, memoria, API) a implementar estos métodos.
    """

    @abstractmethod
    def listar_todos(self) -> List[Paciente]:
        """Devuelve todos los pacientes."""
        raise NotImplementedError

    @abstractmethod
    def crear(self, nombre: str, telefono: str) -> int:
        """Crea un paciente y devuelve su ID."""
        raise NotImplementedError


class RepositorioCitas(ABC):
    """Contrato para repositorios de citas."""

    @abstractmethod
    def listar_todas(self) -> List[Cita]:
        """Devuelve todas las citas."""
        raise NotImplementedError

    @abstractmethod
    def crear(self, id_paciente: int, fecha_hora: datetime, motivo: str) -> int:
        """Crea una cita y devuelve su ID."""
        raise NotImplementedError


class RepositorioMedicos(ABC):
    """Contrato para repositorios de citas."""

    @abstractmethod
    def listar_todos(self) -> List[Medico]:
        """Devuelve todas los medicos."""
        raise NotImplementedError

    @abstractmethod
    def crear(self, id_medico: int,tipo_documento:str,n_documento:str, nombre: str, especialidad: str,telefono:str) -> int:
        """Crea un medico y devuelve su ID."""
        raise NotImplementedError
