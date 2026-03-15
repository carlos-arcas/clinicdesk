from clinicdesk.app.application.seguros import (
    AnalizarMigracionSeguroUseCase,
    CatalogoPlanesSeguro,
    EconomiaValorSeguroService,
    GestionComercialSeguroService,
    RecomendadorProductoSeguroService,
    ScoringComercialSeguroService,
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
from clinicdesk.app.infrastructure.seguros.repositorio_comercial_memoria import RepositorioComercialSeguroMemoria


def _servicios() -> tuple[GestionComercialSeguroService, EconomiaValorSeguroService]:
    repo = RepositorioComercialSeguroMemoria()
    catalogo = CatalogoPlanesSeguro()
    gestion = GestionComercialSeguroService(AnalizarMigracionSeguroUseCase(catalogo), repo)
    scoring = ScoringComercialSeguroService(repo, minimo_muestras=3)
    recomendador = RecomendadorProductoSeguroService(catalogo, scoring)
    return gestion, EconomiaValorSeguroService(catalogo, scoring, recomendador)


def _abrir(
    gestion: GestionComercialSeguroService,
    id_oportunidad: str,
    sensibilidad: SensibilidadPrecioSeguro,
    friccion: FriccionMigracionSeguro,
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
            friccion_migracion=friccion,
            plan_origen_id="externo_basico",
            plan_destino_id="clinica_integral",
        )
    )


def test_panel_valor_prioriza_por_score_y_margen_esperado() -> None:
    gestion, economia = _servicios()
    _abrir(gestion, "opp-alta", SensibilidadPrecioSeguro.BAJA, FriccionMigracionSeguro.BAJA)
    _abrir(gestion, "opp-baja", SensibilidadPrecioSeguro.ALTA, FriccionMigracionSeguro.ALTA)
    gestion.preparar_oferta("opp-alta", ("prioritaria",))
    gestion.registrar_seguimiento("opp-alta", EstadoOportunidadSeguro.OFERTA_ENVIADA, "llamada", "ok", "cierre")
    gestion.cerrar_oportunidad("opp-alta", ResultadoComercialSeguro.CONVERTIDO)

    panel = economia.construir_panel(gestion.listar_cartera(), gestion.listar_renovaciones_pendientes())

    assert panel.prioridades
    assert panel.prioridades[0].score_impacto >= panel.prioridades[-1].score_impacto
    assert panel.prioridades[0].accion_sugerida


def test_guardrail_evidencia_insuficiente_en_muestras_debiles() -> None:
    gestion, economia = _servicios()
    _abrir(gestion, "opp-unica", SensibilidadPrecioSeguro.MEDIA, FriccionMigracionSeguro.MEDIA)

    panel = economia.construir_panel(gestion.listar_cartera(), gestion.listar_renovaciones_pendientes())

    assert panel.prioridades[0].categoria_valor.value in {"BAJO", "EVIDENCIA_INSUFICIENTE"}
    assert panel.prioridades[0].riesgo_economico.value in {"MEDIA", "ALTA"}


def test_campanias_y_segmentos_muestran_valor_rentable_prudente() -> None:
    gestion, economia = _servicios()
    _abrir(gestion, "opp-1", SensibilidadPrecioSeguro.BAJA, FriccionMigracionSeguro.BAJA)
    _abrir(gestion, "opp-2", SensibilidadPrecioSeguro.MEDIA, FriccionMigracionSeguro.MEDIA)
    _abrir(gestion, "opp-3", SensibilidadPrecioSeguro.ALTA, FriccionMigracionSeguro.ALTA)

    panel = economia.construir_panel(gestion.listar_cartera(), gestion.listar_renovaciones_pendientes())

    assert panel.campanias_rentables
    assert panel.segmentos_rentables
    assert panel.insights
    assert all(item.explicacion_humana for item in panel.insights)
