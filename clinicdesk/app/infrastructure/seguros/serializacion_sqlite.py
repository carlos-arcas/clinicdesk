from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime

from clinicdesk.app.domain.seguros.comercial import (
    CandidatoSeguro,
    EstadoOportunidadSeguro,
    OfertaSeguro,
    OportunidadSeguro,
    RenovacionSeguro,
    ResultadoComercialSeguro,
    ResultadoRenovacionSeguro,
    SeguimientoOportunidadSeguro,
)


def row_a_oportunidad(row: sqlite3.Row, seguimientos: tuple[SeguimientoOportunidadSeguro, ...]) -> OportunidadSeguro:
    return OportunidadSeguro(
        id_oportunidad=row["id_oportunidad"],
        candidato=CandidatoSeguro(row["id_candidato"], row["id_paciente"], row["segmento"]),
        plan_origen_id=row["plan_origen_id"],
        plan_destino_id=row["plan_destino_id"],
        estado_actual=EstadoOportunidadSeguro(row["estado_actual"]),
        clasificacion_motor=row["clasificacion_motor"],
        seguimientos=seguimientos,
        resultado_comercial=(
            ResultadoComercialSeguro(row["resultado_comercial"]) if row["resultado_comercial"] else None
        ),
    )


def row_a_oferta(row: sqlite3.Row) -> OfertaSeguro:
    return OfertaSeguro(
        id_oferta=row["id_oferta"],
        id_oportunidad=row["id_oportunidad"],
        plan_propuesto_id=row["plan_propuesto_id"],
        resumen_valor=row["resumen_valor"],
        puntos_fuertes=tuple(json.loads(row["puntos_fuertes_json"])),
        riesgos_revision=tuple(json.loads(row["riesgos_revision_json"])),
        clasificacion_migracion=row["clasificacion_migracion"],
        notas_comerciales=tuple(json.loads(row["notas_comerciales_json"])),
    )


def row_a_renovacion(row: sqlite3.Row) -> RenovacionSeguro:
    return RenovacionSeguro(
        id_renovacion=row["id_renovacion"],
        id_oportunidad=row["id_oportunidad"],
        plan_vigente_id=row["plan_vigente_id"],
        fecha_renovacion=date.fromisoformat(row["fecha_renovacion"]),
        revision_pendiente=bool(row["revision_pendiente"]),
        resultado=ResultadoRenovacionSeguro(row["resultado"]),
    )


def row_a_seguimiento(row: sqlite3.Row) -> SeguimientoOportunidadSeguro:
    return SeguimientoOportunidadSeguro(
        fecha_registro=datetime.fromisoformat(row["fecha_registro"]),
        estado=EstadoOportunidadSeguro(row["estado"]),
        accion_comercial=row["accion_comercial"],
        nota_corta=row["nota_corta"],
        siguiente_paso=row["siguiente_paso"],
    )
