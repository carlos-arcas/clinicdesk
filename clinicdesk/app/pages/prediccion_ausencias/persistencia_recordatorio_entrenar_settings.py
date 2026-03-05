from __future__ import annotations

from datetime import date
from typing import Any, Protocol

from clinicdesk.app.application.prediccion_ausencias.preferencias_recordatorio_entrenar import (
    CLAVE_RECORDATORIO_DIAS_SNOOZE,
    CLAVE_RECORDATORIO_FECHA_UTC,
    DIAS_SNOOZE_POR_DEFECTO,
    PreferenciaRecordatorioEntrenarDTO,
    calcular_fecha_recordatorio,
    deserializar_fecha_recordatorio_iso,
    normalizar_dias_snooze,
    serializar_fecha_recordatorio_iso,
)


class ProtocoloSettings(Protocol):
    def value(self, key: str, defaultValue: Any = None) -> Any: ...  # noqa: N803

    def setValue(self, key: str, value: Any) -> None: ...  # noqa: N803


def claves_recordatorio_entrenar() -> dict[str, str]:
    return {
        "fecha_recordatorio_utc": CLAVE_RECORDATORIO_FECHA_UTC,
        "dias_snooze": CLAVE_RECORDATORIO_DIAS_SNOOZE,
    }


def leer_preferencia_recordatorio_entrenar(settings: ProtocoloSettings) -> PreferenciaRecordatorioEntrenarDTO:
    claves = claves_recordatorio_entrenar()
    fecha_recordatorio = deserializar_fecha_recordatorio_iso(settings.value(claves["fecha_recordatorio_utc"], ""))
    dias_snooze = normalizar_dias_snooze(settings.value(claves["dias_snooze"], DIAS_SNOOZE_POR_DEFECTO))
    return PreferenciaRecordatorioEntrenarDTO(
        fecha_recordatorio_utc=fecha_recordatorio,
        dias_snooze=dias_snooze,
    )


def guardar_preferencia_recordatorio_entrenar(
    settings: ProtocoloSettings,
    preferencia: PreferenciaRecordatorioEntrenarDTO,
) -> None:
    claves = claves_recordatorio_entrenar()
    settings.setValue(
        claves["fecha_recordatorio_utc"], serializar_fecha_recordatorio_iso(preferencia.fecha_recordatorio_utc)
    )
    settings.setValue(claves["dias_snooze"], str(normalizar_dias_snooze(preferencia.dias_snooze)))


def posponer_recordatorio_entrenar(
    settings: ProtocoloSettings,
    hoy_utc: date,
    dias_snooze: int = DIAS_SNOOZE_POR_DEFECTO,
) -> PreferenciaRecordatorioEntrenarDTO:
    preferencia = PreferenciaRecordatorioEntrenarDTO(
        fecha_recordatorio_utc=calcular_fecha_recordatorio(hoy_utc, dias_snooze),
        dias_snooze=normalizar_dias_snooze(dias_snooze),
    )
    guardar_preferencia_recordatorio_entrenar(settings, preferencia)
    return preferencia


def limpiar_recordatorio_entrenar(settings: ProtocoloSettings, dias_snooze: int = DIAS_SNOOZE_POR_DEFECTO) -> None:
    guardar_preferencia_recordatorio_entrenar(
        settings,
        PreferenciaRecordatorioEntrenarDTO(
            fecha_recordatorio_utc=None,
            dias_snooze=normalizar_dias_snooze(dias_snooze),
        ),
    )
