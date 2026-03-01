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
    llamada_lista: int = 0
    llamada_calendario: int = 0
    ultimo_filtro_lista: FiltrosCitasDTO | None = None
    ultimo_filtro_calendario: FiltrosCitasDTO | None = None

    def buscar_para_lista(self, filtros_norm, paginacion, columnas):
        self.llamada_lista += 1
        self.ultimo_filtro_lista = filtros_norm
        return ([{"cita_id": 10, "fecha": "2025-01-10"}], 1)

    def buscar_para_calendario(self, filtros_norm, columnas):
        self.llamada_calendario += 1
        self.ultimo_filtro_calendario = filtros_norm
        return [{"cita_id": 11, "fecha": "2025-01-10"}]


def test_buscar_citas_lista_recibe_filtros_normalizados() -> None:
    fake = FakeQueries()
    uc = BuscarCitasParaLista(fake)
    ahora = datetime(2025, 1, 10, 9, 0)
    filtros_norm = normalizar_filtros_citas(
        FiltrosCitasDTO(rango_preset="SEMANA", texto_busqueda="  eco  "),
        ahora,
    )

    resultado = uc.ejecutar(
        filtros_norm,
        PaginacionCitasDTO(limit=20, offset=0),
        ("fecha", "hora_inicio"),
    )

    assert resultado.total == 1
    assert fake.llamada_lista == 1
    assert fake.ultimo_filtro_lista is not None
    assert fake.ultimo_filtro_lista.desde == datetime(2025, 1, 10, 0, 0)
    assert fake.ultimo_filtro_lista.hasta == datetime(2025, 1, 16, 23, 59, 59)


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

    items = uc.ejecutar(filtros)

    assert len(items) == 1
    assert fake.llamada_calendario == 1
    assert fake.llamada_lista == 0
