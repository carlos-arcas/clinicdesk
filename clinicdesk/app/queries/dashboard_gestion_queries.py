from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import sqlite3

from clinicdesk.app.application.usecases.dashboard_gestion_prediccion import CitaGestionHoyDTO
from clinicdesk.app.infrastructure.sqlite.proveedor_conexion_sqlite import ProveedorConexionSqlitePorHilo

_ESTADOS_PROXIMOS = ("PROGRAMADA", "CONFIRMADA", "EN_CURSO")


@dataclass(frozen=True, slots=True)
class FilaCitaHoyGestion:
    cita_id: int
    hora: str
    paciente_nombre: str
    medico_nombre: str
    paciente_id: int
    medico_id: int
    antelacion_dias: int


@dataclass(frozen=True, slots=True)
class OpcionFiltroDTO:
    valor: int
    etiqueta: str


@dataclass(frozen=True, slots=True)
class ResumenCentroSaludRow:
    total_citas: int
    total_completadas: int
    total_pendientes: int
    total_canceladas: int
    total_no_presentadas: int
    riesgo_medio_pct: float | None
    total_riesgo_alto: int


class DashboardGestionQueries:
    def __init__(self, proveedor: ProveedorConexionSqlitePorHilo | sqlite3.Connection) -> None:
        self._proveedor = proveedor

    def _con(self) -> sqlite3.Connection:
        return self._proveedor if isinstance(self._proveedor, sqlite3.Connection) else self._proveedor.obtener()

    def listar_citas_hoy_gestion(self, limite: int) -> tuple[CitaGestionHoyDTO, ...]:
        rows = (
            self._con()
            .execute(
                """
            SELECT
                c.id AS cita_id,
                time(c.inicio) AS hora,
                (p.nombre || ' ' || p.apellidos) AS paciente_nombre,
                (m.nombre || ' ' || m.apellidos) AS medico_nombre,
                c.paciente_id,
                c.medico_id,
                CAST(julianday(substr(c.inicio, 1, 10)) - julianday('now') AS INTEGER) AS antelacion_dias
            FROM citas c
            JOIN pacientes p ON p.id = c.paciente_id
            JOIN medicos m ON m.id = c.medico_id
            WHERE c.activo = 1
              AND c.estado IN (?, ?, ?)
              AND datetime(c.inicio) >= datetime('now', 'start of day')
              AND datetime(c.inicio) < datetime('now', 'start of day', '+1 day')
            ORDER BY datetime(c.inicio) ASC
            LIMIT ?
            """,
                (*_ESTADOS_PROXIMOS, limite),
            )
            .fetchall()
        )
        return tuple(
            CitaGestionHoyDTO(
                cita_id=int(row["cita_id"]),
                hora=str(row["hora"]),
                paciente_nombre=str(row["paciente_nombre"]),
                medico_nombre=str(row["medico_nombre"]),
                paciente_id=int(row["paciente_id"]),
                medico_id=int(row["medico_id"]),
                antelacion_dias=max(0, int(row["antelacion_dias"] or 0)),
            )
            for row in rows
        )

    def listar_medicos_filtro(self) -> tuple[OpcionFiltroDTO, ...]:
        rows = self._con().execute(
            "SELECT id, (nombre || ' ' || apellidos) AS etiqueta FROM medicos WHERE activo = 1 ORDER BY etiqueta"
        )
        return tuple(OpcionFiltroDTO(valor=int(row["id"]), etiqueta=str(row["etiqueta"])) for row in rows)

    def listar_salas_filtro(self) -> tuple[OpcionFiltroDTO, ...]:
        rows = self._con().execute("SELECT id, nombre AS etiqueta FROM salas WHERE activa = 1 ORDER BY nombre")
        return tuple(OpcionFiltroDTO(valor=int(row["id"]), etiqueta=str(row["etiqueta"])) for row in rows)

    def obtener_resumen_centro_salud(
        self,
        desde: date,
        hasta: date,
        medico_id: int | None,
        sala_id: int | None,
        estado: str | None,
    ) -> ResumenCentroSaludRow:
        where, params = _build_where_operativa(desde, hasta, medico_id, sala_id, estado)
        row = (
            self._con()
            .execute(
                f"""
            SELECT
                COUNT(1) AS total_citas,
                SUM(CASE WHEN c.estado = 'REALIZADA' THEN 1 ELSE 0 END) AS total_completadas,
                SUM(CASE WHEN c.estado IN ('PROGRAMADA', 'CONFIRMADA', 'EN_CURSO') THEN 1 ELSE 0 END) AS total_pendientes,
                SUM(CASE WHEN c.estado IN ('CANCELADA', 'NO_PRESENTADO') THEN 1 ELSE 0 END) AS total_canceladas,
                SUM(CASE WHEN c.estado = 'NO_PRESENTADO' THEN 1 ELSE 0 END) AS total_no_presentadas,
                AVG(
                    CASE pal.riesgo
                        WHEN 'ALTO' THEN 100.0
                        WHEN 'MEDIO' THEN 50.0
                        WHEN 'BAJO' THEN 0.0
                    END
                ) AS riesgo_medio_pct,
                SUM(CASE WHEN pal.riesgo = 'ALTO' THEN 1 ELSE 0 END) AS total_riesgo_alto
            FROM citas c
            LEFT JOIN (
                SELECT p1.cita_id, p1.riesgo
                FROM predicciones_ausencias_log p1
                JOIN (
                    SELECT cita_id, MAX(modelo_fecha_utc) AS modelo_fecha_utc
                    FROM predicciones_ausencias_log
                    GROUP BY cita_id
                ) ult
                    ON ult.cita_id = p1.cita_id
                   AND ult.modelo_fecha_utc = p1.modelo_fecha_utc
            ) pal ON pal.cita_id = c.id
            {where}
            """,
                params,
            )
            .fetchone()
        )
        return ResumenCentroSaludRow(
            total_citas=int(row["total_citas"] or 0),
            total_completadas=int(row["total_completadas"] or 0),
            total_pendientes=int(row["total_pendientes"] or 0),
            total_canceladas=int(row["total_canceladas"] or 0),
            total_no_presentadas=int(row["total_no_presentadas"] or 0),
            riesgo_medio_pct=float(row["riesgo_medio_pct"]) if row["riesgo_medio_pct"] is not None else None,
            total_riesgo_alto=int(row["total_riesgo_alto"] or 0),
        )

    def contar_pacientes_riesgo_operativo(self, desde: date, hasta: date) -> int:
        row = (
            self._con()
            .execute(
                """
            SELECT COUNT(1) AS total
            FROM (
                SELECT c.paciente_id
                FROM citas c
                WHERE c.activo = 1
                  AND date(c.inicio) BETWEEN date(?) AND date(?)
                GROUP BY c.paciente_id
                HAVING SUM(CASE WHEN c.estado IN ('NO_PRESENTADO', 'CANCELADA') THEN 1 ELSE 0 END) >= 2
            ) x
            """,
                (desde.isoformat(), hasta.isoformat()),
            )
            .fetchone()
        )
        return int(row["total"] or 0)

    def contar_cuellos_botella(self, desde: date, hasta: date, medico_id: int | None, sala_id: int | None) -> int:
        where, params = _build_where_operativa(desde, hasta, medico_id, sala_id, None)
        row = (
            self._con()
            .execute(
                f"""
            SELECT COUNT(1) AS total
            FROM (
                SELECT date(c.inicio) AS fecha, strftime('%H', c.inicio) AS hora, COUNT(1) AS total_hora
                FROM citas c
                {where}
                GROUP BY fecha, hora
                HAVING COUNT(1) >= 4
            ) x
            """,
                params,
            )
            .fetchone()
        )
        return int(row["total"] or 0)


def _build_where_operativa(
    desde: date, hasta: date, medico_id: int | None, sala_id: int | None, estado: str | None
) -> tuple[str, list[object]]:
    clauses = ["c.activo = 1", "date(c.inicio) BETWEEN date(?) AND date(?)"]
    params: list[object] = [desde.isoformat(), hasta.isoformat()]
    if medico_id is not None:
        clauses.append("c.medico_id = ?")
        params.append(medico_id)
    if sala_id is not None:
        clauses.append("c.sala_id = ?")
        params.append(sala_id)
    if estado:
        clauses.append("c.estado = ?")
        params.append(estado)
    return f"WHERE {' AND '.join(clauses)}", params
