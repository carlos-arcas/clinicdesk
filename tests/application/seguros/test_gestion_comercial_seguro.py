from clinicdesk.app.application.seguros import (
    AnalizarMigracionSeguroUseCase,
    CatalogoPlanesSeguro,
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
from clinicdesk.app.infrastructure.seguros.repositorio_comercial_memoria import RepositorioComercialSeguroMemoria


def _servicio() -> GestionComercialSeguroService:
    analizador = AnalizarMigracionSeguroUseCase(CatalogoPlanesSeguro())
    return GestionComercialSeguroService(analizador, RepositorioComercialSeguroMemoria())


def test_abre_oportunidad_y_prepara_oferta() -> None:
    servicio = _servicio()
    oportunidad = servicio.abrir_oportunidad(
        SolicitudNuevaOportunidadSeguro(
            "opp-1",
            "cand-1",
            "pac-1",
            SegmentoClienteSeguro.ASEGURADO_EXTERNO_MIGRAR,
            OrigenClienteSeguro.WEB,
            NecesidadPrincipalSeguro.AHORRO_COSTE,
            (MotivacionCompraSeguro.MEJOR_RELACION_CALIDAD_PRECIO,),
            ObjecionComercialSeguro.PRECIO_PERCIBIDO_ALTO,
            SensibilidadPrecioSeguro.MEDIA,
            FriccionMigracionSeguro.MEDIA,
            "externo_basico",
            "clinica_esencial",
        )
    )

    oferta = servicio.preparar_oferta("opp-1", ("alto interes",))

    assert oportunidad.estado_actual is EstadoOportunidadSeguro.ELEGIBLE
    assert oferta.plan_propuesto_id == "clinica_esencial"
    assert oferta.notas_comerciales == ("alto interes",)


def test_registro_seguimiento_y_cierre_convertido_genera_renovacion() -> None:
    servicio = _servicio()
    servicio.abrir_oportunidad(
        SolicitudNuevaOportunidadSeguro(
            "opp-2",
            "cand-2",
            "pac-2",
            SegmentoClienteSeguro.ASEGURADO_EXTERNO_MIGRAR,
            OrigenClienteSeguro.REFERIDO,
            NecesidadPrincipalSeguro.CONTINUIDAD_MEDICA,
            (MotivacionCompraSeguro.CONFIANZA_EN_CLINICA,),
            ObjecionComercialSeguro.MIEDO_CAMBIO,
            SensibilidadPrecioSeguro.BAJA,
            FriccionMigracionSeguro.BAJA,
            "externo_plus",
            "clinica_integral",
        )
    )
    servicio.preparar_oferta("opp-2", ("seguimiento semanal",))
    oportunidad = servicio.registrar_seguimiento(
        "opp-2",
        EstadoOportunidadSeguro.OFERTA_ENVIADA,
        "contacto_whatsapp",
        "cliente confirma recepcion",
        "llamada 48h",
    )

    cerrada = servicio.cerrar_oportunidad("opp-2", ResultadoComercialSeguro.CONVERTIDO)

    assert oportunidad.estado_actual is EstadoOportunidadSeguro.OFERTA_ENVIADA
    assert cerrada.estado_actual is EstadoOportunidadSeguro.PENDIENTE_RENOVACION
    assert len(servicio.listar_renovaciones_pendientes()) == 1
