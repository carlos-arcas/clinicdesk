from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from clinicdesk.app.domain.seguros.comercial import CandidatoSeguro, EstadoOportunidadSeguro, OportunidadSeguro
from clinicdesk.app.domain.seguros.cola_operativa import (
    AccionPendienteSeguro,
    EstadoOperativoSeguro,
    GestionOperativaColaSeguro,
)
from clinicdesk.app.infrastructure.seguros.repositorio_comercial_sqlite import RepositorioComercialSeguroSqlite


def _repo() -> RepositorioComercialSeguroSqlite:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    return RepositorioComercialSeguroSqlite(connection)


def test_sqlite_persiste_y_recupera_gestion_operativa() -> None:
    repo = _repo()
    repo.guardar_oportunidad(
        OportunidadSeguro(
            id_oportunidad="opp-op",
            candidato=CandidatoSeguro("cand-op", "pac-op", "seg"),
            plan_origen_id="externo_basico",
            plan_destino_id="clinica_esencial",
            estado_actual=EstadoOportunidadSeguro.EN_SEGUIMIENTO,
            clasificacion_motor="FAVORABLE",
            perfil_comercial=None,
            evaluacion_fit=None,
            seguimientos=(),
            resultado_comercial=None,
        )
    )
    gestion = GestionOperativaColaSeguro(
        id_oportunidad="opp-op",
        accion=AccionPendienteSeguro.CONTACTADO,
        estado_resultante=EstadoOperativoSeguro.EN_CURSO,
        nota_corta="llamada completada",
        siguiente_paso="enviar oferta",
        timestamp=datetime(2026, 1, 10, 9, 0, tzinfo=UTC),
    )

    repo.guardar_gestion_operativa(gestion)

    ultima = repo.obtener_ultima_gestion_operativa("opp-op")
    historial = repo.listar_gestiones_operativas("opp-op", limite=5)

    assert ultima is not None
    assert ultima.accion is AccionPendienteSeguro.CONTACTADO
    assert len(historial) == 1
    assert historial[0].siguiente_paso == "enviar oferta"


def test_listar_oportunidades_operativas_excluye_cerradas() -> None:
    repo = _repo()
    repo.guardar_oportunidad(
        OportunidadSeguro(
            id_oportunidad="opp-abierta",
            candidato=CandidatoSeguro("cand-a", "pac-a", "seg"),
            plan_origen_id="externo_basico",
            plan_destino_id="clinica_esencial",
            estado_actual=EstadoOportunidadSeguro.EN_SEGUIMIENTO,
            clasificacion_motor="FAVORABLE",
            perfil_comercial=None,
            evaluacion_fit=None,
            seguimientos=(),
            resultado_comercial=None,
        )
    )
    repo.guardar_oportunidad(
        OportunidadSeguro(
            id_oportunidad="opp-cerrada",
            candidato=CandidatoSeguro("cand-c", "pac-c", "seg"),
            plan_origen_id="externo_plus",
            plan_destino_id="clinica_integral",
            estado_actual=EstadoOportunidadSeguro.RECHAZADA,
            clasificacion_motor="REVISION",
            perfil_comercial=None,
            evaluacion_fit=None,
            seguimientos=(),
            resultado_comercial=None,
        )
    )

    operativas = repo.listar_oportunidades_por_gestion_operativa()

    assert [item.id_oportunidad for item in operativas] == ["opp-abierta"]
