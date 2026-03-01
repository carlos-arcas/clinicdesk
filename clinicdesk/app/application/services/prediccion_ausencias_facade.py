from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.prediccion_ausencias.riesgo_agenda import (
    ObtenerRiesgoAusenciaParaCitas,
)
from clinicdesk.app.application.prediccion_ausencias.usecases import (
    ComprobarDatosPrediccionAusencias,
    EntrenarPrediccionAusencias,
    PrevisualizarPrediccionAusencias,
    ObtenerExplicacionRiesgoAusenciaCita,
)


@dataclass(slots=True)
class PrediccionAusenciasFacade:
    comprobar_datos_uc: ComprobarDatosPrediccionAusencias
    entrenar_uc: EntrenarPrediccionAusencias
    previsualizar_uc: PrevisualizarPrediccionAusencias
    obtener_riesgo_agenda_uc: ObtenerRiesgoAusenciaParaCitas
    obtener_explicacion_riesgo_uc: ObtenerExplicacionRiesgoAusenciaCita
