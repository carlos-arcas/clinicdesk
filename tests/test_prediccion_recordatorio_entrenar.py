from __future__ import annotations

from datetime import date

from clinicdesk.app.application.prediccion_ausencias.preferencias_recordatorio_entrenar import (
    calcular_fecha_recordatorio,
    debe_mostrar_recordatorio,
    deserializar_fecha_recordatorio_iso,
    serializar_fecha_recordatorio_iso,
)


def test_debe_mostrar_recordatorio_estado_verde_no_muestra() -> None:
    assert debe_mostrar_recordatorio(date(2026, 1, 1), "VERDE", None) is False


def test_debe_mostrar_recordatorio_primer_aviso_si_salud_no_es_verde() -> None:
    assert debe_mostrar_recordatorio(date(2026, 1, 1), "AMARILLO", None) is True
    assert debe_mostrar_recordatorio(date(2026, 1, 1), "ROJO", None) is True


def test_debe_mostrar_recordatorio_con_fecha_futura_no_muestra() -> None:
    assert debe_mostrar_recordatorio(date(2026, 1, 1), "ROJO", date(2026, 1, 8)) is False


def test_debe_mostrar_recordatorio_con_fecha_hoy_o_pasada_muestra() -> None:
    assert debe_mostrar_recordatorio(date(2026, 1, 8), "ROJO", date(2026, 1, 8)) is True
    assert debe_mostrar_recordatorio(date(2026, 1, 9), "ROJO", date(2026, 1, 8)) is True


def test_calcular_fecha_recordatorio_suma_siete_dias() -> None:
    assert calcular_fecha_recordatorio(date(2026, 1, 1), 7) == date(2026, 1, 8)


def test_serializacion_fecha_recordatorio_iso() -> None:
    fecha = date(2026, 1, 8)
    assert serializar_fecha_recordatorio_iso(fecha) == "2026-01-08"
    assert deserializar_fecha_recordatorio_iso("2026-01-08") == fecha
