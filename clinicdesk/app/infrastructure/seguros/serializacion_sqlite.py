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
from clinicdesk.app.domain.seguros.postventa import (
    AseguradoPrincipalSeguro,
    BeneficiarioSeguro,
    CoberturaActivaPolizaSeguro,
    EstadoAseguradoSeguro,
    EstadoIncidenciaPolizaSeguro,
    EstadoPolizaSeguro,
    EstadoRenovacionPolizaSeguro,
    IncidenciaPolizaSeguro,
    PolizaSeguro,
    RenovacionPolizaSeguro,
    TipoIncidenciaPolizaSeguro,
    VigenciaPolizaSeguro,
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


def poliza_a_payload_sqlite(poliza: PolizaSeguro) -> tuple[object, ...]:
    coberturas = [
        {
            "codigo_cobertura": item.codigo_cobertura,
            "descripcion": item.descripcion,
            "activa": item.activa,
        }
        for item in poliza.coberturas
    ]
    return (
        poliza.id_poliza,
        poliza.id_oportunidad_origen,
        poliza.id_paciente,
        poliza.id_plan,
        poliza.estado.value,
        poliza.titular.id_asegurado,
        poliza.titular.nombre,
        poliza.titular.documento,
        poliza.titular.estado.value,
        poliza.vigencia.fecha_inicio.isoformat(),
        poliza.vigencia.fecha_fin.isoformat(),
        poliza.renovacion.fecha_renovacion_prevista.isoformat(),
        poliza.renovacion.estado.value,
        json.dumps(coberturas),
    )


def row_a_poliza(
    row: sqlite3.Row,
    beneficiarios: tuple[BeneficiarioSeguro, ...],
    incidencias: tuple[IncidenciaPolizaSeguro, ...],
) -> PolizaSeguro:
    coberturas = tuple(
        CoberturaActivaPolizaSeguro(
            codigo_cobertura=item["codigo_cobertura"],
            descripcion=item["descripcion"],
            activa=bool(item["activa"]),
        )
        for item in json.loads(row["coberturas_json"] or "[]")
    )
    return PolizaSeguro(
        id_poliza=row["id_poliza"],
        id_oportunidad_origen=row["id_oportunidad_origen"],
        id_paciente=row["id_paciente"],
        id_plan=row["id_plan"],
        estado=EstadoPolizaSeguro(row["estado_poliza"]),
        titular=AseguradoPrincipalSeguro(
            id_asegurado=row["titular_id_asegurado"],
            nombre=row["titular_nombre"],
            documento=row["titular_documento"],
            estado=EstadoAseguradoSeguro(row["titular_estado"]),
        ),
        beneficiarios=beneficiarios,
        vigencia=VigenciaPolizaSeguro(
            fecha_inicio=date.fromisoformat(row["vigencia_inicio"]),
            fecha_fin=date.fromisoformat(row["vigencia_fin"]),
        ),
        renovacion=RenovacionPolizaSeguro(
            fecha_renovacion_prevista=date.fromisoformat(row["renovacion_fecha"]),
            estado=EstadoRenovacionPolizaSeguro(row["renovacion_estado"]),
        ),
        coberturas=coberturas,
        incidencias=incidencias,
    )


def row_a_beneficiario(row: sqlite3.Row) -> BeneficiarioSeguro:
    return BeneficiarioSeguro(
        id_beneficiario=row["id_beneficiario"],
        nombre=row["nombre"],
        parentesco=row["parentesco"],
        estado=EstadoAseguradoSeguro(row["estado"]),
    )


def row_a_incidencia(row: sqlite3.Row) -> IncidenciaPolizaSeguro:
    return IncidenciaPolizaSeguro(
        id_incidencia=row["id_incidencia"],
        tipo=TipoIncidenciaPolizaSeguro(row["tipo"]),
        descripcion=row["descripcion"],
        estado=EstadoIncidenciaPolizaSeguro(row["estado"]),
        fecha_apertura=date.fromisoformat(row["fecha_apertura"]),
    )
