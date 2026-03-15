from __future__ import annotations

import sqlite3

from clinicdesk.app.application.seguros.postventa import FiltroCarteraPolizaSeguro
from clinicdesk.app.domain.seguros.postventa import BeneficiarioSeguro, IncidenciaPolizaSeguro, PolizaSeguro
from clinicdesk.app.infrastructure.seguros.schema_sqlite import inicializar_schema_comercial_seguro
from clinicdesk.app.infrastructure.seguros.serializacion_sqlite import (
    poliza_a_payload_sqlite,
    row_a_beneficiario,
    row_a_incidencia,
    row_a_poliza,
)


class RepositorioPolizaSeguroSqlite:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._connection.row_factory = sqlite3.Row
        inicializar_schema_comercial_seguro(self._connection)

    def guardar_poliza(self, poliza: PolizaSeguro) -> None:
        payload = poliza_a_payload_sqlite(poliza)
        self._connection.execute(
            """
            INSERT INTO seguro_polizas (
                id_poliza, id_oportunidad_origen, id_paciente, id_plan, estado_poliza,
                titular_id_asegurado, titular_nombre, titular_documento, titular_estado,
                vigencia_inicio, vigencia_fin, renovacion_fecha, renovacion_estado,
                coberturas_json, actualizado_en
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(id_poliza) DO UPDATE SET
                estado_poliza = excluded.estado_poliza,
                titular_id_asegurado = excluded.titular_id_asegurado,
                titular_nombre = excluded.titular_nombre,
                titular_documento = excluded.titular_documento,
                titular_estado = excluded.titular_estado,
                vigencia_inicio = excluded.vigencia_inicio,
                vigencia_fin = excluded.vigencia_fin,
                renovacion_fecha = excluded.renovacion_fecha,
                renovacion_estado = excluded.renovacion_estado,
                coberturas_json = excluded.coberturas_json,
                actualizado_en = excluded.actualizado_en
            """,
            payload,
        )
        self._connection.execute("DELETE FROM seguro_poliza_beneficiarios WHERE id_poliza = ?", (poliza.id_poliza,))
        self._connection.executemany(
            """
            INSERT INTO seguro_poliza_beneficiarios (
                id_beneficiario, id_poliza, nombre, parentesco, estado
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (item.id_beneficiario, poliza.id_poliza, item.nombre, item.parentesco, item.estado.value)
                for item in poliza.beneficiarios
            ],
        )
        self._connection.commit()

    def obtener_poliza(self, id_poliza: str) -> PolizaSeguro:
        row = self._connection.execute("SELECT * FROM seguro_polizas WHERE id_poliza = ?", (id_poliza,)).fetchone()
        if row is None:
            raise KeyError(id_poliza)
        return row_a_poliza(row, self._listar_beneficiarios(id_poliza), self._listar_incidencias(id_poliza))

    def guardar_incidencia(self, id_poliza: str, incidencia: IncidenciaPolizaSeguro) -> None:
        self._connection.execute(
            """
            INSERT INTO seguro_poliza_incidencias (
                id_incidencia, id_poliza, tipo, descripcion, estado, fecha_apertura
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id_incidencia) DO UPDATE SET
                tipo = excluded.tipo,
                descripcion = excluded.descripcion,
                estado = excluded.estado,
                fecha_apertura = excluded.fecha_apertura
            """,
            (
                incidencia.id_incidencia,
                id_poliza,
                incidencia.tipo.value,
                incidencia.descripcion,
                incidencia.estado.value,
                incidencia.fecha_apertura.isoformat(),
            ),
        )
        self._connection.commit()

    def listar_polizas(self, filtro: FiltroCarteraPolizaSeguro) -> tuple[PolizaSeguro, ...]:
        where_clauses = ["1=1"]
        params: list[object] = []
        if filtro.estado:
            where_clauses.append("p.estado_poliza = ?")
            params.append(filtro.estado.value)
        if filtro.id_plan:
            where_clauses.append("p.id_plan = ?")
            params.append(filtro.id_plan)
        if filtro.renovacion_pendiente:
            where_clauses.append("p.renovacion_estado = 'PENDIENTE'")
        if filtro.proximos_a_vencer_dias is not None:
            where_clauses.append("julianday(p.vigencia_fin) - julianday(date('now')) <= ?")
            params.append(filtro.proximos_a_vencer_dias)
        if filtro.solo_con_incidencias:
            where_clauses.append("EXISTS (SELECT 1 FROM seguro_poliza_incidencias i WHERE i.id_poliza = p.id_poliza)")

        rows = self._connection.execute(
            f"SELECT p.* FROM seguro_polizas p WHERE {' AND '.join(where_clauses)} ORDER BY p.vigencia_fin ASC",
            tuple(params),
        ).fetchall()
        return tuple(
            row_a_poliza(row, self._listar_beneficiarios(row["id_poliza"]), self._listar_incidencias(row["id_poliza"]))
            for row in rows
        )

    def _listar_beneficiarios(self, id_poliza: str) -> tuple[BeneficiarioSeguro, ...]:
        rows = self._connection.execute(
            "SELECT * FROM seguro_poliza_beneficiarios WHERE id_poliza = ? ORDER BY id_beneficiario",
            (id_poliza,),
        ).fetchall()
        return tuple(row_a_beneficiario(row) for row in rows)

    def _listar_incidencias(self, id_poliza: str) -> tuple[IncidenciaPolizaSeguro, ...]:
        rows = self._connection.execute(
            "SELECT * FROM seguro_poliza_incidencias WHERE id_poliza = ? ORDER BY fecha_apertura DESC",
            (id_poliza,),
        ).fetchall()
        return tuple(row_a_incidencia(row) for row in rows)
