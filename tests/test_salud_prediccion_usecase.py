from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from clinicdesk.app.application.prediccion_ausencias.salud_prediccion import ObtenerSaludPrediccionAusencias


@dataclass(frozen=True, slots=True)
class _FakeMetadata:
    fecha_entrenamiento: str


class _FakeStorage:
    def __init__(self, metadata: _FakeMetadata | None) -> None:
        self._metadata = metadata

    def cargar_metadata(self) -> _FakeMetadata | None:
        return self._metadata


class _FakeQueries:
    def __init__(self, total: int) -> None:
        self._total = total

    def contar_citas_validas_recientes(self, dias: int = 90) -> int:
        return self._total


def _fecha_hace(dias: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()


def _ejecutar(metadata: _FakeMetadata | None, total: int):
    return ObtenerSaludPrediccionAusencias(_FakeStorage(metadata), _FakeQueries(total)).ejecutar()


def test_salud_sin_metadata_es_rojo() -> None:
    salud = _ejecutar(metadata=None, total=90)

    assert salud.estado == "ROJO"


def test_salud_verde_con_metadata_reciente_y_conteo_alto() -> None:
    salud = _ejecutar(metadata=_FakeMetadata(fecha_entrenamiento=_fecha_hace(10)), total=70)

    assert salud.estado == "VERDE"


def test_salud_amarillo_con_veinte_dias_y_conteo_treinta() -> None:
    salud = _ejecutar(metadata=_FakeMetadata(fecha_entrenamiento=_fecha_hace(20)), total=30)

    assert salud.estado == "AMARILLO"


def test_salud_rojo_con_sesenta_dias_y_conteo_alto() -> None:
    salud = _ejecutar(metadata=_FakeMetadata(fecha_entrenamiento=_fecha_hace(60)), total=90)

    assert salud.estado == "ROJO"


def test_salud_rojo_con_conteo_muy_bajo_aunque_sea_reciente() -> None:
    salud = _ejecutar(metadata=_FakeMetadata(fecha_entrenamiento=_fecha_hace(1)), total=10)

    assert salud.estado == "ROJO"
