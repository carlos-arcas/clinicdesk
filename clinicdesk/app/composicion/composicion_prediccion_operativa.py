from __future__ import annotations

from clinicdesk.app.application.prediccion_operativa.agenda import ObtenerEstimacionesAgenda
from clinicdesk.app.application.prediccion_operativa.usecases import (
    ComprobarDatosPrediccionOperativa,
    EntrenarPrediccionOperativa,
    ListarProximasCitasOperativas,
    ObtenerExplicacionPrediccionOperativa,
    ObtenerSaludPrediccionOperativa,
    PrevisualizarPrediccionOperativa,
)
from clinicdesk.app.application.services.prediccion_operativa_facade import PrediccionOperativaFacade
from clinicdesk.app.infrastructure.prediccion_operativa import AlmacenamientoModeloOperativo, PredictorOperativoBaseline
from clinicdesk.app.infrastructure.sqlite.proveedor_conexion_sqlite import ProveedorConexionSqlitePorHilo
from clinicdesk.app.queries.prediccion_operativa_queries import PrediccionOperativaQueries


def build_prediccion_operativa_facade(
    proveedor_conexion: ProveedorConexionSqlitePorHilo,
) -> PrediccionOperativaFacade:
    queries = PrediccionOperativaQueries(proveedor_conexion)
    predictor = PredictorOperativoBaseline()
    almacenamiento_duracion = AlmacenamientoModeloOperativo("prediccion_duracion")
    almacenamiento_espera = AlmacenamientoModeloOperativo("prediccion_espera")
    previsualizar_duracion_uc = PrevisualizarPrediccionOperativa(queries, almacenamiento_duracion)
    previsualizar_espera_uc = PrevisualizarPrediccionOperativa(queries, almacenamiento_espera)
    return PrediccionOperativaFacade(
        comprobar_duracion_uc=ComprobarDatosPrediccionOperativa(queries, "duracion"),
        entrenar_duracion_uc=EntrenarPrediccionOperativa(queries, predictor, almacenamiento_duracion, "duracion"),
        previsualizar_duracion_uc=previsualizar_duracion_uc,
        salud_duracion_uc=ObtenerSaludPrediccionOperativa(queries, almacenamiento_duracion, "duracion"),
        explicar_duracion_uc=ObtenerExplicacionPrediccionOperativa(almacenamiento_duracion),
        comprobar_espera_uc=ComprobarDatosPrediccionOperativa(queries, "espera"),
        entrenar_espera_uc=EntrenarPrediccionOperativa(queries, predictor, almacenamiento_espera, "espera"),
        previsualizar_espera_uc=previsualizar_espera_uc,
        salud_espera_uc=ObtenerSaludPrediccionOperativa(queries, almacenamiento_espera, "espera"),
        explicar_espera_uc=ObtenerExplicacionPrediccionOperativa(almacenamiento_espera),
        agenda_uc=ObtenerEstimacionesAgenda(previsualizar_duracion_uc, previsualizar_espera_uc),
        listar_proximas_citas_uc=ListarProximasCitasOperativas(queries),
        cerrar_conexion_hilo_actual=proveedor_conexion.cerrar_conexion_del_hilo_actual,
    )
