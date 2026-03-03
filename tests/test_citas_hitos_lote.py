from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from clinicdesk.app.application.citas import (
    HitoAtencion,
    ModoTimestampHito,
    RegistrarHitoAtencionCita,
    RegistrarHitosAtencionEnLote,
)
from clinicdesk.app.domain.enums import EstadoCita
from clinicdesk.app.domain.modelos import Cita
from clinicdesk.app.infrastructure.sqlite.repos_citas import CitasRepository
from clinicdesk.app.infrastructure.sqlite.repos_citas_hitos import CitasHitosRepository


@dataclass(slots=True)
class _RelojFijo:
    fijo: datetime

    def ahora(self) -> datetime:
        return self.fijo


def _crear_cita(repo: CitasRepository, seed_data: dict[str, int], inicio: datetime) -> int:
    cita = Cita(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio=inicio,
        fin=inicio + timedelta(minutes=30),
        estado=EstadoCita.PROGRAMADA,
        motivo="Control",
    )
    return repo.create(cita)


def test_registrar_hitos_lote_cuenta_aplicadas_y_ya_estaban(container, seed_data) -> None:
    repo = CitasRepository(container.connection)
    citas_repo = CitasHitosRepository(container.connection)
    ids = (
        _crear_cita(repo, seed_data, datetime(2026, 3, 1, 9, 0, 0)),
        _crear_cita(repo, seed_data, datetime(2026, 3, 1, 10, 0, 0)),
        _crear_cita(repo, seed_data, datetime(2026, 3, 1, 11, 0, 0)),
    )
    registrar = RegistrarHitoAtencionCita(citas_repo, _RelojFijo(datetime(2026, 3, 1, 8, 0, 0)))
    registrar.ejecutar(ids[2], HitoAtencion.CHECK_IN)

    resultado = RegistrarHitosAtencionEnLote(registrar, citas_repo).ejecutar(ids, HitoAtencion.CHECK_IN, ModoTimestampHito.AHORA)

    assert resultado.aplicadas == 2
    assert resultado.ya_estaban == 1
    assert resultado.omitidas_por_orden == 0
    assert resultado.errores == 0


def test_registrar_hitos_lote_omite_por_orden_invalido(container, seed_data) -> None:
    repo = CitasRepository(container.connection)
    citas_repo = CitasHitosRepository(container.connection)
    ids = (
        _crear_cita(repo, seed_data, datetime(2026, 3, 2, 9, 0, 0)),
        _crear_cita(repo, seed_data, datetime(2026, 3, 2, 10, 0, 0)),
    )
    registrar = RegistrarHitoAtencionCita(citas_repo, _RelojFijo(datetime(2026, 3, 2, 12, 0, 0)))

    resultado = RegistrarHitosAtencionEnLote(registrar, citas_repo).ejecutar(ids, HitoAtencion.FIN_CONSULTA, ModoTimestampHito.AHORA)

    assert resultado.aplicadas == 0
    assert resultado.ya_estaban == 0
    assert resultado.omitidas_por_orden == 2
    assert resultado.errores == 0


def test_obtener_inicio_programado_por_cita_ids(container, seed_data) -> None:
    repo = CitasRepository(container.connection)
    citas_repo = CitasHitosRepository(container.connection)
    cita_id = _crear_cita(repo, seed_data, datetime(2026, 3, 3, 9, 45, 0))

    resultado = citas_repo.obtener_inicios_programados_por_cita_ids((cita_id, 999999))

    assert resultado[cita_id] == datetime(2026, 3, 3, 9, 45, 0)
    assert 999999 not in resultado
