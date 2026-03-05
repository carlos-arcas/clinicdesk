from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta

from clinicdesk.app.application.citas.registrar_hito_atencion import HitoAtencion, RegistrarHitoAtencionCita
from clinicdesk.app.domain.enums import EstadoCita
from clinicdesk.app.domain.modelos import Cita
from clinicdesk.app.infrastructure.sqlite.db import asegurar_columnas_citas_extendido
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


def test_migracion_asegura_columnas_citas_extendido_idempotente() -> None:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE citas (id INTEGER PRIMARY KEY, inicio TEXT NOT NULL, fin TEXT NOT NULL)")

    asegurar_columnas_citas_extendido(con)
    asegurar_columnas_citas_extendido(con)

    columnas = {row["name"] for row in con.execute("PRAGMA table_info(citas)").fetchall()}
    assert "check_in_at" in columnas
    assert "llamado_a_consulta_at" in columnas
    assert "consulta_inicio_at" in columnas
    assert "consulta_fin_at" in columnas
    assert "check_out_at" in columnas
    assert "tipo_cita" in columnas
    assert "canal_reserva" in columnas


def test_usecase_hitos_idempotencia_y_orden(container, seed_data) -> None:
    repo = CitasRepository(container.connection)
    cita_id = _crear_cita(repo, seed_data, datetime(2026, 1, 1, 10, 0, 0))
    uc = RegistrarHitoAtencionCita(
        CitasHitosRepository(container.connection), _RelojFijo(datetime(2026, 1, 1, 10, 1, 0))
    )

    primero = uc.ejecutar(cita_id, HitoAtencion.CHECK_IN)
    segundo = uc.ejecutar(cita_id, HitoAtencion.CHECK_IN)
    invalido = uc.ejecutar(cita_id, HitoAtencion.FIN_CONSULTA)

    assert primero.aplicado is True
    assert segundo.ya_estaba is True
    assert segundo.reason_code == "hito_ya_registrado"
    assert invalido.aplicado is False
    assert invalido.reason_code == "orden_invalido_requiere_inicio_consulta"


def test_persistencia_hitos_flujo_feliz(container, seed_data) -> None:
    repo = CitasRepository(container.connection)
    cita_id = _crear_cita(repo, seed_data, datetime(2026, 1, 2, 9, 0, 0))

    pasos = [
        (HitoAtencion.CHECK_IN, datetime(2026, 1, 2, 8, 55, 0)),
        (HitoAtencion.INICIO_CONSULTA, datetime(2026, 1, 2, 9, 0, 0)),
        (HitoAtencion.FIN_CONSULTA, datetime(2026, 1, 2, 9, 25, 0)),
        (HitoAtencion.CHECK_OUT, datetime(2026, 1, 2, 9, 30, 0)),
    ]
    for hito, marca in pasos:
        resultado = RegistrarHitoAtencionCita(CitasHitosRepository(container.connection), _RelojFijo(marca)).ejecutar(
            cita_id, hito
        )
        assert resultado.aplicado is True

    fila = CitasHitosRepository(container.connection).obtener_cita_por_id(cita_id)
    assert fila is not None
    assert datetime.fromisoformat(str(fila["check_in_at"])) == datetime(2026, 1, 2, 8, 55, 0)
    assert datetime.fromisoformat(str(fila["consulta_inicio_at"])) == datetime(2026, 1, 2, 9, 0, 0)
    assert datetime.fromisoformat(str(fila["consulta_fin_at"])) == datetime(2026, 1, 2, 9, 25, 0)
    assert datetime.fromisoformat(str(fila["check_out_at"])) == datetime(2026, 1, 2, 9, 30, 0)
