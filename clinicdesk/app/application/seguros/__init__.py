from clinicdesk.app.application.seguros.fit_comercial import MotorFitComercialSeguro, SolicitudFitComercialSeguro
from clinicdesk.app.application.seguros.catalogo_planes import CatalogoPlanesSeguro
from clinicdesk.app.application.seguros.scoring_comercial import (
    AccionComercialSugerida,
    BandaPropensionSeguro,
    CarteraPriorizadaSeguro,
    NivelPrioridadComercialSeguro,
    PrediccionComercialSeguro,
    PrioridadOportunidadSeguro,
    ScoringComercialSeguroService,
    SemaforoComercialSeguro,
)
from clinicdesk.app.application.seguros.recomendacion_producto import (
    AccionRetencionSeguro,
    ArgumentoComercialSeguro,
    DiagnosticoComercialSeguro,
    MotivoRecomendacionPlan,
    RecomendacionPlanSeguro,
    RecomendadorProductoSeguroService,
    RiesgoRenovacionSeguro,
    SemaforoRenovacionSeguro,
)
from clinicdesk.app.application.seguros.cola_trabajo import (
    ColaTrabajoSeguroService,
    SolicitudGestionItemColaSeguro,
)
from clinicdesk.app.application.seguros.comercial import (
    FiltroCarteraSeguro,
    GestionComercialSeguroService,
    SolicitudNuevaOportunidadSeguro,
)
from clinicdesk.app.application.seguros.usecases import (
    AnalizarMigracionSeguroUseCase,
    RespuestaAnalisisMigracionSeguro,
    SolicitudAnalisisMigracionSeguro,
)
from clinicdesk.app.application.seguros.campanias import (
    GestionCampaniasSeguroService,
    SolicitudCrearCampaniaSeguro,
    SolicitudCrearCampaniaDesdeSugerencia,
    SolicitudGestionItemCampaniaSeguro,
)
from clinicdesk.app.application.seguros.analitica_ejecutiva import (
    AnaliticaEjecutivaSegurosService,
    CampaniaAccionableSeguro,
    CohorteSeguro,
    EstadoEmbudoSeguro,
    GrupoRenovacionSeguro,
    InsightComercialSeguro,
    MetricaFunnelSeguro,
    ResumenEjecutivoSeguros,
)

__all__ = [
    "CatalogoPlanesSeguro",
    "AnalizarMigracionSeguroUseCase",
    "SolicitudAnalisisMigracionSeguro",
    "RespuestaAnalisisMigracionSeguro",
    "GestionComercialSeguroService",
    "SolicitudNuevaOportunidadSeguro",
    "FiltroCarteraSeguro",
    "ColaTrabajoSeguroService",
    "SolicitudGestionItemColaSeguro",
    "MotorFitComercialSeguro",
    "SolicitudFitComercialSeguro",
    "ScoringComercialSeguroService",
    "PrediccionComercialSeguro",
    "PrioridadOportunidadSeguro",
    "AccionComercialSugerida",
    "SemaforoComercialSeguro",
    "NivelPrioridadComercialSeguro",
    "BandaPropensionSeguro",
    "CarteraPriorizadaSeguro",
    "RecomendadorProductoSeguroService",
    "RecomendacionPlanSeguro",
    "RiesgoRenovacionSeguro",
    "SemaforoRenovacionSeguro",
    "MotivoRecomendacionPlan",
    "ArgumentoComercialSeguro",
    "AccionRetencionSeguro",
    "DiagnosticoComercialSeguro",
    "AnaliticaEjecutivaSegurosService",
    "ResumenEjecutivoSeguros",
    "CohorteSeguro",
    "MetricaFunnelSeguro",
    "EstadoEmbudoSeguro",
    "CampaniaAccionableSeguro",
    "GrupoRenovacionSeguro",
    "InsightComercialSeguro",
    "GestionCampaniasSeguroService",
    "SolicitudCrearCampaniaSeguro",
    "SolicitudCrearCampaniaDesdeSugerencia",
    "SolicitudGestionItemCampaniaSeguro",
]
