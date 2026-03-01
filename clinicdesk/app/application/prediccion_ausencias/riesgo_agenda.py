from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from clinicdesk.app.application.prediccion_ausencias.dtos import CitaParaPrediccionDTO
from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.domain.prediccion_ausencias import CitaParaPrediccion, PredictorEntrenado
from clinicdesk.app.infrastructure.prediccion_ausencias import (
    AlmacenamientoModeloPrediccion,
    ModeloPrediccionNoDisponibleError,
)

LOGGER = get_logger(__name__)
RIESGO_NO_DISPONIBLE = "NO_DISPONIBLE"


@dataclass(slots=True)
class ObtenerRiesgoAusenciaParaCitas:
    almacenamiento: AlmacenamientoModeloPrediccion
    _predictor_cache: PredictorEntrenado | None = None
    _predictor_intentado: bool = False

    def ejecutar(self, citas: Sequence[CitaParaPrediccionDTO]) -> dict[int, str]:
        if not citas:
            return {}
        predictor = self._obtener_predictor()
        if predictor is None:
            return self._resultado_no_disponible(citas)

        predicciones = predictor.predecir(self._mapear_citas(citas))
        riesgo_por_cita = {item.cita_id: item.riesgo.value for item in predicciones}
        return {cita.id: riesgo_por_cita.get(cita.id, RIESGO_NO_DISPONIBLE) for cita in citas}

    def _obtener_predictor(self) -> PredictorEntrenado | None:
        if self._predictor_cache is not None:
            return self._predictor_cache
        if self._predictor_intentado:
            return None
        self._predictor_intentado = True

        try:
            predictor, _ = self.almacenamiento.cargar()
            self._predictor_cache = predictor
            return predictor
        except ModeloPrediccionNoDisponibleError:
            LOGGER.info(
                "prediccion_agenda_no_disponible",
                extra={"reason_code": "predictor_missing"},
            )
        except Exception as exc:  # noqa: BLE001
            LOGGER.error(
                "prediccion_agenda_no_disponible",
                extra={"reason_code": "predictor_load_failed", "error": str(exc)},
            )
        return None

    @staticmethod
    def _resultado_no_disponible(citas: Sequence[CitaParaPrediccionDTO]) -> dict[int, str]:
        return {cita.id: RIESGO_NO_DISPONIBLE for cita in citas}

    @staticmethod
    def _mapear_citas(citas: Sequence[CitaParaPrediccionDTO]) -> list[CitaParaPrediccion]:
        return [
            CitaParaPrediccion(
                cita_id=cita.id,
                paciente_id=cita.paciente_id,
                dias_antelacion=cita.antelacion_dias,
            )
            for cita in citas
        ]
