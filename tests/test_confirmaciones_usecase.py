from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.confirmaciones.dtos import FiltrosConfirmacionesDTO
from clinicdesk.app.application.confirmaciones.usecases import (
    ObtenerConfirmacionesCitas,
    PaginacionConfirmacionesDTO,
)
from clinicdesk.app.application.prediccion_ausencias.dtos import SaludPrediccionDTO
from clinicdesk.app.queries.confirmaciones_queries import CitaConfirmacionRow


@dataclass
class FakeQueries:
    items: list[CitaConfirmacionRow]

    def buscar_citas_confirmaciones(self, filtros, limit, offset):
        _ = filtros
        return self.items[offset : offset + limit], len(self.items)


class FakeRiesgo:
    def __init__(self, riesgos: dict[int, str]) -> None:
        self.riesgos = riesgos
        self.calls = 0

    def ejecutar(self, citas):
        self.calls += 1
        return {cita.id: self.riesgos.get(cita.id, "NO_DISPONIBLE") for cita in citas}


class FakeSalud:
    def __init__(self) -> None:
        self.calls = 0

    def ejecutar(self) -> SaludPrediccionDTO:
        self.calls += 1
        return SaludPrediccionDTO(
            estado="AMARILLO",
            mensaje_i18n_key="x",
            acciones_i18n_keys=tuple(),
            fecha_ultima_actualizacion=None,
            citas_validas_recientes=10,
        )


def test_obtener_confirmaciones_mapea_filtra_y_ejecuta_en_lote() -> None:
    rows = [
        CitaConfirmacionRow(1, "2030-01-01T09:00:00", "A", "M", "PENDIENTE", 11, 21, "SIN_PREPARAR"),
        CitaConfirmacionRow(2, "2030-01-02T09:00:00", "B", "M", "PENDIENTE", 12, 21, "PREPARADO"),
        CitaConfirmacionRow(3, "2030-01-03T09:00:00", "C", "M", "PENDIENTE", 13, 21, "ENVIADO"),
    ]
    riesgo = FakeRiesgo({1: "ALTO", 2: "MEDIO", 3: "BAJO"})
    salud = FakeSalud()
    uc = ObtenerConfirmacionesCitas(FakeQueries(rows), riesgo, salud)

    result = uc.ejecutar(
        FiltrosConfirmacionesDTO(
            desde="2030-01-01",
            hasta="2030-01-31",
            riesgo_filtro="ALTO_MEDIO",
        ),
        PaginacionConfirmacionesDTO(limit=10, offset=0),
    )

    assert [item.cita_id for item in result.items] == [1, 2]
    assert result.total == 3
    assert result.mostrados == 2
    assert riesgo.calls == 1
    assert salud.calls == 1

    alto = uc.ejecutar(
        FiltrosConfirmacionesDTO(
            desde="2030-01-01",
            hasta="2030-01-31",
            riesgo_filtro="SOLO_ALTO",
        ),
        PaginacionConfirmacionesDTO(limit=10, offset=0),
    )
    assert [item.cita_id for item in alto.items] == [1]
