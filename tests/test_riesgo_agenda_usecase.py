from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.prediccion_ausencias.dtos import CitaParaPrediccionDTO
from clinicdesk.app.application.prediccion_ausencias.riesgo_agenda import (
    ObtenerRiesgoAusenciaParaCitas,
    RIESGO_NO_DISPONIBLE,
)
from clinicdesk.app.domain.prediccion_ausencias import NivelRiesgo, PrediccionAusencia
from clinicdesk.app.infrastructure.prediccion_ausencias import ModeloPrediccionNoDisponibleError


@dataclass
class _FakePredictorEntrenado:
    def predecir(self, citas):
        return [
            PrediccionAusencia(cita_id=citas[0].cita_id, riesgo=NivelRiesgo.BAJO, explicacion_corta=""),
            PrediccionAusencia(cita_id=citas[1].cita_id, riesgo=NivelRiesgo.MEDIO, explicacion_corta=""),
            PrediccionAusencia(cita_id=citas[2].cita_id, riesgo=NivelRiesgo.ALTO, explicacion_corta=""),
        ]


class _FakeAlmacenamiento:
    def __init__(self, predictor=None, fail=False) -> None:
        self._predictor = predictor
        self._fail = fail
        self.cargas = 0

    def cargar(self):
        self.cargas += 1
        if self._fail:
            raise ModeloPrediccionNoDisponibleError()
        return self._predictor, None


def _citas() -> list[CitaParaPrediccionDTO]:
    return [
        CitaParaPrediccionDTO(id=1, fecha="2025-01-01", hora="09:00:00", paciente_id=10, medico_id=100, antelacion_dias=5),
        CitaParaPrediccionDTO(id=2, fecha="2025-01-01", hora="10:00:00", paciente_id=11, medico_id=100, antelacion_dias=5),
        CitaParaPrediccionDTO(id=3, fecha="2025-01-01", hora="11:00:00", paciente_id=12, medico_id=101, antelacion_dias=5),
    ]


def test_obtener_riesgo_agenda_con_predictor() -> None:
    almacenamiento = _FakeAlmacenamiento(predictor=_FakePredictorEntrenado())
    uc = ObtenerRiesgoAusenciaParaCitas(almacenamiento=almacenamiento)

    riesgos = uc.ejecutar(_citas())

    assert riesgos == {1: "BAJO", 2: "MEDIO", 3: "ALTO"}


def test_obtener_riesgo_agenda_sin_predictor_devuelve_no_disponible() -> None:
    almacenamiento = _FakeAlmacenamiento(fail=True)
    uc = ObtenerRiesgoAusenciaParaCitas(almacenamiento=almacenamiento)

    riesgos = uc.ejecutar(_citas())

    assert riesgos == {1: RIESGO_NO_DISPONIBLE, 2: RIESGO_NO_DISPONIBLE, 3: RIESGO_NO_DISPONIBLE}


def test_obtener_riesgo_agenda_cachea_carga_de_predictor() -> None:
    almacenamiento = _FakeAlmacenamiento(predictor=_FakePredictorEntrenado())
    uc = ObtenerRiesgoAusenciaParaCitas(almacenamiento=almacenamiento)

    uc.ejecutar(_citas())
    uc.ejecutar(_citas())

    assert almacenamiento.cargas == 1
