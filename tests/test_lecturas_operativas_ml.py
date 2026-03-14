from __future__ import annotations

from clinicdesk.app.application.ml.drift import DriftReport
from clinicdesk.app.application.ml.lecturas_operativas_ml import (
    SemaforoLecturaML,
    construir_lectura_operativa_drift,
    construir_lectura_operativa_exportacion,
    construir_lectura_operativa_metricas,
    construir_lectura_operativa_scoring,
)


def test_scoring_sin_datos_marca_rojo_y_baja_confianza() -> None:
    lectura = construir_lectura_operativa_scoring(total=0, riesgo_alto=0)
    assert lectura.semaforo is SemaforoLecturaML.ROJO
    assert lectura.nivel_confianza == "baja"
    assert lectura.lectura_origen == "scoring"


def test_scoring_con_muestra_pequena_marca_amarillo() -> None:
    lectura = construir_lectura_operativa_scoring(total=10, riesgo_alto=2)
    assert lectura.semaforo is SemaforoLecturaML.AMARILLO
    assert lectura.nivel_confianza == "baja"


def test_drift_sin_reporte_no_concluye_fuerte() -> None:
    lectura = construir_lectura_operativa_drift(None)
    assert lectura.semaforo is SemaforoLecturaML.AMARILLO
    assert "no_concluir" in lectura.cuando_no_concluir_fuerte.clave


def test_drift_con_psi_alto_marca_rojo() -> None:
    report = DriftReport(
        from_version="v1",
        to_version="v2",
        total_from=10,
        total_to=10,
        feature_shifts={"duracion_bucket": {"30-45": 0.3}},
        psi_by_feature={"duracion_bucket": 0.25},
        overall_flag=True,
    )
    lectura = construir_lectura_operativa_drift(report)
    assert lectura.semaforo is SemaforoLecturaML.ROJO
    assert lectura.accion_sugerida.urgencia == "alta"


def test_metricas_debiles_marca_rojo() -> None:
    lectura = construir_lectura_operativa_metricas(accuracy=0.51, precision=0.60, recall=0.56, test_row_count=80)
    assert lectura.semaforo is SemaforoLecturaML.ROJO


def test_metricas_con_poca_muestra_marca_amarillo() -> None:
    lectura = construir_lectura_operativa_metricas(accuracy=0.9, precision=0.9, recall=0.9, test_row_count=20)
    assert lectura.semaforo is SemaforoLecturaML.AMARILLO
    assert lectura.nivel_confianza == "baja"


def test_exportacion_disponible_marca_verde() -> None:
    lectura = construir_lectura_operativa_exportacion(export_count=4)
    assert lectura.semaforo is SemaforoLecturaML.VERDE
    assert lectura.accion_sugerida.clave_accion == "compartir_bi"
