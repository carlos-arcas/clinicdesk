from __future__ import annotations

import pytest

from tests.support.ruta_critica_desktop import seed_historial_y_agenda_prediccion

pytestmark = [pytest.mark.integration]


def test_facade_prediccion_operativa_cubre_pipeline_minimo(container, seed_data) -> None:
    cita_futura_id = seed_historial_y_agenda_prediccion(container, seed_data)
    facade = container.prediccion_operativa_facade

    comprobacion = facade.comprobar_duracion_uc.ejecutar()
    entrenamiento = facade.entrenar_duracion_uc.ejecutar()
    predicciones = facade.previsualizar_duracion_uc.ejecutar(30)
    salud = facade.obtener_salud_duracion()
    cita_id_explicable, prediccion = next(iter(predicciones.items()))
    explicacion = facade.obtener_explicacion_duracion(cita_id_explicable, prediccion.nivel)

    assert comprobacion.apto_para_entrenar is True
    assert entrenamiento.ejemplos_usados >= 50
    assert predicciones
    assert predicciones[cita_futura_id].nivel in {"BAJO", "MEDIO", "ALTO"}
    assert salud.estado in {"VERDE", "AMARILLO"}
    assert explicacion.motivos_i18n_keys
    assert explicacion.acciones_i18n_keys
    assert explicacion.necesita_entrenar is False
