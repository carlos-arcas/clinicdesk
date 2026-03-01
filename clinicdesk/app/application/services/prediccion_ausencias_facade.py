from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.prediccion_ausencias.usecases import (
    ComprobarDatosPrediccionAusencias,
    EntrenarPrediccionAusencias,
    PrevisualizarPrediccionAusencias,
)


@dataclass(slots=True)
class PrediccionAusenciasFacade:
    comprobar_datos_uc: ComprobarDatosPrediccionAusencias
    entrenar_uc: EntrenarPrediccionAusencias
    previsualizar_uc: PrevisualizarPrediccionAusencias
