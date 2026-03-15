from datetime import UTC, date, datetime, timedelta

from clinicdesk.app.application.seguros import (
    AnalizarMigracionSeguroUseCase,
    CatalogoPlanesSeguro,
    ColaTrabajoSeguroService,
    GestionComercialSeguroService,
    RecomendadorProductoSeguroService,
    ScoringComercialSeguroService,
    SolicitudGestionItemColaSeguro,
    SolicitudNuevaOportunidadSeguro,
)
from clinicdesk.app.domain.seguros import (
    AccionPendienteSeguro,
    EstadoOperativoSeguro,
    EstadoOportunidadSeguro,
    FriccionMigracionSeguro,
    MotivacionCompraSeguro,
    NecesidadPrincipalSeguro,
    ObjecionComercialSeguro,
    OrigenClienteSeguro,
    PrioridadTrabajoSeguro,
    ResultadoComercialSeguro,
    SegmentoClienteSeguro,
    SensibilidadPrecioSeguro,
)
from clinicdesk.app.domain.seguros.comercial import RenovacionSeguro, ResultadoRenovacionSeguro
from clinicdesk.app.infrastructure.seguros.repositorio_comercial_memoria import RepositorioComercialSeguroMemoria


def _contexto() -> tuple[GestionComercialSeguroService, ColaTrabajoSeguroService, RepositorioComercialSeguroMemoria]:
    repo = RepositorioComercialSeguroMemoria()
    gestion = GestionComercialSeguroService(AnalizarMigracionSeguroUseCase(CatalogoPlanesSeguro()), repo)
    scoring = ScoringComercialSeguroService(repo, minimo_muestras=2)
    recomendador = RecomendadorProductoSeguroService(CatalogoPlanesSeguro(), scoring)
    cola = ColaTrabajoSeguroService(repo, scoring, recomendador)
    return gestion, cola, repo


def _abrir(gestion: GestionComercialSeguroService, id_oportunidad: str) -> None:
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
            sensibilidad_precio=SensibilidadPrecioSeguro.MEDIA,
            friccion_migracion=FriccionMigracionSeguro.MEDIA,
            plan_origen_id="externo_basico",
            plan_destino_id="clinica_esencial",
        )
    )


def test_cola_operativa_prioriza_renovacion_vencida_y_explica_motivo() -> None:
    gestion, cola, repo = _contexto()
    _abrir(gestion, "opp-ren")
    gestion.preparar_oferta("opp-ren", ("prioridad",))
    gestion.registrar_seguimiento(
        "opp-ren",
        EstadoOportunidadSeguro.OFERTA_ENVIADA,
        "contacto",
        "cliente receptivo",
        "cierre",
    )
    gestion.cerrar_oportunidad("opp-ren", ResultadoComercialSeguro.CONVERTIDO)
    repo.guardar_renovacion(
        RenovacionSeguro(
            id_renovacion="ren-opp-ren",
            id_oportunidad="opp-ren",
            plan_vigente_id="clinica_esencial",
            fecha_renovacion=date.today() - timedelta(days=3),
            revision_pendiente=True,
            resultado=ResultadoRenovacionSeguro.PENDIENTE,
        )
    )

    trabajo = cola.construir_cola_diaria(ahora=datetime.now(UTC))

    assert trabajo.items
    assert trabajo.items[0].id_oportunidad == "opp-ren"
    assert trabajo.items[0].prioridad in {PrioridadTrabajoSeguro.MUY_PRIORITARIA, PrioridadTrabajoSeguro.PRIORITARIA}
    assert "vencido" in trabajo.items[0].motivo_principal


def test_registrar_gestion_actualiza_estado_y_permite_reanudacion() -> None:
    gestion, cola, _ = _contexto()
    _abrir(gestion, "opp-1")

    resultado = cola.registrar_gestion(
        SolicitudGestionItemColaSeguro(
            id_oportunidad="opp-1",
            accion=AccionPendienteSeguro.PENDIENTE_DOCUMENTACION,
            nota_corta="falta poliza",
            siguiente_paso="solicitar adjunto",
        )
    )
    trabajo = cola.construir_cola_diaria(ahora=datetime.now(UTC))

    assert resultado.estado_operativo is EstadoOperativoSeguro.PENDIENTE_DOCUMENTACION
    item = next(item for item in trabajo.items if item.id_oportunidad == "opp-1")
    assert item.estado_operativo is EstadoOperativoSeguro.PENDIENTE_DOCUMENTACION
    assert item.ultima_gestion is not None
    assert item.ultima_gestion.siguiente_paso == "solicitar adjunto"


def test_filtros_cola_operativa() -> None:
    gestion, cola, _ = _contexto()
    _abrir(gestion, "opp-a")
    _abrir(gestion, "opp-b")
    cola.registrar_gestion(SolicitudGestionItemColaSeguro("opp-a", AccionPendienteSeguro.RESUELTO))

    trabajo = cola.construir_cola_diaria(ahora=datetime.now(UTC))

    assert trabajo.filtrar_por_estado(EstadoOperativoSeguro.RESUELTO)
    assert all(
        item.estado_operativo is EstadoOperativoSeguro.RESUELTO
        for item in trabajo.filtrar_por_estado(EstadoOperativoSeguro.RESUELTO)
    )
