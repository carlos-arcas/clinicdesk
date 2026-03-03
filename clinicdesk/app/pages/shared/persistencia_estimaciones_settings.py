from __future__ import annotations

from PySide6.QtCore import QSettings

CLAVE_MOSTRAR_ESTIMACIONES_AGENDA = "prediccion_operativa/mostrar_estimaciones_agenda"


def guardar_mostrar_estimaciones_agenda(valor: bool, settings: QSettings | None = None) -> None:
    qsettings = settings or QSettings()
    qsettings.setValue(CLAVE_MOSTRAR_ESTIMACIONES_AGENDA, 1 if valor else 0)


def leer_mostrar_estimaciones_agenda(settings: QSettings | None = None) -> bool:
    qsettings = settings or QSettings()
    return bool(int(qsettings.value(CLAVE_MOSTRAR_ESTIMACIONES_AGENDA, 0)))
