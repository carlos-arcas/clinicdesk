from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from clinicdesk.app.application.historial_paciente.filtros import (
    FiltrosHistorialPacienteDTO,
    normalizar_filtros_historial_paciente,
)
from clinicdesk.app.application.historial_paciente.usecases import (
    BuscarHistorialCitasPaciente,
    BuscarHistorialRecetasPaciente,
    ObtenerResumenHistorialPaciente,
    ResumenRaw,
)


@dataclass
class FakeQueries:
    llamadas_citas: int = 0
    llamadas_recetas: int = 0
    llamadas_resumen: int = 0
    ultimo_filtro_citas: FiltrosHistorialPacienteDTO | None = None

    def buscar_historial_citas(self, paciente_id, desde, hasta, texto, estados, limit, offset):
        self.llamadas_citas += 1
        self.ultimo_filtro_citas = FiltrosHistorialPacienteDTO(
            paciente_id=paciente_id,
            desde=desde,
            hasta=hasta,
            texto=texto,
            estados=estados,
            limite=limit,
            offset=offset,
        )
        return ([{"cita_id": 1, "estado": "REALIZADA", "medico": "Dra.", "tiene_incidencias": 0}], 1)

    def buscar_historial_recetas(self, paciente_id, desde, hasta, texto, estados, limit, offset):
        self.llamadas_recetas += 1
        return ([{"receta_id": 2, "estado": "ACTIVA", "medico": "Dr.", "num_lineas": 2, "activa": 1}], 1)

    def obtener_resumen_historial(self, paciente_id, desde, hasta):
        self.llamadas_resumen += 1
        return ResumenRaw(total_citas=4, no_presentados=1, total_recetas=3, recetas_activas=2)


def test_usecase_citas_usa_filtro_normalizado_y_sin_n_mas_uno() -> None:
    fake = FakeQueries()
    uc = BuscarHistorialCitasPaciente(fake)
    filtros_norm = normalizar_filtros_historial_paciente(
        FiltrosHistorialPacienteDTO(paciente_id=10, rango_preset="HOY", texto=" abc "),
        datetime(2026, 1, 10, 12, 0),
    )

    resultado = uc.ejecutar(filtros_norm, columnas=("estado", "medico"))

    assert resultado.total == 1
    assert fake.llamadas_citas == 1
    assert fake.llamadas_recetas == 0
    assert fake.ultimo_filtro_citas is not None
    assert fake.ultimo_filtro_citas.texto == "abc"


def test_usecase_recetas_hace_fallback_columnas_corruptas() -> None:
    fake = FakeQueries()
    uc = BuscarHistorialRecetasPaciente(fake)
    filtros_norm = normalizar_filtros_historial_paciente(
        FiltrosHistorialPacienteDTO(paciente_id=10),
        datetime(2026, 1, 10, 12, 0),
    )

    resultado = uc.ejecutar(filtros_norm, columnas=("x", "y"))

    assert fake.llamadas_recetas == 1
    assert "fecha" in resultado.items[0]
    assert "receta_id" in resultado.items[0]


def test_obtener_resumen_historial_devuelve_kpis() -> None:
    fake = FakeQueries()
    uc = ObtenerResumenHistorialPaciente(fake)

    resumen = uc.ejecutar(paciente_id=10, ventana_dias=90)

    assert fake.llamadas_resumen == 1
    assert resumen.total_citas == 4
    assert resumen.no_presentados == 1
    assert resumen.total_recetas == 3
    assert resumen.recetas_activas == 2
