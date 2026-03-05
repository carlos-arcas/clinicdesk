from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from clinicdesk.app.domain.exceptions import AuthorizationError


class Role(str, Enum):
    ADMIN = "ADMIN"
    READONLY = "READONLY"


class Action(str, Enum):
    PACIENTE_CREAR = "pacientes.crear"
    PACIENTE_EDITAR = "pacientes.editar"
    PACIENTE_DESACTIVAR = "pacientes.desactivar"
    CITA_CREAR = "citas.crear"
    CITA_ELIMINAR = "citas.eliminar"
    FARMACIA_DISPENSAR = "farmacia.dispensar"
    AUDITORIA_EXPORTAR_CSV = "auditoria.exportar_csv"
    DEMO_SEED = "demo.seed"
    ML_ENTRENAR = "ml.entrenar"


class AutorizadorAcciones:
    def __init__(self) -> None:
        self._permisos_por_rol: dict[Role, frozenset[Action]] = {
            Role.ADMIN: frozenset(Action),
            Role.READONLY: frozenset(),
        }

    def puede(self, user_context: "UserContext", action: Action) -> bool:
        permisos = self._permisos_por_rol.get(user_context.role)
        if permisos is None:
            return False
        return action in permisos

    def exigir(self, user_context: "UserContext", action: Action) -> None:
        if self.puede(user_context, action):
            return
        raise AuthorizationError(
            f"No tienes permisos para ejecutar '{action.value}'. Tu perfil es {user_context.role.value}."
        )


_ACTION_BY_OPERATION: dict[str, Action] = {
    Action.PACIENTE_CREAR.value: Action.PACIENTE_CREAR,
    Action.PACIENTE_EDITAR.value: Action.PACIENTE_EDITAR,
    Action.PACIENTE_DESACTIVAR.value: Action.PACIENTE_DESACTIVAR,
    Action.CITA_CREAR.value: Action.CITA_CREAR,
    Action.CITA_ELIMINAR.value: Action.CITA_ELIMINAR,
    Action.FARMACIA_DISPENSAR.value: Action.FARMACIA_DISPENSAR,
    Action.AUDITORIA_EXPORTAR_CSV.value: Action.AUDITORIA_EXPORTAR_CSV,
    Action.DEMO_SEED.value: Action.DEMO_SEED,
    Action.ML_ENTRENAR.value: Action.ML_ENTRENAR,
}


@dataclass(slots=True)
class UserContext:
    role: Role = Role.ADMIN
    username: str = "system"
    demo_mode: bool = False
    run_id: str | None = None

    @property
    def can_write(self) -> bool:
        return self.role == Role.ADMIN

    def require_write(self, operation: str) -> None:
        action = _ACTION_BY_OPERATION.get(operation)
        if action is not None:
            AutorizadorAcciones().exigir(self, action)
            return
        if self.can_write:
            return
        raise AuthorizationError(f"No tienes permisos para ejecutar '{operation}'. Tu perfil es {self.role.value}.")
