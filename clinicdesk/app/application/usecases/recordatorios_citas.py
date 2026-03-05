from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from datetime import datetime, timezone

from clinicdesk.app.application.recordatorios.puertos import (
    DatosRecordatorioCitaDTO,
    EstadoRecordatorioDTO,
    RecordatorioPreviewDTO,
    GatewayRecordatoriosCitas,
)
from clinicdesk.app.bootstrap_logging import get_logger


LOGGER = get_logger(__name__)
CANALES_VALIDOS = {"WHATSAPP", "EMAIL", "LLAMADA"}
ESTADOS_VALIDOS = {"PREPARADO", "ENVIADO"}


@dataclass(slots=True)
class PrepararRecordatorioCita:
    recordatorios: GatewayRecordatoriosCitas

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
        return RecordatorioPreviewDTO(
            canal=canal_normalizado, mensaje=mensaje, advertencias=advertencias, puede_copiar=puede_copiar
        )


@dataclass(slots=True)
class RegistrarRecordatorioCita:
    recordatorios: GatewayRecordatoriosCitas

    def ejecutar(self, cita_id: int, canal: str, estado: str = "PREPARADO") -> None:
        canal_normalizado = _validar_canal(canal)
        estado_normalizado = _validar_estado(estado)
        now_utc = datetime.now(timezone.utc).isoformat()
        self.recordatorios.upsert_recordatorio_cita(cita_id, canal_normalizado, estado_normalizado, now_utc)
        LOGGER.info(
            "recordatorio_actualizado",
            extra={
                "action": "recordatorio",
                "cita_id": cita_id,
                "canal": canal_normalizado,
                "estado": estado_normalizado,
            },
        )


@dataclass(slots=True)
class ObtenerEstadoRecordatorioCita:
    recordatorios: GatewayRecordatoriosCitas

    def ejecutar(self, cita_id: int) -> tuple[EstadoRecordatorioDTO, ...]:
        return self.recordatorios.obtener_estado_recordatorio(cita_id)


@dataclass(frozen=True, slots=True)
class DetalleOmitidaDTO:
    motivo_code: str


@dataclass(frozen=True, slots=True)
class ResultadoLoteRecordatoriosDTO:
    preparadas: int = 0
    enviadas: int = 0
    omitidas_sin_contacto: int = 0
    omitidas_ya_enviado: int = 0
    errores: int = 0


@dataclass(slots=True)
class PrepararRecordatoriosEnLote:
    recordatorios: GatewayRecordatoriosCitas

    def ejecutar(self, cita_ids: tuple[int, ...], canal: str) -> ResultadoLoteRecordatoriosDTO:
        canal_normalizado = _validar_canal_lote(canal)
        if not cita_ids:
            return ResultadoLoteRecordatoriosDTO()
        contactos = self.recordatorios.obtener_contacto_citas(cita_ids)
        estados = self.recordatorios.obtener_estado_recordatorio_lote(cita_ids)
        now_utc = datetime.now(timezone.utc).isoformat()
        resultado = _contabilizar_preparacion(cita_ids, canal_normalizado, contactos, estados, now_utc)
        if resultado.dto.preparadas > 0:
            self.recordatorios.upsert_recordatorios_lote(resultado.items_upsert)
        _log_lote("confirmaciones_lote_preparar", canal_normalizado, len(cita_ids), resultado.dto)
        return resultado.dto


@dataclass(slots=True)
class MarcarRecordatoriosEnviadosEnLote:
    recordatorios: GatewayRecordatoriosCitas

    def ejecutar(self, cita_ids: tuple[int, ...], canal: str | None = None) -> ResultadoLoteRecordatoriosDTO:
        if not cita_ids:
            return ResultadoLoteRecordatoriosDTO()
        canales = (_validar_canal_lote(canal),) if canal else ("WHATSAPP", "EMAIL")
        now_utc = datetime.now(timezone.utc).isoformat()
        items = [(cita_id, canal_item, "ENVIADO", now_utc) for cita_id in cita_ids for canal_item in canales]
        if items:
            self.recordatorios.upsert_recordatorios_lote(items)
        dto = ResultadoLoteRecordatoriosDTO(enviadas=len(items))
        _log_lote("confirmaciones_lote_enviar", canal or "TODOS", len(cita_ids), dto)
        return dto


@dataclass(frozen=True, slots=True)
class _ResultadoPreparacionInterno:
    dto: ResultadoLoteRecordatoriosDTO
    items_upsert: list[tuple[int, str, str, str]]


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


def _validar_canal_lote(canal: str) -> str:
    valor = _validar_canal(canal)
    if valor not in {"WHATSAPP", "EMAIL"}:
        raise ValueError(f"Canal inválido para lote: {canal}")
    return valor


def _contabilizar_preparacion(
    cita_ids: tuple[int, ...],
    canal: str,
    contactos: dict[int, tuple[str | None, str | None]],
    estados: dict[tuple[int, str], str],
    now_utc: str,
) -> _ResultadoPreparacionInterno:
    omitidas_sin_contacto = 0
    omitidas_ya_enviado = 0
    items_upsert: list[tuple[int, str, str, str]] = []
    for cita_id in cita_ids:
        telefono, email = contactos.get(cita_id, (None, None))
        if _falta_contacto(canal, telefono, email):
            omitidas_sin_contacto += 1
            continue
        if estados.get((cita_id, canal)) == "ENVIADO":
            omitidas_ya_enviado += 1
            continue
        items_upsert.append((cita_id, canal, "PREPARADO", now_utc))
    dto = ResultadoLoteRecordatoriosDTO(
        preparadas=len(items_upsert),
        omitidas_sin_contacto=omitidas_sin_contacto,
        omitidas_ya_enviado=omitidas_ya_enviado,
    )
    return _ResultadoPreparacionInterno(dto=dto, items_upsert=items_upsert)


def _falta_contacto(canal: str, telefono: str | None, email: str | None) -> bool:
    if canal == "WHATSAPP":
        return not telefono
    return not email


def _log_lote(action: str, canal: str, total_seleccionadas: int, resultado: ResultadoLoteRecordatoriosDTO) -> None:
    LOGGER.info(
        "recordatorios_lote",
        extra={
            "action": action,
            "canal": canal,
            "total_seleccionadas": total_seleccionadas,
            "preparadas": resultado.preparadas,
            "enviadas": resultado.enviadas,
            "omitidas_sin_contacto": resultado.omitidas_sin_contacto,
            "omitidas_ya_enviado": resultado.omitidas_ya_enviado,
            "errores": resultado.errores,
        },
    )


def _advertencias_contacto(
    traductor: Callable[[str], str], canal: str, datos: DatosRecordatorioCitaDTO
) -> tuple[str, ...]:
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
