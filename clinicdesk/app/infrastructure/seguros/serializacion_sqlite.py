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
from clinicdesk.app.domain.seguros.segmentacion import (
    EncajePlanSeguro,
    EvaluacionFitComercialSeguro,
    FriccionMigracionSeguro,
    MotivacionCompraSeguro,
    NecesidadPrincipalSeguro,
    ObjecionComercialSeguro,
    OrigenClienteSeguro,
    PerfilComercialSeguro,
    SegmentoClienteSeguro,
    SensibilidadPrecioSeguro,
)


def row_a_oportunidad(row: sqlite3.Row, seguimientos: tuple[SeguimientoOportunidadSeguro, ...]) -> OportunidadSeguro:
    perfil = _row_a_perfil(row)
    return OportunidadSeguro(
        id_oportunidad=row["id_oportunidad"],
        candidato=CandidatoSeguro(row["id_candidato"], row["id_paciente"], row["segmento"]),
        plan_origen_id=row["plan_origen_id"],
        plan_destino_id=row["plan_destino_id"],
        estado_actual=EstadoOportunidadSeguro(row["estado_actual"]),
        clasificacion_motor=row["clasificacion_motor"],
        perfil_comercial=perfil,
        evaluacion_fit=_row_a_fit(row),
        seguimientos=seguimientos,
        resultado_comercial=(
            ResultadoComercialSeguro(row["resultado_comercial"]) if row["resultado_comercial"] else None
        ),
    )


def _row_a_perfil(row: sqlite3.Row) -> PerfilComercialSeguro | None:
    if not row["segmento_cliente"]:
        return None
    return PerfilComercialSeguro(
        segmento_cliente=SegmentoClienteSeguro(row["segmento_cliente"]),
        origen_cliente=OrigenClienteSeguro(row["origen_cliente"]),
        necesidad_principal=NecesidadPrincipalSeguro(row["necesidad_principal"]),
        motivaciones=tuple(MotivacionCompraSeguro(item) for item in json.loads(row["motivaciones_json"] or "[]")),
        objecion_principal=ObjecionComercialSeguro(row["objecion_principal"]),
        sensibilidad_precio=SensibilidadPrecioSeguro(row["sensibilidad_precio"]),
        friccion_migracion=FriccionMigracionSeguro(row["friccion_migracion"]),
    )


def _row_a_fit(row: sqlite3.Row) -> EvaluacionFitComercialSeguro | None:
    if not row["fit_comercial"]:
        return None
    return EvaluacionFitComercialSeguro(
        encaje_plan=EncajePlanSeguro(row["fit_comercial"]),
        motivo_principal=row["fit_motivo"] or "",
        riesgos_friccion=tuple(json.loads(row["fit_riesgos_json"] or "[]")),
        argumentos_valor=tuple(json.loads(row["fit_argumentos_json"] or "[]")),
        conviene_insistir=bool(row["fit_conviene_insistir"]),
        revision_humana_recomendada=bool(row["fit_revision_humana"]),
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
