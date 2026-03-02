from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from clinicdesk.app.application.citas.filtros import FiltrosCitasDTO, normalizar_filtros_citas
from clinicdesk.app.application.citas.usecases import (
    BuscarCitasParaCalendario,
    BuscarCitasParaLista,
    PaginacionCitasDTO,
)


@dataclass
class FakeQueries:
    llamada_listado: int = 0
    llamada_calendario: int = 0
    ultimo_filtro_listado: FiltrosCitasDTO | None = None
    ultimas_columnas_listado: tuple[str, ...] = ()

    def buscar_citas_listado(self, filtros_norm, campos_requeridos, limit, offset):
        self.llamada_listado += 1
        self.ultimo_filtro_listado = filtros_norm
        self.ultimas_columnas_listado = campos_requeridos
        return ([{"cita_id": 10, "fecha": "2025-01-10"}], 1)

    def buscar_citas_calendario(self, filtros_norm, campos_requeridos_tooltip):
        self.llamada_calendario += 1
        return [{"cita_id": 11, "fecha": "2025-01-10"}]


def test_buscar_citas_lista_recibe_filtros_normalizados_y_sanea_columnas() -> None:
    fake = FakeQueries()
    uc = BuscarCitasParaLista(fake)
    ahora = datetime(2025, 1, 10, 9, 0)
    filtros_norm = normalizar_filtros_citas(
        FiltrosCitasDTO(rango_preset="SEMANA", texto_busqueda="  eco  "),
        ahora,
    )

    resultado = uc.ejecutar(
        filtros_norm,
        ("fecha", "desconocida", "fecha"),
        PaginacionCitasDTO(limit=20, offset=0),
    )

    assert resultado.total == 1
    assert fake.llamada_listado == 1
    assert fake.ultimo_filtro_listado is not None
    assert fake.ultimo_filtro_listado.desde == datetime(2025, 1, 10, 0, 0)
    assert fake.ultimo_filtro_listado.hasta == datetime(2025, 1, 16, 23, 59, 59)
    assert fake.ultimas_columnas_listado == ("fecha", "cita_id")


def test_buscar_citas_calendario_usa_una_llamada_por_refresco() -> None:
    fake = FakeQueries()
    uc = BuscarCitasParaCalendario(fake)
    filtros = normalizar_filtros_citas(
        FiltrosCitasDTO(
            rango_preset="PERSONALIZADO",
            desde=datetime(2025, 1, 10, 0, 0),
            hasta=datetime(2025, 1, 10, 23, 59, 59),
        ),
        datetime(2025, 1, 10, 12, 0),
    )

    items = uc.ejecutar(filtros, ("fecha", "paciente"))

    assert len(items) == 1
    assert fake.llamada_calendario == 1
    assert fake.llamada_listado == 0
