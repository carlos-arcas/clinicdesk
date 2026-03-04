from __future__ import annotations

from pathlib import Path

import pytest

from clinicdesk.app.application.auditoria.audit_service import AuditEvent, AuditService
from clinicdesk.app.application.seguridad.politica_rutas_seguras import es_ruta_db_segura_para_reset
from clinicdesk.app.application.security import AutorizadorAcciones, Role, UserContext
from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoData, SeedDemoDataRequest, SeedDemoDataSeguridadError


class _RepoAuditoriaFake:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self.events.append(event)


class _SeederOk:
    class _Resultado:
        doctors = 1
        patients = 1
        personal = 1
        appointments = 1
        incidences = 0
        medicamentos = 0
        materiales = 0
        recetas = 0
        receta_lineas = 0
        dispensaciones = 0
        movimientos_medicamentos = 0
        movimientos_materiales = 0
        turnos = 0
        ausencias = 0

    def persist(self, *args, **kwargs):
        return self._Resultado()


def test_es_ruta_db_segura_para_reset_valida_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    raiz_data = tmp_path / "data"
    raiz_tmp = tmp_path / "tmp"
    raiz_data.mkdir(parents=True)
    raiz_tmp.mkdir(parents=True)
    monkeypatch.setenv("CLINICDESK_SAFE_DB_ROOTS", f"{raiz_data};{raiz_tmp}")

    assert es_ruta_db_segura_para_reset(raiz_data / "clinicdesk.db") is True
    assert es_ruta_db_segura_para_reset(tmp_path / "sandbox" / "demo.sqlite") is True
    assert es_ruta_db_segura_para_reset(tmp_path / "sandbox" / "test.sqlite3") is True
    assert es_ruta_db_segura_para_reset(Path.home()) is False
    assert es_ruta_db_segura_para_reset(tmp_path / "prod" / "real.db") is False
    assert es_ruta_db_segura_para_reset(tmp_path / "data" / "sin_extension") is False


def test_seed_demo_falla_por_ruta_insegura_y_audita_fail() -> None:
    repo = _RepoAuditoriaFake()
    usecase = SeedDemoData(
        _SeederOk(),
        user_context=UserContext(role=Role.ADMIN, username="admin"),
        autorizador_acciones=AutorizadorAcciones(),
        audit_service=AuditService(repo),
    )

    with pytest.raises(SeedDemoDataSeguridadError, match="unsafe_db_path"):
        usecase.execute(SeedDemoDataRequest(reset_db=True, db_path="/opt/prod/real.db"))

    assert repo.events[-1].outcome == "fail"
    assert repo.events[-1].metadata["reason_code"] == "unsafe_db_path"


def test_seed_demo_falla_si_no_hay_confirmacion_y_audita_fail(tmp_path: Path) -> None:
    repo = _RepoAuditoriaFake()
    db_path = tmp_path / "demo-seed.db"
    usecase = SeedDemoData(
        _SeederOk(),
        user_context=UserContext(role=Role.ADMIN, username="admin"),
        autorizador_acciones=AutorizadorAcciones(),
        audit_service=AuditService(repo),
    )

    with pytest.raises(SeedDemoDataSeguridadError, match="confirmation_required"):
        usecase.execute(SeedDemoDataRequest(reset_db=True, db_path=db_path.as_posix()))

    assert repo.events[-1].outcome == "fail"
    assert repo.events[-1].metadata["reason_code"] == "confirmation_required"


def test_seed_demo_ok_con_ruta_segura_confirmacion_y_admin(tmp_path: Path) -> None:
    repo = _RepoAuditoriaFake()
    db_path = tmp_path / "demo-seed.db"
    usecase = SeedDemoData(
        _SeederOk(),
        user_context=UserContext(role=Role.ADMIN, username="admin"),
        autorizador_acciones=AutorizadorAcciones(),
        audit_service=AuditService(repo),
    )

    response = usecase.execute(
        SeedDemoDataRequest(
            reset_db=True,
            db_path=db_path.as_posix(),
            confirmacion="RESET-DEMO",
            n_doctors=1,
            n_patients=1,
            n_appointments=1,
        )
    )

    assert response.doctors == 1
    assert repo.events[-1].outcome == "ok"
    assert repo.events[-1].metadata["reason_code"] == "ok"
