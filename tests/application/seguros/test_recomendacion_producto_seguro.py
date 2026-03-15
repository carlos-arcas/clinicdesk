from clinicdesk.app.application.seguros import (
    AnalizarMigracionSeguroUseCase,
    CatalogoPlanesSeguro,
    GestionComercialSeguroService,
    RecomendadorProductoSeguroService,
    ScoringComercialSeguroService,
    SemaforoRenovacionSeguro,
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


def _crear_contexto() -> tuple[GestionComercialSeguroService, RecomendadorProductoSeguroService]:
    repo = RepositorioComercialSeguroMemoria()
    catalogo = CatalogoPlanesSeguro()
    gestion = GestionComercialSeguroService(AnalizarMigracionSeguroUseCase(catalogo), repo)
    recomendador = RecomendadorProductoSeguroService(
        catalogo, scoring=ScoringComercialSeguroService(repo, minimo_muestras=3)
    )
    return gestion, recomendador


def _abrir(
    gestion: GestionComercialSeguroService,
    id_oportunidad: str,
    sensibilidad: SensibilidadPrecioSeguro,
    objecion: ObjecionComercialSeguro,
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
            objecion_principal=objecion,
            sensibilidad_precio=sensibilidad,
            friccion_migracion=FriccionMigracionSeguro.MEDIA,
            plan_origen_id="externo_plus",
            plan_destino_id="clinica_esencial",
        )
    )


def test_recomienda_plan_con_argumento_accionable() -> None:
    gestion, recomendador = _crear_contexto()
    _abrir(
        gestion,
        "opp-recom",
        SensibilidadPrecioSeguro.MEDIA,
        ObjecionComercialSeguro.MIEDO_CAMBIO,
    )
    oportunidad = gestion.listar_cartera()[0]

    diagnostico = recomendador.evaluar_oportunidad(oportunidad)

    assert diagnostico.recomendacion_plan.plan_recomendado_id == "clinica_esencial"
    assert diagnostico.argumento_comercial.angulo_principal in {"AHORRO_TOTAL", "MIGRACION_FAVORABLE", "COBERTURA_UTIL"}
    assert diagnostico.accion_retencion.accion_sugerida in {"REVISAR_OBJECION_PRECIO", "REVISAR_RENOVACION_PRIORITARIA"}


def test_guardrail_sin_recomendacion_fuerte_con_fit_debil() -> None:
    gestion, recomendador = _crear_contexto()
    _abrir(
        gestion,
        "opp-fit-debil",
        SensibilidadPrecioSeguro.ALTA,
        ObjecionComercialSeguro.PRECIO_PERCIBIDO_ALTO,
    )
    gestion.preparar_oferta("opp-fit-debil", ("ajuste",))
    gestion.registrar_seguimiento(
        "opp-fit-debil",
        EstadoOportunidadSeguro.OFERTA_ENVIADA,
        "llamada_1",
        "cliente duda por precio",
        "revisar",
    )
    gestion.registrar_seguimiento(
        "opp-fit-debil",
        EstadoOportunidadSeguro.EN_SEGUIMIENTO,
        "llamada_2",
        "sin cierre",
        "esperar",
    )
    oportunidad = gestion.cerrar_oportunidad("opp-fit-debil", ResultadoComercialSeguro.RECHAZADO)

    diagnostico = recomendador.evaluar_oportunidad(oportunidad)

    assert diagnostico.recomendacion_plan.plan_recomendado_id is None
    assert diagnostico.riesgo_renovacion.semaforo is SemaforoRenovacionSeguro.ALTO
    assert diagnostico.accion_retencion.accion_sugerida == "REVISAR_RENOVACION_PRIORITARIA"


def test_evidencia_insuficiente_entrega_cautela() -> None:
    gestion, recomendador = _crear_contexto()
    _abrir(
        gestion,
        "opp-insuf",
        SensibilidadPrecioSeguro.MEDIA,
        ObjecionComercialSeguro.DUDAS_COBERTURA,
    )
    oportunidad = gestion.listar_cartera()[0]
    oportunidad_sin_base = oportunidad.__class__(
        id_oportunidad="opp-vacia",
        candidato=oportunidad.candidato,
        plan_origen_id=oportunidad.plan_origen_id,
        plan_destino_id=oportunidad.plan_destino_id,
        estado_actual=oportunidad.estado_actual,
        clasificacion_motor=oportunidad.clasificacion_motor,
        perfil_comercial=None,
        evaluacion_fit=None,
        seguimientos=(),
        resultado_comercial=None,
    )

    diagnostico = recomendador.evaluar_oportunidad(oportunidad_sin_base)

    assert diagnostico.recomendacion_plan.plan_recomendado_id is None
    assert diagnostico.riesgo_renovacion.semaforo is SemaforoRenovacionSeguro.EVIDENCIA_INSUFICIENTE
    assert "suficiente" in diagnostico.accion_retencion.motivo.lower()
