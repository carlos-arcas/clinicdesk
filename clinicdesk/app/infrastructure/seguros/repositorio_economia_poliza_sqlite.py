from __future__ import annotations

import sqlite3

from clinicdesk.app.domain.seguros.economia_poliza import (
    CuotaPolizaSeguro,
    EstadoCuotaPolizaSeguro,
    ImpagoPolizaSeguro,
    ReactivacionPolizaSeguro,
    SuspensionPolizaSeguro,
)
from clinicdesk.app.infrastructure.seguros.schema_sqlite import inicializar_schema_comercial_seguro


class RepositorioEconomiaPolizaSeguroSqlite:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._connection.row_factory = sqlite3.Row
        inicializar_schema_comercial_seguro(self._connection)

    def guardar_cuota(self, cuota: CuotaPolizaSeguro) -> None:
        self._connection.execute(
            """
            INSERT INTO seguro_poliza_cuotas (
                id_cuota, id_poliza, periodo, fecha_emision, fecha_vencimiento,
                importe, estado_cuota, fecha_pago, actualizado_en
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(id_cuota) DO UPDATE SET
                periodo = excluded.periodo,
                fecha_emision = excluded.fecha_emision,
                fecha_vencimiento = excluded.fecha_vencimiento,
                importe = excluded.importe,
                estado_cuota = excluded.estado_cuota,
                fecha_pago = excluded.fecha_pago,
                actualizado_en = excluded.actualizado_en
            """,
            (
                cuota.id_cuota,
                cuota.id_poliza,
                cuota.periodo,
                cuota.fecha_emision.isoformat(),
                cuota.fecha_vencimiento.isoformat(),
                cuota.importe,
                cuota.estado.value,
                cuota.fecha_pago.isoformat() if cuota.fecha_pago else None,
            ),
        )
        self._connection.commit()

    def obtener_cuota(self, id_cuota: str) -> CuotaPolizaSeguro:
        row = self._connection.execute(
            "SELECT * FROM seguro_poliza_cuotas WHERE id_cuota = ?",
            (id_cuota,),
        ).fetchone()
        if row is None:
            raise KeyError(id_cuota)
        return self._row_a_cuota(row)

    def listar_cuotas_poliza(self, id_poliza: str) -> tuple[CuotaPolizaSeguro, ...]:
        rows = self._connection.execute(
            "SELECT * FROM seguro_poliza_cuotas WHERE id_poliza = ? ORDER BY fecha_vencimiento ASC",
            (id_poliza,),
        ).fetchall()
        return tuple(self._row_a_cuota(row) for row in rows)

    def listar_cuotas(self) -> tuple[CuotaPolizaSeguro, ...]:
        rows = self._connection.execute(
            "SELECT * FROM seguro_poliza_cuotas ORDER BY id_poliza, fecha_vencimiento ASC"
        ).fetchall()
        return tuple(self._row_a_cuota(row) for row in rows)

    def guardar_impago(self, evento: ImpagoPolizaSeguro) -> None:
        self._connection.execute(
            """
            INSERT INTO seguro_poliza_impagos (id_evento, id_poliza, id_cuota, fecha_evento, motivo)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id_evento) DO UPDATE SET
                id_cuota = excluded.id_cuota,
                fecha_evento = excluded.fecha_evento,
                motivo = excluded.motivo
            """,
            (
                evento.id_evento,
                evento.id_poliza,
                evento.id_cuota,
                evento.fecha_evento.isoformat(),
                evento.motivo,
            ),
        )
        self._connection.commit()

    def guardar_suspension(self, evento: SuspensionPolizaSeguro) -> None:
        self._connection.execute(
            """
            INSERT INTO seguro_poliza_suspensiones (id_evento, id_poliza, fecha_evento, motivo, automatica)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id_evento) DO UPDATE SET
                fecha_evento = excluded.fecha_evento,
                motivo = excluded.motivo,
                automatica = excluded.automatica
            """,
            (
                evento.id_evento,
                evento.id_poliza,
                evento.fecha_evento.isoformat(),
                evento.motivo,
                int(evento.automatica),
            ),
        )
        self._connection.commit()

    def guardar_reactivacion(self, evento: ReactivacionPolizaSeguro) -> None:
        self._connection.execute(
            """
            INSERT INTO seguro_poliza_reactivaciones (id_evento, id_poliza, fecha_evento, motivo)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id_evento) DO UPDATE SET
                fecha_evento = excluded.fecha_evento,
                motivo = excluded.motivo
            """,
            (
                evento.id_evento,
                evento.id_poliza,
                evento.fecha_evento.isoformat(),
                evento.motivo,
            ),
        )
        self._connection.commit()

    def tiene_suspension_activa(self, id_poliza: str) -> bool:
        suspension = self._connection.execute(
            "SELECT fecha_evento FROM seguro_poliza_suspensiones WHERE id_poliza = ? ORDER BY fecha_evento DESC LIMIT 1",
            (id_poliza,),
        ).fetchone()
        if suspension is None:
            return False
        reactivacion = self._connection.execute(
            "SELECT fecha_evento FROM seguro_poliza_reactivaciones WHERE id_poliza = ? ORDER BY fecha_evento DESC LIMIT 1",
            (id_poliza,),
        ).fetchone()
        if reactivacion is None:
            return True
        return str(suspension["fecha_evento"]) > str(reactivacion["fecha_evento"])

    @staticmethod
    def _row_a_cuota(row: sqlite3.Row) -> CuotaPolizaSeguro:
        from datetime import date

        fecha_pago = date.fromisoformat(row["fecha_pago"]) if row["fecha_pago"] else None
        return CuotaPolizaSeguro(
            id_cuota=row["id_cuota"],
            id_poliza=row["id_poliza"],
            periodo=row["periodo"],
            fecha_emision=date.fromisoformat(row["fecha_emision"]),
            fecha_vencimiento=date.fromisoformat(row["fecha_vencimiento"]),
            importe=float(row["importe"]),
            estado=EstadoCuotaPolizaSeguro(row["estado_cuota"]),
            fecha_pago=fecha_pago,
        )
