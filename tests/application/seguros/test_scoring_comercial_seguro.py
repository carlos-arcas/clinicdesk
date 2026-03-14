from clinicdesk.app.application.seguros import (
    AnalizarMigracionSeguroUseCase,
    CatalogoPlanesSeguro,
    GestionComercialSeguroService,
    NivelPrioridadComercialSeguro,
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


def _crear_servicios() -> tuple[GestionComercialSeguroService, ScoringComercialSeguroService]:
    repo = RepositorioComercialSeguroMemoria()
    gestion = GestionComercialSeguroService(AnalizarMigracionSeguroUseCase(CatalogoPlanesSeguro()), repo)
    scoring = ScoringComercialSeguroService(repo, minimo_muestras=3)
    return gestion, scoring


def _abrir_oportunidad(
    gestion: GestionComercialSeguroService,
    id_oportunidad: str,
    sensibilidad: SensibilidadPrecioSeguro,
    friccion: FriccionMigracionSeguro,
    objecion: ObjecionComercialSeguro,
) -> None:
    gestion.abrir_oportunidad(
        SolicitudNuevaOportunidadSeguro(
            id_oportunidad,
            f"cand-{id_oportunidad}",
            f"pac-{id_oportunidad}",
            SegmentoClienteSeguro.ASEGURADO_EXTERNO_MIGRAR,
            OrigenClienteSeguro.WEB,
            NecesidadPrincipalSeguro.AHORRO_COSTE,
            (MotivacionCompraSeguro.MEJOR_RELACION_CALIDAD_PRECIO,),
            objecion,
            sensibilidad,
            friccion,
            "externo_basico",
            "clinica_esencial",
        )
    )


def test_dataset_comercial_es_reproducible_y_sin_pii() -> None:
    gestion, scoring = _crear_servicios()
    _abrir_oportunidad(
        gestion,
        "opp-a",
        SensibilidadPrecioSeguro.MEDIA,
        FriccionMigracionSeguro.MEDIA,
        ObjecionComercialSeguro.PRECIO_PERCIBIDO_ALTO,
    )

    dataset = scoring.construir_dataset()

    assert len(dataset) == 1
    assert dataset[0].id_oportunidad == "opp-a"
    assert dataset[0].segmento_cliente == "ASEGURADO_EXTERNO_MIGRAR"
    assert not hasattr(dataset[0], "id_paciente")


def test_priorizacion_comercial_ordena_cartera_y_define_acciones() -> None:
    gestion, scoring = _crear_servicios()
    _abrir_oportunidad(
        gestion,
        "opp-top",
        SensibilidadPrecioSeguro.BAJA,
        FriccionMigracionSeguro.BAJA,
        ObjecionComercialSeguro.MIEDO_CAMBIO,
    )
    _abrir_oportunidad(
        gestion,
        "opp-mid",
        SensibilidadPrecioSeguro.MEDIA,
        FriccionMigracionSeguro.MEDIA,
        ObjecionComercialSeguro.PRECIO_PERCIBIDO_ALTO,
    )
    _abrir_oportunidad(
        gestion,
        "opp-low",
        SensibilidadPrecioSeguro.ALTA,
        FriccionMigracionSeguro.ALTA,
        ObjecionComercialSeguro.PRECIO_PERCIBIDO_ALTO,
    )
    gestion.preparar_oferta("opp-top", ("prioridad",))
    gestion.registrar_seguimiento(
        "opp-top",
        EstadoOportunidadSeguro.OFERTA_ENVIADA,
        "presentacion",
        "cliente interesado",
        "cierre",
    )
    gestion.preparar_oferta("opp-low", ("ajuste",))
    gestion.registrar_seguimiento(
        "opp-low",
        EstadoOportunidadSeguro.OFERTA_ENVIADA,
        "seguimiento_1",
        "respuesta debil",
        "esperar",
    )
    gestion.registrar_seguimiento(
        "opp-low",
        EstadoOportunidadSeguro.EN_SEGUIMIENTO,
        "seguimiento_2",
        "sin avance",
        "esperar",
    )
    gestion.cerrar_oportunidad("opp-top", ResultadoComercialSeguro.CONVERTIDO)

    cartera = scoring.priorizar_cartera(gestion.listar_cartera())

    assert cartera.oportunidad_mas_caliente is not None
    assert cartera.oportunidad_mas_caliente.id_oportunidad in {"opp-top", "opp-mid", "opp-low"}
    assert cartera.oportunidades[0].score_prioridad >= cartera.oportunidades[-1].score_prioridad
    assert cartera.oportunidades[0].accion_sugerida.value


def test_guardrail_muestra_cautela_con_base_insuficiente() -> None:
    gestion, scoring = _crear_servicios()
    _abrir_oportunidad(
        gestion,
        "opp-guardrail",
        SensibilidadPrecioSeguro.MEDIA,
        FriccionMigracionSeguro.MEDIA,
        ObjecionComercialSeguro.PRECIO_PERCIBIDO_ALTO,
    )

    cartera = scoring.priorizar_cartera(gestion.listar_cartera())

    assert cartera.oportunidades[0].confianza_relativa < 0.35
    assert "insuficiente" in cartera.oportunidades[0].cautela_limite.lower()
    assert cartera.oportunidades[0].prioridad in {
        NivelPrioridadComercialSeguro.MEDIA,
        NivelPrioridadComercialSeguro.BAJA,
    }


def test_interpretacion_humana_es_accionable_y_prudente() -> None:
    gestion, scoring = _crear_servicios()
    _abrir_oportunidad(
        gestion,
        "opp-int",
        SensibilidadPrecioSeguro.BAJA,
        FriccionMigracionSeguro.BAJA,
        ObjecionComercialSeguro.MIEDO_CAMBIO,
    )

    cartera = scoring.priorizar_cartera(gestion.listar_cartera())
    lectura = scoring.interpretar(cartera.oportunidades[0])

    assert "orden" in lectura.utilidad_practica.lower()
    assert "orientacion" in lectura.cautela.lower()
    assert lectura.accion_humana_recomendada
