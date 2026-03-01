from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from datetime import datetime, timezone

from clinicdesk.app.application.ports.recordatorios_citas_port import (
    DatosRecordatorioCitaDTO,
    EstadoRecordatorioDTO,
    RecordatorioPreviewDTO,
    RecordatoriosCitasPort,
)
from clinicdesk.app.bootstrap_logging import get_logger


LOGGER = get_logger(__name__)
CANALES_VALIDOS = {"WHATSAPP", "EMAIL", "LLAMADA"}
ESTADOS_VALIDOS = {"PREPARADO", "ENVIADO"}


@dataclass(slots=True)
class PrepararRecordatorioCita:
    recordatorios: RecordatoriosCitasPort

    def ejecutar(self, cita_id: int, canal: str, traductor: Callable[[str], str]) -> RecordatorioPreviewDTO:
        canal_normalizado = _validar_canal(canal)
        datos = self.recordatorios.obtener_datos_recordatorio_cita(cita_id)
        if datos is None:
            return RecordatorioPreviewDTO(
                canal=canal_normalizado,
                mensaje="",
                advertencias=(traductor("recordatorio.error.no_encontrada"),),
                puede_copiar=False,
            )
        advertencias = _advertencias_contacto(traductor, canal_normalizado, datos)
        puede_copiar = len(advertencias) == 0
        mensaje = _mensaje_por_canal(traductor, canal_normalizado, datos) if puede_copiar else ""
        return RecordatorioPreviewDTO(canal=canal_normalizado, mensaje=mensaje, advertencias=advertencias, puede_copiar=puede_copiar)


@dataclass(slots=True)
class RegistrarRecordatorioCita:
    recordatorios: RecordatoriosCitasPort

    def ejecutar(self, cita_id: int, canal: str, estado: str = "PREPARADO") -> None:
        canal_normalizado = _validar_canal(canal)
        estado_normalizado = _validar_estado(estado)
        now_utc = datetime.now(timezone.utc).isoformat()
        self.recordatorios.upsert_recordatorio_cita(cita_id, canal_normalizado, estado_normalizado, now_utc)
        LOGGER.info(
            "recordatorio_actualizado",
            extra={"action": "recordatorio", "cita_id": cita_id, "canal": canal_normalizado, "estado": estado_normalizado},
        )


@dataclass(slots=True)
class ObtenerEstadoRecordatorioCita:
    recordatorios: RecordatoriosCitasPort

    def ejecutar(self, cita_id: int) -> tuple[EstadoRecordatorioDTO, ...]:
        return self.recordatorios.obtener_estado_recordatorio(cita_id)


def _validar_canal(canal: str) -> str:
    valor = canal.upper().strip()
    if valor not in CANALES_VALIDOS:
        raise ValueError(f"Canal inválido: {canal}")
    return valor


def _validar_estado(estado: str) -> str:
    valor = estado.upper().strip()
    if valor not in ESTADOS_VALIDOS:
        raise ValueError(f"Estado inválido: {estado}")
    return valor


def _advertencias_contacto(traductor: Callable[[str], str], canal: str, datos: DatosRecordatorioCitaDTO) -> tuple[str, ...]:
    if canal in {"WHATSAPP", "LLAMADA"} and not datos.telefono:
        return (traductor("recordatorio.advertencia.falta_telefono"),)
    if canal == "EMAIL" and not datos.email:
        return (traductor("recordatorio.advertencia.falta_email"),)
    return tuple()


def _mensaje_por_canal(traductor: Callable[[str], str], canal: str, datos: DatosRecordatorioCitaDTO) -> str:
    dt = datetime.fromisoformat(datos.inicio)
    fecha = dt.strftime("%Y-%m-%d")
    hora = dt.strftime("%H:%M")
    medico = datos.medico_nombre or traductor("recordatorio.medico.no_disponible")
    return traductor(f"recordatorio.plantilla.{canal.lower()}").format(
        paciente=datos.paciente_nombre,
        fecha=fecha,
        hora=hora,
        clinica=traductor("recordatorio.clinica.por_defecto"),
        medico=medico,
    )
