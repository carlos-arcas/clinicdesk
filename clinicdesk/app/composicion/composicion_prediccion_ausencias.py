from __future__ import annotations

from clinicdesk.app.application.prediccion_ausencias.cierre_citas_usecases import (
    CerrarCitasPendientes,
    ListarCitasPendientesCierre,
)
from clinicdesk.app.application.prediccion_ausencias.resultados_recientes import (
    ObtenerResultadosRecientesPrediccionAusencias,
    RegistrarPrediccionesAusenciasAgenda,
)
from clinicdesk.app.application.prediccion_ausencias.riesgo_agenda import ObtenerRiesgoAusenciaParaCitas
from clinicdesk.app.application.prediccion_ausencias.salud_prediccion import ObtenerSaludPrediccionAusencias
from clinicdesk.app.application.prediccion_ausencias.usecases import (
    ComprobarDatosPrediccionAusencias,
    EntrenarPrediccionAusencias,
    ObtenerExplicacionRiesgoAusenciaCita,
    ObtenerResumenUltimoEntrenamientoPrediccion,
    PrevisualizarPrediccionAusencias,
)
from clinicdesk.app.application.services.prediccion_ausencias_facade import PrediccionAusenciasFacade
from clinicdesk.app.infrastructure.prediccion_ausencias import (
    AlmacenamientoModeloPrediccion,
    PredictorAusenciasBaseline,
)
from clinicdesk.app.infrastructure.sqlite.proveedor_conexion_sqlite import ProveedorConexionSqlitePorHilo
from clinicdesk.app.queries.prediccion_ausencias_queries import PrediccionAusenciasQueries
from clinicdesk.app.queries.prediccion_ausencias_resultados_queries import PrediccionAusenciasResultadosQueries


def build_prediccion_ausencias_facade(
    proveedor_conexion: ProveedorConexionSqlitePorHilo,
) -> PrediccionAusenciasFacade:
    queries = PrediccionAusenciasQueries(proveedor_conexion)
    resultados_queries = PrediccionAusenciasResultadosQueries(proveedor_conexion)
    almacenamiento = AlmacenamientoModeloPrediccion()
    comprobar_uc = ComprobarDatosPrediccionAusencias(queries, minimo_requerido=50)
    entrenar_uc = EntrenarPrediccionAusencias(
        comprobar_datos_uc=comprobar_uc,
        queries=queries,
        predictor=PredictorAusenciasBaseline(),
        almacenamiento=almacenamiento,
    )
    return PrediccionAusenciasFacade(
        proveedor_conexion=proveedor_conexion,
        comprobar_datos_uc=comprobar_uc,
        entrenar_uc=entrenar_uc,
        previsualizar_uc=PrevisualizarPrediccionAusencias(queries, almacenamiento),
        obtener_riesgo_agenda_uc=ObtenerRiesgoAusenciaParaCitas(almacenamiento),
        obtener_explicacion_riesgo_uc=ObtenerExplicacionRiesgoAusenciaCita(queries, almacenamiento),
        obtener_resumen_ultimo_entrenamiento_uc=ObtenerResumenUltimoEntrenamientoPrediccion(almacenamiento),
        obtener_salud_uc=ObtenerSaludPrediccionAusencias(lector_metadata=almacenamiento, queries=queries),
        registrar_predicciones_agenda_uc=RegistrarPrediccionesAusenciasAgenda(resultados_queries),
        obtener_resultados_recientes_uc=ObtenerResultadosRecientesPrediccionAusencias(resultados_queries),
        listar_citas_pendientes_cierre_uc=ListarCitasPendientesCierre(queries),
        cerrar_citas_pendientes_uc=CerrarCitasPendientes(queries),
    )
