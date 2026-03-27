from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

from clinicdesk.app.infrastructure.sqlite.demo_seed.appointments import _iter_batches
from clinicdesk.app.infrastructure.sqlite.demo_seed.contexto_agenda_ml import CitaAgendaMLContext
from clinicdesk.app.infrastructure.sqlite.demo_seed.types import BatchProgress

_PRIORIDADES = {"ALTO": "alta", "MEDIO": "media", "BAJO": "baja"}
_ACTORES = ("recepcion_manana", "recepcion_tarde", "coordinacion_agenda")


def seed_historial_operativo(
    connection: sqlite3.Connection,
    contextos: list[CitaAgendaMLContext],
    *,
    batch_size: int,
) -> None:
    if not contextos:
        return
    _insert_many(
        connection,
        "seed_recordatorios",
        """
        INSERT OR REPLACE INTO recordatorios_citas(
            cita_id, canal, estado, created_at_utc, updated_at_utc
        ) VALUES (?, ?, ?, ?, ?)
        """,
        [row for item in contextos for row in _build_recordatorios_rows(item)],
        batch_size=batch_size,
    )
    _insert_many(
        connection,
        "seed_predicciones",
        """
        INSERT OR REPLACE INTO predicciones_ausencias_log(
            timestamp_utc, modelo_fecha_utc, cita_id, riesgo, source
        ) VALUES (?, ?, ?, ?, ?)
        """,
        [_build_prediccion_row(item) for item in contextos],
        batch_size=batch_size,
    )
    _insert_many(
        connection,
        "seed_acciones_ml",
        """
        INSERT INTO ml_acciones_operativas(
            cita_id, prioridad_ml, accion_sugerida_ml, accion_humana, estado,
            nota_corta, timestamp_utc, actor
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [row for item in contextos for row in _build_acciones_rows(item)],
        batch_size=batch_size,
    )


def _build_recordatorios_rows(item: CitaAgendaMLContext) -> list[tuple[int, str, str, str, str]]:
    created_at = max(item.booked_at, item.inicio - timedelta(days=3))
    updated_at = max(created_at, item.inicio - timedelta(days=1))
    estado = "ENVIADO" if item.inicio <= datetime.now() or item.estado in {"REALIZADA", "NO_PRESENTADO"} else "PREPARADO"
    rows = [(item.cita_id, "WHATSAPP", estado, _utc_iso(created_at), _utc_iso(updated_at))]
    if item.riesgo != "BAJO" or item.estado in {"NO_PRESENTADO", "CANCELADA"}:
        rows.append((item.cita_id, "EMAIL", "ENVIADO", _utc_iso(created_at), _utc_iso(updated_at)))
    if item.riesgo == "ALTO" or item.estado in {"NO_PRESENTADO", "CANCELADA"}:
        rows.append(
            (
                item.cita_id,
                "LLAMADA",
                "ENVIADO",
                _utc_iso(max(created_at, item.inicio - timedelta(hours=24))),
                _utc_iso(max(updated_at, item.inicio - timedelta(hours=6))),
            )
        )
    return rows


def _build_prediccion_row(item: CitaAgendaMLContext) -> tuple[str, str, int, str, str]:
    prediction_at = min(item.inicio - timedelta(hours=6), item.booked_at + timedelta(hours=18))
    if prediction_at <= item.booked_at:
        prediction_at = item.booked_at + timedelta(hours=2)
    model_at = prediction_at - timedelta(hours=2)
    return (
        _utc_iso(prediction_at),
        _utc_iso(model_at),
        item.cita_id,
        item.riesgo,
        "seed_demo_realista",
    )


def _build_acciones_rows(item: CitaAgendaMLContext) -> list[tuple[str, str, str, str, str, str, str, str]]:
    if item.riesgo == "BAJO":
        return []
    prioridad = _PRIORIDADES[item.riesgo]
    accion_sugerida = "confirmar_hoy" if item.riesgo == "ALTO" else "revisar_manual"
    actor = _ACTORES[item.cita_id % len(_ACTORES)]
    inicial = (
        str(item.cita_id),
        prioridad,
        accion_sugerida,
        "confirmar_contacto" if item.riesgo == "ALTO" else "revisar_manual",
        "revisado",
        _nota_inicial(item),
        _utc_iso(item.inicio - timedelta(hours=20)),
        actor,
    )
    if item.estado in {"PROGRAMADA", "CONFIRMADA", "EN_CURSO"} and item.riesgo == "MEDIO":
        return [inicial]
    cierre = (
        str(item.cita_id),
        prioridad,
        accion_sugerida,
        _accion_cierre(item.estado),
        _estado_cierre(item.estado),
        _nota_cierre(item.estado),
        _utc_iso(item.inicio - timedelta(hours=4)),
        actor,
    )
    return [inicial, cierre]


def _accion_cierre(estado: str) -> str:
    if estado == "NO_PRESENTADO":
        return "revisar_manual"
    if estado == "CANCELADA":
        return "abrir_cita"
    if estado == "REALIZADA":
        return "sin_accion"
    return "confirmar_contacto"


def _estado_cierre(estado: str) -> str:
    if estado in {"REALIZADA", "NO_PRESENTADO", "CANCELADA"}:
        return "resuelto"
    if estado == "EN_CURSO":
        return "revisado"
    return "pospuesto"


def _nota_inicial(item: CitaAgendaMLContext) -> str:
    if item.riesgo == "ALTO":
        return "Riesgo alto: conviene confirmar asistencia y margen de llegada."
    return "Riesgo medio: revisar agenda y canal de contacto antes del turno."


def _nota_cierre(estado: str) -> str:
    if estado == "REALIZADA":
        return "La asistencia queda confirmada y el seguimiento operativo se cierra."
    if estado == "NO_PRESENTADO":
        return "Se registra ausencia y se deja trazada la accion humana posterior."
    if estado == "CANCELADA":
        return "La agenda ofrece nueva franja tras cancelacion administrativa."
    return "Seguimiento revisado y pendiente de cierre definitivo."


def _insert_many(
    connection: sqlite3.Connection,
    phase: str,
    sql: str,
    rows: list[tuple[object, ...]],
    *,
    batch_size: int,
) -> None:
    if not rows:
        return
    total = len(rows)
    total_batches = (total + batch_size - 1) // batch_size
    tracker = BatchProgress(phase, total, total_batches, datetime.now(UTC))
    inserted = 0
    for batch_index, batch in enumerate(_iter_batches(rows, batch_size), start=1):
        connection.executemany(sql, batch)
        connection.commit()
        inserted += len(batch)
        tracker.log_batch(batch_index, inserted)


def _utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
