from datetime import datetime

from clinicdesk.app.application.citas.navigation_intent import CitasNavigationIntentDTO, debe_abrir_detalle, es_intent_calidad


def test_debe_abrir_detalle_true_cuando_accion_abrir_y_encontrada() -> None:
    intent = CitasNavigationIntentDTO(preset_rango="HOY", cita_id_destino=5, accion="ABRIR_DETALLE")

    assert debe_abrir_detalle(intent, found=True)


def test_debe_abrir_detalle_false_cuando_accion_abrir_y_no_encontrada() -> None:
    intent = CitasNavigationIntentDTO(preset_rango="HOY", cita_id_destino=5, accion="ABRIR_DETALLE")

    assert not debe_abrir_detalle(intent, found=False)


def test_debe_abrir_detalle_false_cuando_accion_seleccionar() -> None:
    intent = CitasNavigationIntentDTO(preset_rango="HOY", cita_id_destino=5, accion="SELECCIONAR")

    assert not debe_abrir_detalle(intent, found=True)


def test_intent_defaults_accion_resaltar_y_duracion() -> None:
    intent = CitasNavigationIntentDTO(preset_rango="HOY", cita_id_destino=7)

    assert intent.accion == "SELECCIONAR"
    assert intent.resaltar is True
    assert intent.duracion_resaltado_ms == 2500


def test_es_intent_calidad_true_con_filtro() -> None:
    intent = CitasNavigationIntentDTO(
        filtro_calidad="SIN_CHECKIN",
        rango_desde=datetime(2025, 1, 1, 0, 0, 0),
        rango_hasta=datetime(2025, 1, 1, 23, 59, 59),
        preferir_pestana="LISTA",
    )

    assert es_intent_calidad(intent) is True


def test_es_intent_calidad_false_sin_filtro() -> None:
    intent = CitasNavigationIntentDTO(preset_rango="HOY", cita_id_destino=7)

    assert es_intent_calidad(intent) is False
