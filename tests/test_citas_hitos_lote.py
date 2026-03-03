from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import pytest

from clinicdesk.app.application.citas import (
    HitoAtencion,
    ModoTimestamp,
    RegistrarHitoAtencionCita,
    RegistrarHitosAtencionEnLote,
    RegistrarHitosLoteError,
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


def test_lote_check_in_es_idempotente(container, seed_data) -> None:
    repo = CitasRepository(container.connection)
    hitos_repo = CitasHitosRepository(container.connection)
    ids = (
        _crear_cita(repo, seed_data, datetime(2026, 3, 1, 9, 0, 0)),
        _crear_cita(repo, seed_data, datetime(2026, 3, 1, 10, 0, 0)),
    )
    uc = RegistrarHitosAtencionEnLote(
        RegistrarHitoAtencionCita(hitos_repo, _RelojFijo(datetime(2026, 3, 1, 8, 30, 0))),
        hitos_repo,
    )

    primero = uc.ejecutar(ids, HitoAtencion.CHECK_IN, ModoTimestamp.AHORA)
    segundo = uc.ejecutar(ids, HitoAtencion.CHECK_IN, ModoTimestamp.AHORA)

    assert primero.aplicadas == 2
    assert segundo.aplicadas == 0
    assert segundo.ya_estaban == 2


def test_lote_fin_consulta_sin_inicio_cuenta_omitidas_por_orden(container, seed_data) -> None:
    repo = CitasRepository(container.connection)
    hitos_repo = CitasHitosRepository(container.connection)
    ids = (
        _crear_cita(repo, seed_data, datetime(2026, 3, 2, 9, 0, 0)),
        _crear_cita(repo, seed_data, datetime(2026, 3, 2, 10, 0, 0)),
    )
    uc = RegistrarHitosAtencionEnLote(
        RegistrarHitoAtencionCita(hitos_repo, _RelojFijo(datetime(2026, 3, 2, 12, 0, 0))),
        hitos_repo,
    )

    resultado = uc.ejecutar(ids, HitoAtencion.FIN_CONSULTA, ModoTimestamp.AHORA)

    assert resultado.aplicadas == 0
    assert resultado.omitidas_por_orden == 2
    assert resultado.errores == 0


def test_lote_programada_inicio_consulta_usa_inicio_programado(container, seed_data) -> None:
    repo = CitasRepository(container.connection)
    hitos_repo = CitasHitosRepository(container.connection)
    cita_id = _crear_cita(repo, seed_data, datetime(2026, 3, 3, 9, 45, 0))
    uc = RegistrarHitosAtencionEnLote(
        RegistrarHitoAtencionCita(hitos_repo, _RelojFijo(datetime(2026, 3, 3, 13, 0, 0))),
        hitos_repo,
    )

    uc.ejecutar((cita_id,), HitoAtencion.CHECK_IN, ModoTimestamp.PROGRAMADA)
    resultado = uc.ejecutar((cita_id,), HitoAtencion.INICIO_CONSULTA, ModoTimestamp.PROGRAMADA)
    cita = hitos_repo.obtener_cita_por_id(cita_id)

    assert resultado.aplicadas == 1
    assert cita is not None
    assert datetime.fromisoformat(str(cita["consulta_inicio_at"])) == datetime(2026, 3, 3, 9, 45, 0)


def test_lote_programada_no_permitido_lanza_error_tipado(container, seed_data) -> None:
    repo = CitasRepository(container.connection)
    hitos_repo = CitasHitosRepository(container.connection)
    ids = (_crear_cita(repo, seed_data, datetime(2026, 3, 4, 9, 0, 0)),)
    uc = RegistrarHitosAtencionEnLote(
        RegistrarHitoAtencionCita(hitos_repo, _RelojFijo(datetime(2026, 3, 4, 8, 0, 0))),
        hitos_repo,
    )

    with pytest.raises(RegistrarHitosLoteError, match="modo_programada_no_permitido"):
        uc.ejecutar(ids, HitoAtencion.FIN_CONSULTA, ModoTimestamp.PROGRAMADA)


def test_lote_cuenta_no_encontradas(container, seed_data) -> None:
    repo = CitasRepository(container.connection)
    hitos_repo = CitasHitosRepository(container.connection)
    cita_id = _crear_cita(repo, seed_data, datetime(2026, 3, 5, 9, 0, 0))
    uc = RegistrarHitosAtencionEnLote(
        RegistrarHitoAtencionCita(hitos_repo, _RelojFijo(datetime(2026, 3, 5, 8, 0, 0))),
        hitos_repo,
    )

    resultado = uc.ejecutar((cita_id, 999999), HitoAtencion.CHECK_IN, ModoTimestamp.AHORA)

    assert resultado.aplicadas == 1
    assert resultado.no_encontradas == 1


def test_obtener_inicio_programado_por_cita_ids_mapea_fechas(container, seed_data) -> None:
    repo = CitasRepository(container.connection)
    hitos_repo = CitasHitosRepository(container.connection)
    cita_id = _crear_cita(repo, seed_data, datetime(2026, 3, 6, 9, 45, 0))

    resultado = hitos_repo.obtener_inicios_programados_por_cita_ids((cita_id, 999999))

    assert resultado[cita_id] == datetime(2026, 3, 6, 9, 45, 0)
    assert 999999 not in resultado
