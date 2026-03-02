from datetime import datetime

from clinicdesk.app.application.citas import FiltrosCitasDTO
from clinicdesk.app.pages.citas.widgets.persistencia_citas_settings import (
    EstadoPersistidoFiltrosCitas,
    deserializar_columnas_citas,
    deserializar_filtros_citas,
    estado_restauracion_columnas,
    serializar_columnas_citas,
    serializar_filtros_citas,
)


def test_serializar_deserializar_filtros_citas() -> None:
    dto = FiltrosCitasDTO(
        rango_preset="PERSONALIZADO",
        desde=datetime(2025, 2, 1, 0, 0, 0),
        hasta=datetime(2025, 2, 2, 23, 59, 59),
        texto_busqueda=" ana ",
        estado_cita="CONFIRMADA",
    )
    data = serializar_filtros_citas(dto)
    restored = deserializar_filtros_citas(data)
    assert restored.rango_preset == "PERSONALIZADO"
    assert restored.desde == dto.desde
    assert restored.hasta == dto.hasta
    assert restored.texto_busqueda == "ana"


def test_deserializar_filtros_citas_tolera_fechas_invalidas() -> None:
    restored = deserializar_filtros_citas(
        EstadoPersistidoFiltrosCitas("PERSONALIZADO", "bad", "bad", None, None, None, None, None)
    )
    assert restored.desde is None
    assert restored.hasta is None


def test_saneo_columnas_citas() -> None:
    assert "cita_id" in deserializar_columnas_citas("foo,foo")
    assert serializar_columnas_citas(("fecha", "estado")) == "fecha,estado"
    assert estado_restauracion_columnas("foo,foo") is True
