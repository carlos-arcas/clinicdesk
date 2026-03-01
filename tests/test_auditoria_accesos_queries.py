from __future__ import annotations

from clinicdesk.app.queries.auditoria_accesos_queries import AuditoriaAccesosQueries, FiltrosAuditoriaAccesos


def _insert_auditoria_row(
    db_connection,
    *,
    timestamp_utc: str,
    usuario: str,
    accion: str,
    entidad_tipo: str,
    entidad_id: str,
) -> None:
    db_connection.execute(
        """
        INSERT INTO auditoria_accesos (
            timestamp_utc, usuario, modo_demo, accion, entidad_tipo, entidad_id, metadata_json, created_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (timestamp_utc, usuario, 0, accion, entidad_tipo, entidad_id, None, timestamp_utc),
    )
    db_connection.commit()


def test_buscar_auditoria_accesos_filtros_orden_total_y_paginacion(db_connection) -> None:
    _insert_auditoria_row(
        db_connection,
        timestamp_utc="2026-01-01T08:00:00+00:00",
        usuario="ana",
        accion="VER_DETALLE_CITA",
        entidad_tipo="CITA",
        entidad_id="1",
    )
    _insert_auditoria_row(
        db_connection,
        timestamp_utc="2026-01-02T08:00:00+00:00",
        usuario="ana-admin",
        accion="VER_DETALLE_CITA",
        entidad_tipo="CITA",
        entidad_id="2",
    )
    _insert_auditoria_row(
        db_connection,
        timestamp_utc="2026-01-03T08:00:00+00:00",
        usuario="beatriz",
        accion="VER_DETALLE_RECETA",
        entidad_tipo="RECETA",
        entidad_id="3",
    )
    _insert_auditoria_row(
        db_connection,
        timestamp_utc="2026-01-04T08:00:00+00:00",
        usuario="ana",
        accion="VER_HISTORIAL_PACIENTE",
        entidad_tipo="PACIENTE",
        entidad_id="4",
    )

    queries = AuditoriaAccesosQueries(db_connection)

    items_all, total_all = queries.buscar_auditoria_accesos(FiltrosAuditoriaAccesos(), limit=2, offset=0)
    assert total_all == 4
    assert [item.timestamp_utc for item in items_all] == [
        "2026-01-04T08:00:00+00:00",
        "2026-01-03T08:00:00+00:00",
    ]

    page_2, total_page_2 = queries.buscar_auditoria_accesos(FiltrosAuditoriaAccesos(), limit=2, offset=2)
    assert total_page_2 == 4
    assert [item.timestamp_utc for item in page_2] == [
        "2026-01-02T08:00:00+00:00",
        "2026-01-01T08:00:00+00:00",
    ]

    filtros = FiltrosAuditoriaAccesos(usuario_contiene="ana", accion="VER_DETALLE_CITA", entidad_tipo="CITA")
    filtered_items, filtered_total = queries.buscar_auditoria_accesos(filtros, limit=10, offset=0)
    assert filtered_total == 2
    assert [item.entidad_id for item in filtered_items] == ["2", "1"]


def test_buscar_auditoria_accesos_filtra_por_rango_fechas(db_connection) -> None:
    _insert_auditoria_row(
        db_connection,
        timestamp_utc="2026-02-10T09:00:00+00:00",
        usuario="user-1",
        accion="VER_DETALLE_CITA",
        entidad_tipo="CITA",
        entidad_id="10",
    )
    _insert_auditoria_row(
        db_connection,
        timestamp_utc="2026-02-11T09:00:00+00:00",
        usuario="user-2",
        accion="VER_DETALLE_CITA",
        entidad_tipo="CITA",
        entidad_id="11",
    )
    _insert_auditoria_row(
        db_connection,
        timestamp_utc="2026-02-12T09:00:00+00:00",
        usuario="user-3",
        accion="VER_DETALLE_CITA",
        entidad_tipo="CITA",
        entidad_id="12",
    )

    queries = AuditoriaAccesosQueries(db_connection)
    filtros = FiltrosAuditoriaAccesos(
        desde_utc="2026-02-11T00:00:00+00:00",
        hasta_utc="2026-02-12T00:00:00+00:00",
    )
    items, total = queries.buscar_auditoria_accesos(filtros, limit=10, offset=0)

    assert total == 1
    assert len(items) == 1
    assert items[0].entidad_id == "11"
