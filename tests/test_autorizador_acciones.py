from __future__ import annotations

import pytest

from clinicdesk.app.application.security import Action, AutorizadorAcciones, Role, UserContext
from clinicdesk.app.domain.exceptions import AuthorizationError


@pytest.mark.parametrize(
    ("role", "action", "esperado"),
    [
        (Role.ADMIN, Action.CITA_CREAR, True),
        (Role.ADMIN, Action.DEMO_SEED, True),
        (Role.ADMIN, Action.ML_ENTRENAR, True),
        (Role.READONLY, Action.CITA_CREAR, False),
        (Role.READONLY, Action.DEMO_SEED, False),
        (Role.READONLY, Action.AUDITORIA_EXPORTAR_CSV, False),
    ],
)
def test_puede_resuelve_matriz_roles_acciones(role: Role, action: Action, esperado: bool) -> None:
    autorizador = AutorizadorAcciones()

    assert autorizador.puede(UserContext(role=role), action) is esperado


def test_exigir_lanza_si_no_hay_permiso() -> None:
    autorizador = AutorizadorAcciones()
    contexto = UserContext(role=Role.READONLY)

    with pytest.raises(AuthorizationError):
        autorizador.exigir(contexto, Action.CITA_ELIMINAR)
