from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from clinicdesk.app.application.seguros import (
    AnaliticaEjecutivaSegurosService,
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


@dataclass
class _FechaFija:
    fecha: date

    def hoy(self) -> date:
        return self.fecha


def _servicios() -> tuple[GestionComercialSeguroService, RepositorioComercialSeguroMemoria]:
    repositorio = RepositorioComercialSeguroMemoria()
    analizador = AnalizarMigracionSeguroUseCase(CatalogoPlanesSeguro())
    return GestionComercialSeguroService(analizador, repositorio), repositorio


def _abrir(
    servicio: GestionComercialSeguroService, id_oportunidad: str, sensibilidad: SensibilidadPrecioSeguro
) -> None:
    servicio.abrir_oportunidad(
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


def test_construye_resumen_ejecutivo_con_cohortes_y_campanias() -> None:
    servicio, _ = _servicios()
    _abrir(servicio, "opp-1", SensibilidadPrecioSeguro.ALTA)
    _abrir(servicio, "opp-2", SensibilidadPrecioSeguro.ALTA)
    _abrir(servicio, "opp-3", SensibilidadPrecioSeguro.MEDIA)
    servicio.preparar_oferta("opp-1", ("n1",))
    servicio.preparar_oferta("opp-2", ("n2",))
    servicio.preparar_oferta("opp-3", ("n3",))
    servicio.registrar_seguimiento(
        "opp-1",
        EstadoOportunidadSeguro.OFERTA_ENVIADA,
        "llamada",
        "interesado",
        "cerrar",
    )
    servicio.registrar_seguimiento(
        "opp-3",
        EstadoOportunidadSeguro.OFERTA_ENVIADA,
        "envio",
        "acepta",
        "cierre",
    )
    servicio.cerrar_oportunidad("opp-3", ResultadoComercialSeguro.CONVERTIDO)

    analitica = AnaliticaEjecutivaSegurosService(servicio, proveedor_fecha=_FechaFija(date(2026, 3, 15)))
    resumen = analitica.construir_resumen()

    assert resumen.total_oportunidades == 3
    assert resumen.convertidas == 1
    assert resumen.ratio_conversion_global == 0.3333
    assert any(item.dimension == "objecion" for item in resumen.cohortes)
    assert any(item.id_campania == "campania_precio_argumento" for item in resumen.campanias)


def test_guardrail_ratio_nulo_cuando_muestra_insuficiente() -> None:
    servicio, _ = _servicios()
    _abrir(servicio, "opp-x", SensibilidadPrecioSeguro.BAJA)

    analitica = AnaliticaEjecutivaSegurosService(servicio, proveedor_fecha=_FechaFija(date(2026, 3, 15)))
    resumen = analitica.construir_resumen()

    assert resumen.ratio_conversion_global is None
    metrica_convertidas = next(item for item in resumen.metrica_funnel if item.clave == "convertidas")
    assert metrica_convertidas.ratio is None


def test_campania_renovacion_riesgo_identifica_ids() -> None:
    servicio, repo = _servicios()
    _abrir(servicio, "opp-r1", SensibilidadPrecioSeguro.MEDIA)
    servicio.preparar_oferta("opp-r1", ("n",))
    servicio.registrar_seguimiento(
        "opp-r1",
        EstadoOportunidadSeguro.OFERTA_ENVIADA,
        "envio",
        "ok",
        "cierre",
    )
    servicio.cerrar_oportunidad("opp-r1", ResultadoComercialSeguro.CONVERTIDO)
    renovacion = repo.listar_renovaciones_pendientes()[0]
    repo.guardar_renovacion(
        renovacion.__class__(
            id_renovacion=renovacion.id_renovacion,
            id_oportunidad=renovacion.id_oportunidad,
            plan_vigente_id=renovacion.plan_vigente_id,
            fecha_renovacion=date(2026, 3, 20),
            revision_pendiente=True,
            resultado=renovacion.resultado,
        )
    )

    analitica = AnaliticaEjecutivaSegurosService(servicio, proveedor_fecha=_FechaFija(date(2026, 3, 15)))
    ids = analitica.ids_oportunidad_por_campania("campania_renovacion_riesgo")

    assert ids == ("opp-r1",)
