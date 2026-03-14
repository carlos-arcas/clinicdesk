from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime

from clinicdesk.app.application.seguros.comercial import FiltroCarteraSeguro
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
from clinicdesk.app.infrastructure.seguros.repositorio_comercial_sqlite import RepositorioComercialSeguroSqlite


def _repo() -> RepositorioComercialSeguroSqlite:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    return RepositorioComercialSeguroSqlite(connection)


def test_roundtrip_oportunidad_con_historial() -> None:
    repo = _repo()
    seguimiento = SeguimientoOportunidadSeguro(
        datetime(2026, 3, 1, 11, 0, tzinfo=UTC),
        EstadoOportunidadSeguro.OFERTA_ENVIADA,
        "llamada",
        "recibe propuesta",
        "esperar respuesta",
    )
    oportunidad = OportunidadSeguro(
        id_oportunidad="opp-1",
        candidato=CandidatoSeguro("cand-1", "pac-1", "migracion"),
        plan_origen_id="externo_basico",
        plan_destino_id="clinica_esencial",
        estado_actual=EstadoOportunidadSeguro.OFERTA_ENVIADA,
        clasificacion_motor="ALTA",
        perfil_comercial=None,
        evaluacion_fit=None,
        seguimientos=(seguimiento,),
        resultado_comercial=None,
    )

    repo.guardar_oportunidad(oportunidad)
    recuperada = repo.obtener_oportunidad("opp-1")

    assert recuperada.estado_actual is EstadoOportunidadSeguro.OFERTA_ENVIADA
    assert recuperada.seguimientos[0].accion_comercial == "llamada"


def test_queries_cartera_y_renovaciones() -> None:
    repo = _repo()
    base = OportunidadSeguro(
        id_oportunidad="opp-2",
        candidato=CandidatoSeguro("cand-2", "pac-2", "migracion"),
        plan_origen_id="externo_plus",
        plan_destino_id="clinica_integral",
        estado_actual=EstadoOportunidadSeguro.PENDIENTE_RENOVACION,
        clasificacion_motor="MEDIA",
        perfil_comercial=None,
        evaluacion_fit=None,
        seguimientos=(),
        resultado_comercial=ResultadoComercialSeguro.CONVERTIDO,
    )
    repo.guardar_oportunidad(base)
    repo.guardar_oferta(
        OfertaSeguro(
            id_oferta="of-opp-2",
            id_oportunidad="opp-2",
            plan_propuesto_id="clinica_integral",
            resumen_valor="valor",
            puntos_fuertes=("copago",),
            riesgos_revision=("carencia",),
            clasificacion_migracion="MEDIA",
            notas_comerciales=("ok",),
        )
    )
    repo.guardar_renovacion(
        RenovacionSeguro(
            id_renovacion="ren-opp-2",
            id_oportunidad="opp-2",
            plan_vigente_id="clinica_integral",
            fecha_renovacion=date(2026, 12, 1),
            revision_pendiente=True,
            resultado=ResultadoRenovacionSeguro.PENDIENTE,
        )
    )

    cartera_estado = repo.listar_oportunidades(FiltroCarteraSeguro(estado=EstadoOportunidadSeguro.PENDIENTE_RENOVACION))
    cartera_renovacion = repo.listar_oportunidades(FiltroCarteraSeguro(solo_renovacion_pendiente=True))

    assert len(cartera_estado) == 1
    assert len(cartera_renovacion) == 1
    assert repo.obtener_oferta_por_oportunidad("opp-2") is not None
    assert len(repo.listar_renovaciones_pendientes()) == 1
    assert repo.listar_oportunidades_por_fit()


def test_dataset_ml_comercial_preparado() -> None:
    repo = _repo()
    repo.guardar_oportunidad(
        OportunidadSeguro(
            id_oportunidad="opp-3",
            candidato=CandidatoSeguro("cand-3", "pac-3", "migracion"),
            plan_origen_id="externo_plus",
            plan_destino_id="clinica_integral",
            estado_actual=EstadoOportunidadSeguro.RECHAZADA,
            clasificacion_motor="BAJA",
            perfil_comercial=None,
            evaluacion_fit=None,
            seguimientos=(),
            resultado_comercial=ResultadoComercialSeguro.RECHAZADO,
        )
    )

    dataset = repo.construir_dataset_ml_comercial()

    assert dataset
    assert dataset[0]["id_oportunidad"] == "opp-3"
    assert "total_seguimientos" in dataset[0]
