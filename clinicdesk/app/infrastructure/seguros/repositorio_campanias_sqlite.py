from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from clinicdesk.app.domain.seguros import (
    CampaniaSeguro,
    CriterioCampaniaSeguro,
    EstadoCampaniaSeguro,
    EstadoItemCampaniaSeguro,
    ItemCampaniaSeguro,
    OrigenCampaniaSeguro,
    ResultadoCampaniaSeguro,
    ResultadoItemCampaniaSeguro,
)
from clinicdesk.app.infrastructure.seguros.schema_sqlite import inicializar_schema_comercial_seguro


class RepositorioCampaniasSeguroSqlite:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._connection.row_factory = sqlite3.Row
        inicializar_schema_comercial_seguro(self._connection)

    def crear_campania(self, campania: CampaniaSeguro, items: tuple[ItemCampaniaSeguro, ...]) -> None:
        self.guardar_campania(campania)
        self._connection.executemany(
            """
            INSERT INTO seguro_campania_items (
                id_item, id_campania, id_oportunidad, estado_trabajo, accion_tomada,
                resultado, nota_corta, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item.id_item,
                    item.id_campania,
                    item.id_oportunidad,
                    item.estado_trabajo.value,
                    item.accion_tomada,
                    item.resultado.value,
                    item.nota_corta,
                    item.timestamp.isoformat(),
                )
                for item in items
            ],
        )
        self._connection.commit()

    def guardar_campania(self, campania: CampaniaSeguro) -> None:
        now_iso = datetime.now(tz=UTC).isoformat()
        r = campania.resultado_agregado
        self._connection.execute(
            """
            INSERT INTO seguro_campanias (
                id_campania, nombre, objetivo_comercial, origen, criterio_descripcion,
                criterio_referencia, creado_en, tamano_lote, estado, total_items, trabajados,
                convertidos, rechazados, pendientes, ratio_conversion, ratio_avance, actualizado_en
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id_campania) DO UPDATE SET
                nombre=excluded.nombre,
                objetivo_comercial=excluded.objetivo_comercial,
                origen=excluded.origen,
                criterio_descripcion=excluded.criterio_descripcion,
                criterio_referencia=excluded.criterio_referencia,
                tamano_lote=excluded.tamano_lote,
                estado=excluded.estado,
                total_items=excluded.total_items,
                trabajados=excluded.trabajados,
                convertidos=excluded.convertidos,
                rechazados=excluded.rechazados,
                pendientes=excluded.pendientes,
                ratio_conversion=excluded.ratio_conversion,
                ratio_avance=excluded.ratio_avance,
                actualizado_en=excluded.actualizado_en
            """,
            (
                campania.id_campania,
                campania.nombre,
                campania.objetivo_comercial,
                campania.criterio.origen.value,
                campania.criterio.descripcion,
                campania.criterio.id_referencia,
                campania.creado_en.isoformat(),
                campania.tamano_lote,
                campania.estado.value,
                r.total_items,
                r.trabajados,
                r.convertidos,
                r.rechazados,
                r.pendientes,
                r.ratio_conversion,
                r.ratio_avance,
                now_iso,
            ),
        )
        self._connection.commit()

    def obtener_campania(self, id_campania: str) -> CampaniaSeguro:
        row = self._connection.execute(
            "SELECT * FROM seguro_campanias WHERE id_campania = ?", (id_campania,)
        ).fetchone()
        if row is None:
            raise KeyError(id_campania)
        return _row_a_campania(row)

    def listar_campanias(self) -> tuple[CampaniaSeguro, ...]:
        rows = self._connection.execute("SELECT * FROM seguro_campanias ORDER BY creado_en DESC").fetchall()
        return tuple(_row_a_campania(row) for row in rows)

    def listar_items_campania(self, id_campania: str) -> tuple[ItemCampaniaSeguro, ...]:
        rows = self._connection.execute(
            "SELECT * FROM seguro_campania_items WHERE id_campania = ? ORDER BY timestamp ASC", (id_campania,)
        ).fetchall()
        return tuple(_row_a_item(row) for row in rows)

    def guardar_item_campania(self, item: ItemCampaniaSeguro) -> None:
        self._connection.execute(
            """
            UPDATE seguro_campania_items
            SET estado_trabajo = ?, accion_tomada = ?, resultado = ?, nota_corta = ?, timestamp = ?
            WHERE id_item = ?
            """,
            (
                item.estado_trabajo.value,
                item.accion_tomada,
                item.resultado.value,
                item.nota_corta,
                item.timestamp.isoformat(),
                item.id_item,
            ),
        )
        self._connection.commit()


def _row_a_campania(row: sqlite3.Row) -> CampaniaSeguro:
    return CampaniaSeguro(
        id_campania=row["id_campania"],
        nombre=row["nombre"],
        objetivo_comercial=row["objetivo_comercial"],
        creado_en=datetime.fromisoformat(row["creado_en"]),
        criterio=CriterioCampaniaSeguro(
            origen=OrigenCampaniaSeguro(row["origen"]),
            descripcion=row["criterio_descripcion"],
            id_referencia=row["criterio_referencia"],
        ),
        tamano_lote=int(row["tamano_lote"]),
        estado=EstadoCampaniaSeguro(row["estado"]),
        resultado_agregado=ResultadoCampaniaSeguro(
            total_items=int(row["total_items"]),
            trabajados=int(row["trabajados"]),
            convertidos=int(row["convertidos"]),
            rechazados=int(row["rechazados"]),
            pendientes=int(row["pendientes"]),
            ratio_conversion=float(row["ratio_conversion"]),
            ratio_avance=float(row["ratio_avance"]),
        ),
    )


def _row_a_item(row: sqlite3.Row) -> ItemCampaniaSeguro:
    return ItemCampaniaSeguro(
        id_item=row["id_item"],
        id_campania=row["id_campania"],
        id_oportunidad=row["id_oportunidad"],
        estado_trabajo=EstadoItemCampaniaSeguro(row["estado_trabajo"]),
        accion_tomada=row["accion_tomada"],
        resultado=ResultadoItemCampaniaSeguro(row["resultado"]),
        nota_corta=row["nota_corta"],
        timestamp=datetime.fromisoformat(row["timestamp"]),
    )
