from __future__ import annotations

from clinicdesk.app.domain.prediccion_operativa import CitaOperativa, RegistroOperativo
from clinicdesk.app.infrastructure.prediccion_operativa.almacenamiento_modelo import AlmacenamientoModeloOperativo
from clinicdesk.app.infrastructure.prediccion_operativa.predictor_baseline import PredictorOperativoBaseline


def _dataset(n: int, medico: int, tipo: str, base: float) -> list[RegistroOperativo]:
    return [RegistroOperativo(medico, tipo, None, None, base + (i % 9)) for i in range(n)]


def test_entrenamiento_fallback_global_para_claves_con_pocos_datos(tmp_path):
    predictor = PredictorOperativoBaseline()
    modelo = predictor.entrenar(_dataset(29, 1, "PRIMERA_VISITA", 20) + _dataset(40, 2, "CONTROL", 10))
    assert (1, "PRIMERA_VISITA", None, None) not in modelo.por_clave
    assert (2, "CONTROL", None, None) in modelo.por_clave


def test_prediccion_devuelve_tres_niveles_en_franjas():
    predictor = PredictorOperativoBaseline()
    modelo = predictor.entrenar(_dataset(60, 9, "CONTROL", 10))
    citas = [
        CitaOperativa(1, 9, "CONTROL", "08-12", 1),
        CitaOperativa(2, 9, "CONTROL", "12-16", 1),
        CitaOperativa(3, 9, "CONTROL", "16-20", 1),
    ]
    niveles = [x.nivel.value for x in modelo.predecir(citas)]
    assert niveles == ["BAJO", "MEDIO", "ALTO"]


def test_persistencia_modelo_y_metadata(tmp_path):
    predictor = PredictorOperativoBaseline()
    modelo = predictor.entrenar(_dataset(50, 1, "CONTROL", 12))
    store = AlmacenamientoModeloOperativo("prediccion_duracion", base_dir=tmp_path)
    metadata = store.guardar_con_ventana(
        modelo, n_ejemplos=50, desde="2026-01-01 00:00:00", hasta="2026-02-01 00:00:00", version="v1"
    )
    loaded, loaded_meta = store.cargar()
    assert loaded_meta.n_ejemplos == 50
    assert loaded_meta.version_esquema == "v1"
    assert metadata.fecha_entrenamiento == loaded_meta.fecha_entrenamiento
    assert hasattr(loaded, "predecir")
