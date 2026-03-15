from __future__ import annotations

import sqlite3

from clinicdesk.app.application.seguros import (
    CampaniaAccionableSeguro,
    GestionCampaniasSeguroService,
    SolicitudCrearCampaniaDesdeSugerencia,
    SolicitudGestionItemCampaniaSeguro,
)
from clinicdesk.app.domain.seguros import (
    EstadoCampaniaSeguro,
    EstadoItemCampaniaSeguro,
    ResultadoItemCampaniaSeguro,
)
from clinicdesk.app.infrastructure.seguros.repositorio_campanias_sqlite import RepositorioCampaniasSeguroSqlite


def _servicio() -> GestionCampaniasSeguroService:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    return GestionCampaniasSeguroService(RepositorioCampaniasSeguroSqlite(connection))


def test_crear_campania_congela_lote_desde_sugerencia() -> None:
    servicio = _servicio()
    sugerencia = CampaniaAccionableSeguro(
        id_campania="campania_precio_argumento",
        titulo="Oferta precio",
        criterio="Objeción precio alta",
        tamano_estimado=2,
        motivo="objeción persistente",
        accion_recomendada="llamar",
        cautela="sin promesas",
        ids_oportunidad=("opp-1", "opp-2"),
    )

    campania = servicio.crear_desde_sugerencia(
        SolicitudCrearCampaniaDesdeSugerencia(
            id_campania_nueva="exec-camp-1",
            objetivo_comercial="reactivar conversion",
            sugerencia=sugerencia,
        )
    )
    _, items = servicio.obtener_detalle(campania.id_campania)

    assert campania.tamano_lote == 2
    assert campania.estado is EstadoCampaniaSeguro.CREADA
    assert tuple(item.id_oportunidad for item in items) == ("opp-1", "opp-2")


def test_registro_item_actualiza_resultado_agregado_y_cierre() -> None:
    servicio = _servicio()
    sugerencia = CampaniaAccionableSeguro(
        id_campania="campania_renovacion_riesgo",
        titulo="Retencion",
        criterio="Renovacion vencida",
        tamano_estimado=1,
        motivo="riesgo alto",
        accion_recomendada="contactar hoy",
        cautela="no causalidad",
        ids_oportunidad=("opp-r1",),
    )
    campania = servicio.crear_desde_sugerencia(
        SolicitudCrearCampaniaDesdeSugerencia("exec-camp-2", "retener", sugerencia)
    )
    _, items = servicio.obtener_detalle(campania.id_campania)

    actualizada = servicio.registrar_resultado_item(
        SolicitudGestionItemCampaniaSeguro(
            id_campania=campania.id_campania,
            id_item=items[0].id_item,
            estado_trabajo=EstadoItemCampaniaSeguro.CONVERTIDO,
            accion_tomada="llamada y oferta",
            resultado=ResultadoItemCampaniaSeguro.CONVERSION,
            nota_corta="acepta",
        )
    )

    assert actualizada.estado is EstadoCampaniaSeguro.CERRADA
    assert actualizada.resultado_agregado.trabajados == 1
    assert actualizada.resultado_agregado.convertidos == 1
    assert actualizada.resultado_agregado.ratio_conversion == 1.0


def test_persistencia_sqlite_lista_campanias_e_items() -> None:
    servicio = _servicio()
    sugerencia = CampaniaAccionableSeguro(
        id_campania="campania_fit_bajo",
        titulo="Fit bajo",
        criterio="Fit bajo + objeción",
        tamano_estimado=2,
        motivo="atasco embudo",
        accion_recomendada="reencuadre valor",
        cautela="muestra chica",
        ids_oportunidad=("opp-a", "opp-b"),
    )
    servicio.crear_desde_sugerencia(SolicitudCrearCampaniaDesdeSugerencia("exec-camp-3", "avanzar", sugerencia))

    campanias = servicio.listar_campanias()
    _, items = servicio.obtener_detalle("exec-camp-3")

    assert len(campanias) == 1
    assert campanias[0].criterio.id_referencia == "campania_fit_bajo"
    assert len(items) == 2
