from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.infrastructure.sqlite.proveedor_conexion_sqlite import ProveedorConexionSqlitePorHilo

from clinicdesk.app.application.prediccion_ausencias.riesgo_agenda import (
    ObtenerRiesgoAusenciaParaCitas,
)
from clinicdesk.app.application.prediccion_ausencias.cierre_citas_usecases import (
    CerrarCitasPendientes,
    ListarCitasPendientesCierre,
)
from clinicdesk.app.application.prediccion_ausencias.usecases import (
    ComprobarDatosPrediccionAusencias,
    EntrenarPrediccionAusencias,
    ObtenerExplicacionRiesgoAusenciaCita,
    PrevisualizarPrediccionAusencias,
)
from clinicdesk.app.application.prediccion_ausencias.salud_prediccion import ObtenerSaludPrediccionAusencias
from clinicdesk.app.application.prediccion_ausencias.resultados_recientes import (
    ObtenerResultadosRecientesPrediccionAusencias,
    RegistrarPrediccionesAusenciasAgenda,
)


@dataclass(slots=True)
class PrediccionAusenciasFacade:
    proveedor_conexion: ProveedorConexionSqlitePorHilo
    comprobar_datos_uc: ComprobarDatosPrediccionAusencias
    entrenar_uc: EntrenarPrediccionAusencias
    previsualizar_uc: PrevisualizarPrediccionAusencias
    obtener_riesgo_agenda_uc: ObtenerRiesgoAusenciaParaCitas
    obtener_explicacion_riesgo_uc: ObtenerExplicacionRiesgoAusenciaCita
    obtener_salud_uc: ObtenerSaludPrediccionAusencias
    registrar_predicciones_agenda_uc: RegistrarPrediccionesAusenciasAgenda
    obtener_resultados_recientes_uc: ObtenerResultadosRecientesPrediccionAusencias
    listar_citas_pendientes_cierre_uc: ListarCitasPendientesCierre
    cerrar_citas_pendientes_uc: CerrarCitasPendientes
