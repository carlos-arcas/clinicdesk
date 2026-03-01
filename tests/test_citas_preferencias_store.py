from __future__ import annotations

from clinicdesk.app.pages.citas.preferencias_citas import PreferenciasCitasStore
from clinicdesk.app.pages.citas.filtros_citas_estado import FiltrosCitasEstado


class _FakeSettings:
    _data: dict[str, object] = {}

    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def value(self, key: str, default=None):
        return self._data.get(key, default)

    def setValue(self, key: str, value) -> None:  # noqa: N802
        self._data[key] = value


def test_preferencias_citas_persisten_por_usuario(monkeypatch) -> None:
    monkeypatch.setattr("clinicdesk.app.pages.citas.preferencias_citas.QSettings", _FakeSettings)

    _FakeSettings._data.clear()
    store_a = PreferenciasCitasStore("ana")
    store_b = PreferenciasCitasStore("bob")
    filtros = FiltrosCitasEstado(desde="2025-01-01", hasta="2025-01-31", texto="control", estado="PROGRAMADA")

    store_a.guardar_filtros(filtros)
    store_a.guardar_columnas(["fecha", "paciente"])

    assert store_a.cargar().filtros == filtros
    assert store_a.cargar().columnas == ["fecha", "paciente"]
    assert store_b.cargar().filtros.texto == ""


def test_preferencias_citas_columnas_default(monkeypatch) -> None:
    monkeypatch.setattr("clinicdesk.app.pages.citas.preferencias_citas.QSettings", _FakeSettings)
    _FakeSettings._data.clear()

    store = PreferenciasCitasStore("ana")
    columnas = store.cargar().columnas

    assert "fecha" in columnas
    assert "paciente" in columnas
