from __future__ import annotations

from clinicdesk.app.application.seguros import (
    AnalizarMigracionSeguroUseCase,
    AprendizajeComercialSegurosService,
    CatalogoPlanesSeguro,
    GestionCampaniasSeguroService,
    GestionComercialSeguroService,
    SolicitudCrearCampaniaSeguro,
    SolicitudGestionItemCampaniaSeguro,
    SolicitudNuevaOportunidadSeguro,
)
from clinicdesk.app.domain.seguros import (
    CriterioCampaniaSeguro,
    EstadoItemCampaniaSeguro,
    EstadoOportunidadSeguro,
    FriccionMigracionSeguro,
    MotivacionCompraSeguro,
    NecesidadPrincipalSeguro,
    ObjecionComercialSeguro,
    OrigenCampaniaSeguro,
    OrigenClienteSeguro,
    ResultadoComercialSeguro,
    ResultadoItemCampaniaSeguro,
    SegmentoClienteSeguro,
    SensibilidadPrecioSeguro,
)
from clinicdesk.app.infrastructure.seguros.repositorio_campanias_sqlite import RepositorioCampaniasSeguroSqlite
from clinicdesk.app.infrastructure.seguros.repositorio_comercial_memoria import RepositorioComercialSeguroMemoria


def _servicios() -> tuple[GestionComercialSeguroService, GestionCampaniasSeguroService]:
    repo_comercial = RepositorioComercialSeguroMemoria()
    repo_campanias = RepositorioCampaniasSeguroSqlite(__import__("sqlite3").connect(":memory:"))
    gestion = GestionComercialSeguroService(AnalizarMigracionSeguroUseCase(CatalogoPlanesSeguro()), repo_comercial)
    campanias = GestionCampaniasSeguroService(repo_campanias)
    return gestion, campanias


def _abrir_oportunidad(
    gestion: GestionComercialSeguroService, id_oportunidad: str, sensibilidad: SensibilidadPrecioSeguro
) -> None:
    gestion.abrir_oportunidad(
        SolicitudNuevaOportunidadSeguro(
            id_oportunidad=id_oportunidad,
            id_candidato=f"cand-{id_oportunidad}",
            id_paciente=f"pac-{id_oportunidad}",
            segmento_cliente=SegmentoClienteSeguro.ASEGURADO_EXTERNO_MIGRAR,
            origen_cliente=OrigenClienteSeguro.WEB,
            necesidad_principal=NecesidadPrincipalSeguro.AHORRO_COSTE,
            motivaciones=(MotivacionCompraSeguro.MEJOR_RELACION_CALIDAD_PRECIO,),
            objecion_principal=ObjecionComercialSeguro.PRECIO_PERCIBIDO_ALTO,
            sensibilidad_precio=sensibilidad,
            friccion_migracion=FriccionMigracionSeguro.MEDIA,
            plan_origen_id="externo_basico",
            plan_destino_id="clinica_esencial",
        )
    )


def _campania_con_resultados(campanias: GestionCampaniasSeguroService) -> None:
    creada = campanias.crear_campania(
        SolicitudCrearCampaniaSeguro(
            id_campania="camp-1",
            nombre="Campaña externa web",
            objetivo_comercial="Cierre en seguimiento",
            criterio=CriterioCampaniaSeguro(
                origen=OrigenCampaniaSeguro.COHORTE,
                descripcion="Segmento externo",
                id_referencia=None,
            ),
            ids_oportunidad=("opp-1", "opp-2", "opp-3"),
        )
    )
    campanias.registrar_resultado_item(
        SolicitudGestionItemCampaniaSeguro(
            id_campania=creada.id_campania,
            id_item=f"{creada.id_campania}-item-1",
            estado_trabajo=EstadoItemCampaniaSeguro.CONVERTIDO,
            accion_tomada="llamada",
            resultado=ResultadoItemCampaniaSeguro.CONVERSION,
            nota_corta="ok",
        )
    )
    campanias.registrar_resultado_item(
        SolicitudGestionItemCampaniaSeguro(
            id_campania=creada.id_campania,
            id_item=f"{creada.id_campania}-item-2",
            estado_trabajo=EstadoItemCampaniaSeguro.CONTACTADO,
            accion_tomada="seguimiento",
            resultado=ResultadoItemCampaniaSeguro.RECHAZO,
            nota_corta="precio",
        )
    )
    campanias.registrar_resultado_item(
        SolicitudGestionItemCampaniaSeguro(
            id_campania=creada.id_campania,
            id_item=f"{creada.id_campania}-item-3",
            estado_trabajo=EstadoItemCampaniaSeguro.CONTACTADO,
            accion_tomada="seguimiento final",
            resultado=ResultadoItemCampaniaSeguro.CONVERSION,
            nota_corta="ok",
        )
    )


def test_panel_aprendizaje_genera_insights_y_playbooks() -> None:
    gestion, campanias = _servicios()
    for idx in (1, 2, 3):
        _abrir_oportunidad(gestion, f"opp-{idx}", SensibilidadPrecioSeguro.ALTA)
        gestion.preparar_oferta(f"opp-{idx}", ("nota",))
        gestion.registrar_seguimiento(
            f"opp-{idx}",
            EstadoOportunidadSeguro.OFERTA_ENVIADA,
            "argumento de ahorro anual",
            "interesado",
            "cierre",
        )
    gestion.cerrar_oportunidad("opp-1", ResultadoComercialSeguro.CONVERTIDO)
    _campania_con_resultados(campanias)

    panel = AprendizajeComercialSegurosService(gestion, campanias).construir_panel()

    assert panel.efectividad_campanias
    assert panel.efectividad_campanias[0].senal_efectividad in {"prometedora", "razonable", "floja"}
    assert panel.insights_argumentos
    assert panel.insights_planes
    assert panel.playbooks
    assert panel.recomendaciones_campania


def test_guardrail_muestra_insuficiente() -> None:
    gestion, campanias = _servicios()
    _abrir_oportunidad(gestion, "opp-x", SensibilidadPrecioSeguro.BAJA)

    panel = AprendizajeComercialSegurosService(gestion, campanias, muestra_minima=3).construir_panel()

    assert panel.insights_segmentos
    assert panel.insights_segmentos[0].metrica_principal is None
    assert "insuficiente" in panel.insights_segmentos[0].cautela_muestral.lower()
