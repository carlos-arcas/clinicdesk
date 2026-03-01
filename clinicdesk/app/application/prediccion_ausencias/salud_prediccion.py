from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

from clinicdesk.app.application.prediccion_ausencias.dtos import SaludPrediccionDTO
from clinicdesk.app.bootstrap_logging import get_logger

LOGGER = get_logger(__name__)


class LectorMetadataPrediccionPort(Protocol):
    def cargar_metadata(self) -> object | None: ...


class ConteoCitasValidasRecientesPort(Protocol):
    def contar_citas_validas_recientes(self, dias: int = 90) -> int: ...


@dataclass(frozen=True, slots=True)
class ObtenerSaludPrediccionAusencias:
    lector_metadata: LectorMetadataPrediccionPort
    queries: ConteoCitasValidasRecientesPort
    dias_ventana_citas: int = 90

    def ejecutar(self) -> SaludPrediccionDTO:
        metadata = self.lector_metadata.cargar_metadata()
        fecha_entrenamiento = self._extraer_fecha(metadata)
        citas_recientes = self.queries.contar_citas_validas_recientes(self.dias_ventana_citas)
        estado = _resolver_estado(fecha_entrenamiento=fecha_entrenamiento, citas_validas_recientes=citas_recientes)
        return SaludPrediccionDTO(
            estado=estado,
            mensaje_i18n_key=f"prediccion_ausencias.salud.mensaje.{estado.lower()}",
            acciones_i18n_keys=_resolver_acciones(estado),
            fecha_ultima_actualizacion=fecha_entrenamiento,
            citas_validas_recientes=citas_recientes,
        )

    def _extraer_fecha(self, metadata: object | None) -> str | None:
        if metadata is None:
            return None
        fecha_entrenamiento = getattr(metadata, "fecha_entrenamiento", None)
        if isinstance(fecha_entrenamiento, str):
            return fecha_entrenamiento
        LOGGER.warning(
            "prediccion_salud_metadata_invalida",
            extra={"reason_code": "invalid_training_date", "metadata_type": type(metadata).__name__},
        )
        return None


def _resolver_estado(*, fecha_entrenamiento: str | None, citas_validas_recientes: int) -> str:
    if fecha_entrenamiento is None:
        return "ROJO"
    dias_desde_entrenamiento = _dias_desde_entrenamiento(fecha_entrenamiento)
    if dias_desde_entrenamiento is None:
        return "ROJO"
    if dias_desde_entrenamiento > 45 or citas_validas_recientes < 20:
        return "ROJO"
    if dias_desde_entrenamiento <= 14 and citas_validas_recientes >= 50:
        return "VERDE"
    if 15 <= dias_desde_entrenamiento <= 45 or 20 <= citas_validas_recientes <= 49:
        return "AMARILLO"
    return "ROJO"


def _dias_desde_entrenamiento(fecha_entrenamiento: str) -> int | None:
    try:
        fecha = datetime.fromisoformat(fecha_entrenamiento)
    except ValueError:
        LOGGER.warning(
            "prediccion_salud_fecha_invalida",
            extra={"reason_code": "invalid_iso_date", "fecha_entrenamiento": fecha_entrenamiento},
        )
        return None
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    ahora = datetime.now(timezone.utc)
    if fecha > ahora:
        return 0
    return int((ahora - fecha).total_seconds() // timedelta(days=1).total_seconds())


def _resolver_acciones(estado: str) -> tuple[str, ...]:
    if estado == "VERDE":
        return tuple()
    return ("prediccion_ausencias.accion.entrenar",)
