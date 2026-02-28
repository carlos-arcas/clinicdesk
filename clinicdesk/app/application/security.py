from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from clinicdesk.app.domain.exceptions import AuthorizationError


class Role(str, Enum):
    ADMIN = "ADMIN"
    READONLY = "READONLY"


@dataclass(slots=True)
class UserContext:
    role: Role = Role.ADMIN

    @property
    def can_write(self) -> bool:
        return self.role == Role.ADMIN

    def require_write(self, operation: str) -> None:
        if self.can_write:
            return
        raise AuthorizationError(
            f"No tienes permisos para ejecutar '{operation}'. "
            "Tu perfil es READONLY."
        )
