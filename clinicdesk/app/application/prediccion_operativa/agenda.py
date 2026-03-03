from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.prediccion_operativa.usecases import PrevisualizarPrediccionOperativa

NO_DISPONIBLE = "NO_DISPONIBLE"


@dataclass(frozen=True, slots=True)
class ObtenerEstimacionesAgenda:
    previsualizar_duracion_uc: PrevisualizarPrediccionOperativa
    previsualizar_espera_uc: PrevisualizarPrediccionOperativa

    def ejecutar(self) -> tuple[dict[int, str], dict[int, str]]:
        duraciones = {k: v.nivel for k, v in self.previsualizar_duracion_uc.ejecutar().items()}
        esperas = {k: v.nivel for k, v in self.previsualizar_espera_uc.ejecutar().items()}
        return duraciones, esperas
