from datetime import datetime

from clinicdesk.app.application.historial_paciente.filtros import FiltrosHistorialPacienteDTO
from clinicdesk.app.pages.pacientes.dialogs.widgets.persistencia_historial_settings import (
    EstadoPersistidoFiltros,
    deserializar_filtros,
    sanear_columnas_guardadas,
    serializar_columnas,
    serializar_filtros,
)


def test_serializar_y_deserializar_filtros() -> None:
    dto = FiltrosHistorialPacienteDTO(
        paciente_id=7,
        rango_preset="PERSONALIZADO",
        desde=datetime(2025, 1, 1, 10, 0),
        hasta=datetime(2025, 1, 5, 18, 0),
        texto="abc",
        estados=("REALIZADA",),
    )
    persisted = serializar_filtros(dto)
    restored = deserializar_filtros(7, persisted)
    assert restored.rango_preset == "PERSONALIZADO"
    assert restored.desde == dto.desde
    assert restored.hasta == dto.hasta
    assert restored.texto == "abc"
    assert restored.estados == ("REALIZADA",)


def test_deserializar_filtros_tolera_fecha_invalida() -> None:
    restored = deserializar_filtros(1, EstadoPersistidoFiltros("30_DIAS", "bad", None, None, None))
    assert restored.desde is None


def test_saneado_columnas() -> None:
    assert sanear_columnas_guardadas("fecha,estado,fecha,") == ("fecha", "estado")
    assert serializar_columnas(("fecha", "estado")) == "fecha,estado"
