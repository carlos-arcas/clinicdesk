from __future__ import annotations

import random
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from clinicdesk.app.infrastructure.sqlite.demo_seed.appointments import _iter_batches
from clinicdesk.app.infrastructure.sqlite.demo_seed.types import BatchProgress
from clinicdesk.app.infrastructure.sqlite.sqlite_datetime_codecs import deserialize_datetime, serialize_datetime


@dataclass(frozen=True, slots=True)
class CitaSeedRow:
    cita_id: int
    paciente_id: int
    inicio: datetime
    fin: datetime
    estado: str
    motivo: str


@dataclass(frozen=True, slots=True)
class CitaAgendaMLContext:
    cita_id: int
    paciente_id: int
    inicio: datetime
    fin: datetime
    estado: str
    booked_at: datetime
    tipo_cita: str
    canal_reserva: str
    check_in_at: datetime | None
    llamado_a_consulta_at: datetime | None
    consulta_inicio_at: datetime | None
    consulta_fin_at: datetime | None
    check_out_at: datetime | None
    riesgo: str


def enriquecer_citas_agenda_ml(
    connection: sqlite3.Connection,
    *,
    seed: int,
    batch_size: int,
) -> list[CitaAgendaMLContext]:
    citas = _listar_citas(connection)
    if not citas:
        return []
    contextos = _construir_contextos(citas, seed)
    _actualizar_citas(connection, contextos, batch_size=batch_size)
    return contextos


def _listar_citas(connection: sqlite3.Connection) -> list[CitaSeedRow]:
    rows = connection.execute(
        """
        SELECT id, paciente_id, inicio, fin, estado, coalesce(motivo, '') AS motivo
        FROM citas
        WHERE activo = 1
        ORDER BY datetime(inicio) ASC, id ASC
        """
    ).fetchall()
    return [
        CitaSeedRow(
            cita_id=int(row["id"]),
            paciente_id=int(row["paciente_id"]),
            inicio=deserialize_datetime(row["inicio"]),
            fin=deserialize_datetime(row["fin"]),
            estado=str(row["estado"]),
            motivo=str(row["motivo"]),
        )
        for row in rows
    ]


def _construir_contextos(citas: list[CitaSeedRow], seed: int) -> list[CitaAgendaMLContext]:
    rng = random.Random(seed + 10_000)
    historial = defaultdict(lambda: {"realizadas": 0, "no_show": 0})
    contextos: list[CitaAgendaMLContext] = []
    for cita in citas:
        historial_paciente = historial[cita.paciente_id]
        booked_at = _build_booked_at(cita, rng)
        riesgo = _resolver_riesgo(cita, booked_at, historial_paciente, rng)
        check_in_at, llamado_at, inicio_at, fin_at, out_at = _resolver_timings(cita, rng)
        contextos.append(
            CitaAgendaMLContext(
                cita_id=cita.cita_id,
                paciente_id=cita.paciente_id,
                inicio=cita.inicio,
                fin=cita.fin,
                estado=cita.estado,
                booked_at=booked_at,
                tipo_cita=_resolver_tipo_cita(cita.motivo),
                canal_reserva=_resolver_canal_reserva(cita.estado, rng),
                check_in_at=check_in_at,
                llamado_a_consulta_at=llamado_at,
                consulta_inicio_at=inicio_at,
                consulta_fin_at=fin_at,
                check_out_at=out_at,
                riesgo=riesgo,
            )
        )
        if cita.estado == "REALIZADA":
            historial_paciente["realizadas"] += 1
        elif cita.estado == "NO_PRESENTADO":
            historial_paciente["no_show"] += 1
    return contextos


def _build_booked_at(cita: CitaSeedRow, rng: random.Random) -> datetime:
    if cita.estado == "NO_PRESENTADO":
        dias = rng.choice([0, 1, 2, 3, 5, 7])
    elif cita.estado == "CANCELADA":
        dias = rng.choice([1, 2, 4, 7, 14])
    elif cita.estado in {"PROGRAMADA", "CONFIRMADA"}:
        dias = rng.choice([2, 4, 7, 10, 14, 21, 30, 45])
    elif cita.estado == "EN_CURSO":
        dias = rng.choice([0, 1, 2, 3, 5])
    else:
        dias = rng.choice([2, 4, 7, 10, 14, 21, 28, 35])
    horas = rng.randint(1, 18)
    minutos = rng.choice([0, 10, 20, 30, 40, 50])
    return cita.inicio - timedelta(days=dias, hours=horas, minutes=minutos)


def _resolver_tipo_cita(motivo: str) -> str:
    motivo_normalizado = motivo.lower()
    if "primera" in motivo_normalizado or "valoracion" in motivo_normalizado:
        return "PRIMERA"
    if "revision" in motivo_normalizado or "control" in motivo_normalizado or "seguimiento" in motivo_normalizado:
        return "REVISION"
    if any(token in motivo_normalizado for token in ("lesion", "holter", "procedimiento")):
        return "PROCEDIMIENTO"
    return "OTRA"


def _resolver_canal_reserva(estado: str, rng: random.Random) -> str:
    if estado == "NO_PRESENTADO":
        return rng.choice(["ONLINE", "TELEFONO"])
    if estado == "CANCELADA":
        return rng.choice(["TELEFONO", "MOSTRADOR"])
    return rng.choice(["ONLINE", "TELEFONO", "MOSTRADOR", "DERIVACION"])


def _resolver_timings(
    cita: CitaSeedRow,
    rng: random.Random,
) -> tuple[datetime | None, datetime | None, datetime | None, datetime | None, datetime | None]:
    if cita.estado in {"PROGRAMADA", "CONFIRMADA", "CANCELADA", "NO_PRESENTADO"}:
        return None, None, None, None, None
    check_in = cita.inicio - timedelta(minutes=rng.randint(4, 18))
    llamado = check_in + timedelta(minutes=rng.randint(2, 14))
    consulta_inicio = max(cita.inicio - timedelta(minutes=5), llamado + timedelta(minutes=rng.randint(0, 6)))
    duracion = max(5, int((cita.fin - cita.inicio).total_seconds() // 60) + rng.randint(-5, 10))
    consulta_fin = consulta_inicio + timedelta(minutes=duracion)
    if cita.estado == "EN_CURSO":
        return check_in, llamado, consulta_inicio, None, None
    if rng.random() < 0.18:
        return None, llamado, consulta_inicio, consulta_fin, consulta_fin + timedelta(minutes=rng.randint(3, 16))
    if rng.random() < 0.12:
        return check_in, llamado, None, None, None
    if rng.random() < 0.10:
        return check_in, llamado, consulta_inicio, consulta_fin, None
    return check_in, llamado, consulta_inicio, consulta_fin, consulta_fin + timedelta(minutes=rng.randint(3, 16))


def _resolver_riesgo(
    cita: CitaSeedRow,
    booked_at: datetime,
    historial_paciente: dict[str, int],
    rng: random.Random,
) -> str:
    dias_antelacion = max(0, int((cita.inicio.date() - booked_at.date()).days))
    score = 0.12
    if cita.estado == "NO_PRESENTADO":
        score += 0.55
    elif cita.estado == "CANCELADA":
        score += 0.15
    elif cita.estado == "REALIZADA":
        score -= 0.06
    score += min(0.3, historial_paciente["no_show"] * 0.12)
    if historial_paciente["realizadas"] >= 3 and historial_paciente["no_show"] == 0:
        score -= 0.08
    if dias_antelacion <= 1:
        score += 0.12
    elif dias_antelacion <= 3:
        score += 0.07
    elif dias_antelacion >= 21:
        score -= 0.05
    score += rng.uniform(-0.04, 0.04)
    if score >= 0.58:
        return "ALTO"
    if score >= 0.33:
        return "MEDIO"
    return "BAJO"


def _actualizar_citas(
    connection: sqlite3.Connection,
    contextos: list[CitaAgendaMLContext],
    *,
    batch_size: int,
) -> None:
    total = len(contextos)
    total_batches = (total + batch_size - 1) // batch_size
    tracker = BatchProgress("seed_contexto_citas", total, total_batches, datetime.now(UTC))
    actualizadas = 0
    for batch_index, batch in enumerate(_iter_batches(contextos, batch_size), start=1):
        connection.executemany(
            """
            UPDATE citas
            SET
                check_in_at = ?,
                llamado_a_consulta_at = ?,
                consulta_inicio_at = ?,
                consulta_fin_at = ?,
                check_out_at = ?,
                tipo_cita = ?,
                canal_reserva = ?,
                override_fecha_hora = ?
            WHERE id = ?
            """,
            [
                (
                    _serialize_optional(item.check_in_at),
                    _serialize_optional(item.llamado_a_consulta_at),
                    _serialize_optional(item.consulta_inicio_at),
                    _serialize_optional(item.consulta_fin_at),
                    _serialize_optional(item.check_out_at),
                    item.tipo_cita,
                    item.canal_reserva,
                    serialize_datetime(item.booked_at),
                    item.cita_id,
                )
                for item in batch
            ],
        )
        connection.commit()
        actualizadas += len(batch)
        tracker.log_batch(batch_index, actualizadas)


def _serialize_optional(value: datetime | None) -> str | None:
    return serialize_datetime(value) if value is not None else None
