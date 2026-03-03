from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from clinicdesk.app.application.prediccion_operativa.agenda import ObtenerEstimacionesAgenda
from clinicdesk.app.application.prediccion_operativa.usecases import (
    ComprobarDatosPrediccionOperativa,
    EntrenarPrediccionOperativa,
    ListarProximasCitasOperativas,
    ObtenerExplicacionPrediccionOperativa,
    ObtenerSaludPrediccionOperativa,
    PrevisualizarPrediccionOperativa,
)


@dataclass(slots=True)
class PrediccionOperativaFacade:
    comprobar_duracion_uc: ComprobarDatosPrediccionOperativa
    entrenar_duracion_uc: EntrenarPrediccionOperativa
    previsualizar_duracion_uc: PrevisualizarPrediccionOperativa
    salud_duracion_uc: ObtenerSaludPrediccionOperativa
    explicar_duracion_uc: ObtenerExplicacionPrediccionOperativa
    comprobar_espera_uc: ComprobarDatosPrediccionOperativa
    entrenar_espera_uc: EntrenarPrediccionOperativa
    previsualizar_espera_uc: PrevisualizarPrediccionOperativa
    salud_espera_uc: ObtenerSaludPrediccionOperativa
    explicar_espera_uc: ObtenerExplicacionPrediccionOperativa
    agenda_uc: ObtenerEstimacionesAgenda
    listar_proximas_citas_uc: ListarProximasCitasOperativas
    cerrar_conexion_hilo_actual: Callable[[], None] | None = None
