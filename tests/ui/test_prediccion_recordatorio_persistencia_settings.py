from __future__ import annotations

from datetime import date

from clinicdesk.app.application.prediccion_ausencias.preferencias_recordatorio_entrenar import (
    PreferenciaRecordatorioEntrenarDTO,
)
from clinicdesk.app.pages.prediccion_ausencias.persistencia_recordatorio_entrenar_settings import (
    guardar_preferencia_recordatorio_entrenar,
    leer_preferencia_recordatorio_entrenar,
)


class _SettingsFake:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def value(self, key: str, defaultValue: str = "") -> str:  # noqa: N803
        return self._store.get(key, defaultValue)

    def setValue(self, key: str, value: str) -> None:  # noqa: N803
        self._store[key] = value


def test_persistencia_recordatorio_serializa_y_deserializa_iso() -> None:
    settings = _SettingsFake()
    preferencia = PreferenciaRecordatorioEntrenarDTO(
        fecha_recordatorio_utc=date(2026, 1, 8),
        dias_snooze=7,
    )

    guardar_preferencia_recordatorio_entrenar(settings, preferencia)
    restaurada = leer_preferencia_recordatorio_entrenar(settings)

    assert restaurada.fecha_recordatorio_utc == date(2026, 1, 8)
    assert restaurada.dias_snooze == 7
