from __future__ import annotations

import sqlite3

from clinicdesk.app.application.seguros import (
    AnalizarMigracionSeguroUseCase,
    CatalogoPlanesSeguro,
    FiltroCarteraSeguro,
    GestionComercialSeguroService,
    SolicitudNuevaOportunidadSeguro,
)
from clinicdesk.app.domain.seguros import (
    EstadoOportunidadSeguro,
    FriccionMigracionSeguro,
    MotivacionCompraSeguro,
    NecesidadPrincipalSeguro,
    ObjecionComercialSeguro,
    OrigenClienteSeguro,
    ResultadoComercialSeguro,
    SegmentoClienteSeguro,
    SensibilidadPrecioSeguro,
)
from clinicdesk.app.infrastructure.seguros.repositorio_comercial_sqlite import RepositorioComercialSeguroSqlite


def _servicio() -> GestionComercialSeguroService:
    analizador = AnalizarMigracionSeguroUseCase(CatalogoPlanesSeguro())
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    return GestionComercialSeguroService(analizador, RepositorioComercialSeguroSqlite(connection))


def test_flujo_sqlite_cierre_y_cartera_filtrada() -> None:
    servicio = _servicio()
    servicio.abrir_oportunidad(
        SolicitudNuevaOportunidadSeguro(
            "opp-sql",
            "cand-sql",
            "pac-sql",
            SegmentoClienteSeguro.ASEGURADO_EXTERNO_MIGRAR,
            OrigenClienteSeguro.CALL_CENTER,
            NecesidadPrincipalSeguro.AHORRO_COSTE,
            (MotivacionCompraSeguro.MEJOR_RELACION_CALIDAD_PRECIO,),
            ObjecionComercialSeguro.PRECIO_PERCIBIDO_ALTO,
            SensibilidadPrecioSeguro.ALTA,
            FriccionMigracionSeguro.MEDIA,
            "externo_plus",
            "clinica_integral",
        )
    )
    servicio.preparar_oferta("opp-sql", ("seguimiento semanal",))
    servicio.registrar_seguimiento(
        "opp-sql",
        EstadoOportunidadSeguro.OFERTA_ENVIADA,
        "contacto_whatsapp",
        "cliente confirma recepcion",
        "llamada 48h",
    )
    cerrada = servicio.cerrar_oportunidad("opp-sql", ResultadoComercialSeguro.CONVERTIDO)

    cartera = servicio.listar_cartera(FiltroCarteraSeguro(solo_renovacion_pendiente=True))
    historial = servicio.recuperar_historial("opp-sql")

    assert cerrada.estado_actual is EstadoOportunidadSeguro.PENDIENTE_RENOVACION
    assert len(cartera) == 1
    assert historial[-1].estado is EstadoOportunidadSeguro.OFERTA_ENVIADA
