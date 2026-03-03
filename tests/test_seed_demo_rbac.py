from __future__ import annotations

import pytest

from clinicdesk.app.application.security import AutorizadorAcciones, Role, UserContext
from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoData, SeedDemoDataRequest
from clinicdesk.app.domain.exceptions import AuthorizationError


class _SeederStub:
    def persist(self, *args, **kwargs):  # pragma: no cover - no se debe ejecutar
        raise AssertionError("No debe persistir cuando no hay permisos")


def test_seed_demo_falla_para_rol_readonly() -> None:
    usecase = SeedDemoData(
        _SeederStub(),
        user_context=UserContext(role=Role.READONLY),
        autorizador_acciones=AutorizadorAcciones(),
    )

    with pytest.raises(AuthorizationError):
        usecase.execute(SeedDemoDataRequest())
