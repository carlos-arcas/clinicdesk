from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from clinicdesk.app.application.seguros.comercial import FiltroCarteraSeguro
from clinicdesk.app.domain.seguros.comercial import (
    OfertaSeguro,
    OportunidadSeguro,
    RenovacionSeguro,
    ResultadoRenovacionSeguro,
    SeguimientoOportunidadSeguro,
)
from clinicdesk.app.infrastructure.seguros.schema_sqlite import inicializar_schema_comercial_seguro
from clinicdesk.app.infrastructure.seguros.serializacion_sqlite import (
    row_a_oferta,
    row_a_oportunidad,
    row_a_renovacion,
    row_a_seguimiento,
)


class RepositorioComercialSeguroSqlite:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._connection.row_factory = sqlite3.Row
        inicializar_schema_comercial_seguro(self._connection)

    def guardar_oportunidad(self, oportunidad: OportunidadSeguro) -> None:
        now_iso = datetime.now().isoformat()
        creado_en = self._obtener_creado_en_existente(oportunidad.id_oportunidad, now_iso)
        self._connection.execute(
            """
            INSERT INTO seguro_oportunidades (
                id_oportunidad, id_candidato, id_paciente, segmento, plan_origen_id,
                plan_destino_id, estado_actual, clasificacion_motor, resultado_comercial,
                creado_en, actualizado_en
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id_oportunidad) DO UPDATE SET
                id_candidato = excluded.id_candidato,
                id_paciente = excluded.id_paciente,
                segmento = excluded.segmento,
                plan_origen_id = excluded.plan_origen_id,
                plan_destino_id = excluded.plan_destino_id,
                estado_actual = excluded.estado_actual,
                clasificacion_motor = excluded.clasificacion_motor,
                resultado_comercial = excluded.resultado_comercial,
                actualizado_en = excluded.actualizado_en
            """,
            (
                oportunidad.id_oportunidad,
                oportunidad.candidato.id_candidato,
                oportunidad.candidato.id_paciente,
                oportunidad.candidato.segmento,
                oportunidad.plan_origen_id,
                oportunidad.plan_destino_id,
                oportunidad.estado_actual.value,
                oportunidad.clasificacion_motor,
                oportunidad.resultado_comercial.value if oportunidad.resultado_comercial else None,
                creado_en,
                now_iso,
            ),
        )
        self._reemplazar_seguimientos(oportunidad)
        self._connection.commit()

    def obtener_oportunidad(self, id_oportunidad: str) -> OportunidadSeguro:
        row = self._connection.execute(
            "SELECT * FROM seguro_oportunidades WHERE id_oportunidad = ?", (id_oportunidad,)
        ).fetchone()
        if row is None:
            raise KeyError(id_oportunidad)
        return row_a_oportunidad(row, self.listar_historial_oportunidad(id_oportunidad))

    def guardar_oferta(self, oferta: OfertaSeguro) -> None:
        now_iso = datetime.now().isoformat()
        self._connection.execute(
            """
            INSERT INTO seguro_ofertas (
                id_oferta, id_oportunidad, plan_propuesto_id, resumen_valor,
                puntos_fuertes_json, riesgos_revision_json, clasificacion_migracion,
                notas_comerciales_json, creada_en, actualizada_en
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id_oferta) DO UPDATE SET
                plan_propuesto_id = excluded.plan_propuesto_id,
                resumen_valor = excluded.resumen_valor,
                puntos_fuertes_json = excluded.puntos_fuertes_json,
                riesgos_revision_json = excluded.riesgos_revision_json,
                clasificacion_migracion = excluded.clasificacion_migracion,
                notas_comerciales_json = excluded.notas_comerciales_json,
                actualizada_en = excluded.actualizada_en
            """,
            (
                oferta.id_oferta,
                oferta.id_oportunidad,
                oferta.plan_propuesto_id,
                oferta.resumen_valor,
                json.dumps(oferta.puntos_fuertes),
                json.dumps(oferta.riesgos_revision),
                oferta.clasificacion_migracion,
                json.dumps(oferta.notas_comerciales),
                now_iso,
                now_iso,
            ),
        )
        self._connection.commit()

    def obtener_oferta_por_oportunidad(self, id_oportunidad: str) -> OfertaSeguro | None:
        row = self._connection.execute(
            "SELECT * FROM seguro_ofertas WHERE id_oportunidad = ?", (id_oportunidad,)
        ).fetchone()
        return row_a_oferta(row) if row else None

    def guardar_renovacion(self, renovacion: RenovacionSeguro) -> None:
        now_iso = datetime.now().isoformat()
        self._connection.execute(
            """
            INSERT INTO seguro_renovaciones (
                id_renovacion, id_oportunidad, plan_vigente_id, fecha_renovacion,
                revision_pendiente, resultado, actualizada_en
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id_renovacion) DO UPDATE SET
                id_oportunidad = excluded.id_oportunidad,
                plan_vigente_id = excluded.plan_vigente_id,
                fecha_renovacion = excluded.fecha_renovacion,
                revision_pendiente = excluded.revision_pendiente,
                resultado = excluded.resultado,
                actualizada_en = excluded.actualizada_en
            """,
            (
                renovacion.id_renovacion,
                renovacion.id_oportunidad,
                renovacion.plan_vigente_id,
                renovacion.fecha_renovacion.isoformat(),
                int(renovacion.revision_pendiente),
                renovacion.resultado.value,
                now_iso,
            ),
        )
        self._connection.commit()

    def listar_renovaciones_pendientes(self) -> tuple[RenovacionSeguro, ...]:
        rows = self._connection.execute(
            "SELECT * FROM seguro_renovaciones WHERE revision_pendiente = 1 AND resultado = ? ORDER BY fecha_renovacion ASC",
            (ResultadoRenovacionSeguro.PENDIENTE.value,),
        ).fetchall()
        return tuple(row_a_renovacion(row) for row in rows)

    def listar_oportunidades(self, filtro: FiltroCarteraSeguro) -> tuple[OportunidadSeguro, ...]:
        where_sql, params = _construir_where_cartera(filtro)
        rows = self._connection.execute(
            f"SELECT * FROM seguro_oportunidades o {where_sql} ORDER BY o.actualizado_en DESC",
            params,
        ).fetchall()
        return tuple(row_a_oportunidad(row, self.listar_historial_oportunidad(row["id_oportunidad"])) for row in rows)

    def listar_seguimientos_recientes(self, limite: int = 20) -> tuple[SeguimientoOportunidadSeguro, ...]:
        rows = self._connection.execute(
            "SELECT * FROM seguro_seguimientos ORDER BY fecha_registro DESC LIMIT ?",
            (limite,),
        ).fetchall()
        return tuple(row_a_seguimiento(row) for row in rows)

    def listar_historial_oportunidad(self, id_oportunidad: str) -> tuple[SeguimientoOportunidadSeguro, ...]:
        rows = self._connection.execute(
            "SELECT * FROM seguro_seguimientos WHERE id_oportunidad = ? ORDER BY fecha_registro ASC",
            (id_oportunidad,),
        ).fetchall()
        return tuple(row_a_seguimiento(row) for row in rows)

    def construir_dataset_ml_comercial(self) -> list[dict[str, object]]:
        rows = self._connection.execute(
            """
            SELECT o.id_oportunidad, o.plan_origen_id, o.plan_destino_id, o.clasificacion_motor, o.estado_actual,
                   o.resultado_comercial, o.creado_en, o.actualizado_en,
                   CAST((julianday(o.actualizado_en) - julianday(o.creado_en)) AS INTEGER) AS dias_ciclo,
                   (SELECT COUNT(*) FROM seguro_seguimientos s WHERE s.id_oportunidad = o.id_oportunidad) AS total_seguimientos,
                   EXISTS (SELECT 1 FROM seguro_renovaciones r WHERE r.id_oportunidad = o.id_oportunidad) AS tiene_renovacion,
                   EXISTS (SELECT 1 FROM seguro_renovaciones r WHERE r.id_oportunidad = o.id_oportunidad AND r.resultado = ?) AS renovada
            FROM seguro_oportunidades o
            ORDER BY o.actualizado_en DESC
            """,
            (ResultadoRenovacionSeguro.RENOVADA.value,),
        ).fetchall()
        return [dict(row) for row in rows]

    def _reemplazar_seguimientos(self, oportunidad: OportunidadSeguro) -> None:
        self._connection.execute(
            "DELETE FROM seguro_seguimientos WHERE id_oportunidad = ?", (oportunidad.id_oportunidad,)
        )
        self._connection.executemany(
            """
            INSERT INTO seguro_seguimientos (id_oportunidad, fecha_registro, estado, accion_comercial, nota_corta, siguiente_paso)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    oportunidad.id_oportunidad,
                    seg.fecha_registro.isoformat(),
                    seg.estado.value,
                    seg.accion_comercial,
                    seg.nota_corta,
                    seg.siguiente_paso,
                )
                for seg in oportunidad.seguimientos
            ],
        )

    def _obtener_creado_en_existente(self, id_oportunidad: str, fallback: str) -> str:
        row = self._connection.execute(
            "SELECT creado_en FROM seguro_oportunidades WHERE id_oportunidad = ?", (id_oportunidad,)
        ).fetchone()
        return row["creado_en"] if row else fallback


def _construir_where_cartera(filtro: FiltroCarteraSeguro) -> tuple[str, tuple[object, ...]]:
    where: list[str] = []
    params: list[object] = []
    if filtro.estado:
        where.append("o.estado_actual = ?")
        params.append(filtro.estado.value)
    if filtro.plan_destino_id:
        where.append("o.plan_destino_id = ?")
        params.append(filtro.plan_destino_id)
    if filtro.clasificacion_migracion:
        where.append("o.clasificacion_motor = ?")
        params.append(filtro.clasificacion_migracion)
    if filtro.fecha_desde:
        where.append("date(o.actualizado_en) >= date(?)")
        params.append(filtro.fecha_desde.isoformat())
    if filtro.solo_renovacion_pendiente:
        where.append(
            "EXISTS (SELECT 1 FROM seguro_renovaciones r WHERE r.id_oportunidad = o.id_oportunidad "
            "AND r.revision_pendiente = 1 AND r.resultado = ? )"
        )
        params.append(ResultadoRenovacionSeguro.PENDIENTE.value)
    return (f"WHERE {' AND '.join(where)}" if where else "", tuple(params))
