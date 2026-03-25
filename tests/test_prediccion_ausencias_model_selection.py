from __future__ import annotations

from clinicdesk.app.application.prediccion_ausencias.seleccion_modelo import (
    ResultadoMetricasModelo,
    seleccionar_mejor_modelo,
)
from clinicdesk.app.domain.prediccion_ausencias import CitaParaPrediccion, NivelRiesgo, RegistroEntrenamiento
from clinicdesk.app.infrastructure.prediccion_ausencias.predictor_v2 import (
    PredictorAusenciasV2,
    _bucket_antelacion,
    _mezclar_probabilidades,
)


def test_selector_prefiere_mejor_f1() -> None:
    seleccion = seleccionar_mejor_modelo(
        baseline=ResultadoMetricasModelo(
            model_type="PredictorAusenciasBaseline", accuracy=0.7, recall_no_show=0.5, f1_no_show=0.58
        ),
        candidato_v2=ResultadoMetricasModelo(
            model_type="PredictorAusenciasV2", accuracy=0.68, recall_no_show=0.6, f1_no_show=0.6
        ),
    )

    assert seleccion.ganador.model_type == "PredictorAusenciasV2"


def test_selector_empate_prefiere_baseline_por_estabilidad() -> None:
    seleccion = seleccionar_mejor_modelo(
        baseline=ResultadoMetricasModelo(
            model_type="PredictorAusenciasBaseline", accuracy=0.7, recall_no_show=0.6, f1_no_show=0.59
        ),
        candidato_v2=ResultadoMetricasModelo(
            model_type="PredictorAusenciasV2", accuracy=0.7, recall_no_show=0.6, f1_no_show=0.59
        ),
    )

    assert seleccion.ganador.model_type == "PredictorAusenciasBaseline"


def test_predictor_v2_entrena_y_predice_con_bucket_y_soporte() -> None:
    dataset = [
        RegistroEntrenamiento(paciente_id=1, no_vino=1, dias_antelacion=0),
        RegistroEntrenamiento(paciente_id=1, no_vino=1, dias_antelacion=1),
        RegistroEntrenamiento(paciente_id=1, no_vino=1, dias_antelacion=2),
        RegistroEntrenamiento(paciente_id=2, no_vino=0, dias_antelacion=20),
        RegistroEntrenamiento(paciente_id=2, no_vino=0, dias_antelacion=18),
        RegistroEntrenamiento(paciente_id=3, no_vino=0, dias_antelacion=10),
    ]
    predictor = PredictorAusenciasV2().entrenar(dataset)

    predicciones = predictor.predecir(
        [
            CitaParaPrediccion(cita_id=101, paciente_id=1, dias_antelacion=1),
            CitaParaPrediccion(cita_id=102, paciente_id=2, dias_antelacion=20),
        ]
    )

    assert predicciones[0].riesgo in {NivelRiesgo.MEDIO, NivelRiesgo.ALTO}
    assert predicciones[1].riesgo in {NivelRiesgo.BAJO, NivelRiesgo.MEDIO}
    assert "jerárquico" in predicciones[0].explicacion_corta.lower()


def test_predictor_v2_bucket_y_mezcla_determinista() -> None:
    assert _bucket_antelacion(0) == "MISMO_DIA"
    assert _bucket_antelacion(2) == "CORTA"
    assert _bucket_antelacion(6) == "MEDIA"
    assert _bucket_antelacion(11) == "LARGA"
    assert _bucket_antelacion(22) == "MUY_LARGA"

    baja_confianza = _mezclar_probabilidades(
        prob_global=0.3,
        prob_paciente=0.8,
        soporte_paciente=1,
        prob_bucket=0.7,
        soporte_bucket=1,
    )
    alta_confianza = _mezclar_probabilidades(
        prob_global=0.3,
        prob_paciente=0.8,
        soporte_paciente=20,
        prob_bucket=0.7,
        soporte_bucket=20,
    )

    assert 0.0 <= baja_confianza <= 1.0
    assert 0.0 <= alta_confianza <= 1.0
    assert alta_confianza > baja_confianza
