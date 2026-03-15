from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from clinicdesk.app.domain.seguros.economia_poliza import (
    CarteraEconomicaPolizaSeguro,
    CuotaPolizaSeguro,
    EstadoCuotaPolizaSeguro,
    EstadoPagoPolizaSeguro,
    ImpagoPolizaSeguro,
    NivelRiesgoEconomicoPolizaSeguro,
    ReactivacionPolizaSeguro,
    ResumenEconomicoPolizaSeguro,
    SuspensionPolizaSeguro,
)


@dataclass(frozen=True, slots=True)
class SolicitudEmitirCuotaPolizaSeguro:
    id_cuota: str
    id_poliza: str
    periodo: str
    fecha_emision: date
    fecha_vencimiento: date
    importe: float


@dataclass(frozen=True, slots=True)
class SolicitudRegistrarPagoCuotaSeguro:
    id_cuota: str
    fecha_pago: date


@dataclass(frozen=True, slots=True)
class SolicitudRegistrarImpagoSeguro:
    id_evento: str
    id_poliza: str
    id_cuota: str
    fecha_evento: date
    motivo: str


@dataclass(frozen=True, slots=True)
class SolicitudRegistrarSuspensionPolizaSeguro:
    id_evento: str
    id_poliza: str
    fecha_evento: date
    motivo: str


@dataclass(frozen=True, slots=True)
class SolicitudRegistrarReactivacionPolizaSeguro:
    id_evento: str
    id_poliza: str
    fecha_evento: date
    motivo: str


@dataclass(frozen=True, slots=True)
class FiltroCarteraEconomicaPolizaSeguro:
    estado_pago: EstadoPagoPolizaSeguro | None = None
    nivel_riesgo: NivelRiesgoEconomicoPolizaSeguro | None = None
    solo_suspendidas: bool = False
    solo_reactivables: bool = False


class RepositorioEconomiaPolizaSeguro(Protocol):
    def guardar_cuota(self, cuota: CuotaPolizaSeguro) -> None: ...

    def obtener_cuota(self, id_cuota: str) -> CuotaPolizaSeguro: ...

    def listar_cuotas_poliza(self, id_poliza: str) -> tuple[CuotaPolizaSeguro, ...]: ...

    def listar_cuotas(self) -> tuple[CuotaPolizaSeguro, ...]: ...

    def guardar_impago(self, evento: ImpagoPolizaSeguro) -> None: ...

    def guardar_suspension(self, evento: SuspensionPolizaSeguro) -> None: ...

    def guardar_reactivacion(self, evento: ReactivacionPolizaSeguro) -> None: ...

    def tiene_suspension_activa(self, id_poliza: str) -> bool: ...


def _resolver_estado_cuota(cuota: CuotaPolizaSeguro, hoy: date, impagada: bool) -> EstadoCuotaPolizaSeguro:
    if cuota.fecha_pago is not None:
        return EstadoCuotaPolizaSeguro.PAGADA
    if impagada:
        return EstadoCuotaPolizaSeguro.IMPAGADA
    if cuota.fecha_vencimiento < hoy:
        return EstadoCuotaPolizaSeguro.VENCIDA
    return EstadoCuotaPolizaSeguro.EMITIDA


def _motivo_por_estado(
    estado: EstadoPagoPolizaSeguro,
    cuotas_vencidas: int,
    cuotas_impagadas: int,
    suspension_activa: bool,
) -> str:
    if estado is EstadoPagoPolizaSeguro.SUSPENDIDA:
        return "Poliza con suspension operativa activa por riesgo economico"
    if estado is EstadoPagoPolizaSeguro.REACTIVABLE:
        return "Poliza suspendida previamente con pago suficiente para revision de reactivacion"
    if estado is EstadoPagoPolizaSeguro.IMPAGADA:
        return f"Impago confirmado en {cuotas_impagadas} cuota(s)"
    if estado is EstadoPagoPolizaSeguro.VENCIDA:
        return f"Cuotas vencidas sin pago: {cuotas_vencidas}"
    if estado is EstadoPagoPolizaSeguro.PROXIMA_A_VENCER:
        return "Existe cuota proxima a vencer en menos de 5 dias"
    if suspension_activa:
        return "Poliza con historial de suspension en seguimiento"
    return "Sin alertas economicas relevantes"


def construir_resumen_economico_poliza(
    id_poliza: str,
    cuotas: tuple[CuotaPolizaSeguro, ...],
    hoy: date,
    suspension_activa: bool,
) -> ResumenEconomicoPolizaSeguro:
    cuotas_ordenadas = tuple(sorted(cuotas, key=lambda item: item.fecha_vencimiento))
    cuotas_emitidas = len(cuotas_ordenadas)
    cuotas_pagadas = sum(1 for item in cuotas_ordenadas if item.fecha_pago is not None)
    cuotas_impagadas = sum(1 for item in cuotas_ordenadas if item.estado is EstadoCuotaPolizaSeguro.IMPAGADA)
    cuotas_vencidas = sum(
        1
        for item in cuotas_ordenadas
        if item.fecha_pago is None and item.estado in {EstadoCuotaPolizaSeguro.VENCIDA, EstadoCuotaPolizaSeguro.IMPAGADA}
    )
    total_emitido = float(sum(item.importe for item in cuotas_ordenadas))
    total_pagado = float(sum(item.importe for item in cuotas_ordenadas if item.fecha_pago is not None))
    total_pendiente = max(total_emitido - total_pagado, 0.0)

    proxima = next((item for item in cuotas_ordenadas if item.fecha_pago is None), None)
    dias_para_vencer = None if proxima is None else (proxima.fecha_vencimiento - hoy).days

    if suspension_activa and total_pendiente <= 0:
        estado = EstadoPagoPolizaSeguro.REACTIVABLE
    elif suspension_activa:
        estado = EstadoPagoPolizaSeguro.SUSPENDIDA
    elif cuotas_impagadas > 0:
        estado = EstadoPagoPolizaSeguro.IMPAGADA
    elif cuotas_vencidas > 0:
        estado = EstadoPagoPolizaSeguro.VENCIDA
    elif dias_para_vencer is not None and dias_para_vencer <= 5:
        estado = EstadoPagoPolizaSeguro.PROXIMA_A_VENCER
    else:
        estado = EstadoPagoPolizaSeguro.AL_DIA

    if estado in {EstadoPagoPolizaSeguro.SUSPENDIDA, EstadoPagoPolizaSeguro.IMPAGADA}:
        riesgo = NivelRiesgoEconomicoPolizaSeguro.ALTO
    elif estado in {EstadoPagoPolizaSeguro.VENCIDA, EstadoPagoPolizaSeguro.REACTIVABLE}:
        riesgo = NivelRiesgoEconomicoPolizaSeguro.MEDIO
    else:
        riesgo = NivelRiesgoEconomicoPolizaSeguro.BAJO

    return ResumenEconomicoPolizaSeguro(
        id_poliza=id_poliza,
        estado_pago=estado,
        nivel_riesgo=riesgo,
        total_emitido=total_emitido,
        total_pagado=total_pagado,
        total_pendiente=total_pendiente,
        cuotas_emitidas=cuotas_emitidas,
        cuotas_pagadas=cuotas_pagadas,
        cuotas_vencidas=cuotas_vencidas,
        cuotas_impagadas=cuotas_impagadas,
        suspendida=suspension_activa,
        reactivable=estado is EstadoPagoPolizaSeguro.REACTIVABLE,
        motivo_estado=_motivo_por_estado(estado, cuotas_vencidas, cuotas_impagadas, suspension_activa),
    )


class GestionEconomicaPolizaSeguroService:
    def __init__(self, repositorio: RepositorioEconomiaPolizaSeguro) -> None:
        self._repositorio = repositorio

    def emitir_cuota(self, solicitud: SolicitudEmitirCuotaPolizaSeguro) -> CuotaPolizaSeguro:
        cuota = CuotaPolizaSeguro(
            id_cuota=solicitud.id_cuota,
            id_poliza=solicitud.id_poliza,
            periodo=solicitud.periodo,
            fecha_emision=solicitud.fecha_emision,
            fecha_vencimiento=solicitud.fecha_vencimiento,
            importe=solicitud.importe,
            estado=EstadoCuotaPolizaSeguro.EMITIDA,
            fecha_pago=None,
        )
        self._repositorio.guardar_cuota(cuota)
        return cuota

    def registrar_pago_cuota(self, solicitud: SolicitudRegistrarPagoCuotaSeguro) -> CuotaPolizaSeguro:
        cuota = self._repositorio.obtener_cuota(solicitud.id_cuota)
        actualizada = CuotaPolizaSeguro(
            id_cuota=cuota.id_cuota,
            id_poliza=cuota.id_poliza,
            periodo=cuota.periodo,
            fecha_emision=cuota.fecha_emision,
            fecha_vencimiento=cuota.fecha_vencimiento,
            importe=cuota.importe,
            estado=EstadoCuotaPolizaSeguro.PAGADA,
            fecha_pago=solicitud.fecha_pago,
        )
        self._repositorio.guardar_cuota(actualizada)
        return actualizada

    def registrar_impago(self, solicitud: SolicitudRegistrarImpagoSeguro) -> ImpagoPolizaSeguro:
        cuota = self._repositorio.obtener_cuota(solicitud.id_cuota)
        actualizada = CuotaPolizaSeguro(
            id_cuota=cuota.id_cuota,
            id_poliza=cuota.id_poliza,
            periodo=cuota.periodo,
            fecha_emision=cuota.fecha_emision,
            fecha_vencimiento=cuota.fecha_vencimiento,
            importe=cuota.importe,
            estado=EstadoCuotaPolizaSeguro.IMPAGADA,
            fecha_pago=cuota.fecha_pago,
        )
        self._repositorio.guardar_cuota(actualizada)
        evento = ImpagoPolizaSeguro(
            id_evento=solicitud.id_evento,
            id_poliza=solicitud.id_poliza,
            id_cuota=solicitud.id_cuota,
            fecha_evento=solicitud.fecha_evento,
            motivo=solicitud.motivo,
        )
        self._repositorio.guardar_impago(evento)
        return evento

    def registrar_suspension(self, solicitud: SolicitudRegistrarSuspensionPolizaSeguro) -> SuspensionPolizaSeguro:
        evento = SuspensionPolizaSeguro(
            id_evento=solicitud.id_evento,
            id_poliza=solicitud.id_poliza,
            fecha_evento=solicitud.fecha_evento,
            motivo=solicitud.motivo,
            automatica=False,
        )
        self._repositorio.guardar_suspension(evento)
        return evento

    def registrar_reactivacion(self, solicitud: SolicitudRegistrarReactivacionPolizaSeguro) -> ReactivacionPolizaSeguro:
        evento = ReactivacionPolizaSeguro(
            id_evento=solicitud.id_evento,
            id_poliza=solicitud.id_poliza,
            fecha_evento=solicitud.fecha_evento,
            motivo=solicitud.motivo,
        )
        self._repositorio.guardar_reactivacion(evento)
        return evento

    def obtener_resumen_poliza(self, id_poliza: str, hoy: date | None = None) -> ResumenEconomicoPolizaSeguro:
        fecha = hoy or date.today()
        cuotas = self._repositorio.listar_cuotas_poliza(id_poliza)
        normalizadas = tuple(
            CuotaPolizaSeguro(
                id_cuota=cuota.id_cuota,
                id_poliza=cuota.id_poliza,
                periodo=cuota.periodo,
                fecha_emision=cuota.fecha_emision,
                fecha_vencimiento=cuota.fecha_vencimiento,
                importe=cuota.importe,
                estado=_resolver_estado_cuota(cuota, fecha, cuota.estado is EstadoCuotaPolizaSeguro.IMPAGADA),
                fecha_pago=cuota.fecha_pago,
            )
            for cuota in cuotas
        )
        return construir_resumen_economico_poliza(
            id_poliza=id_poliza,
            cuotas=normalizadas,
            hoy=fecha,
            suspension_activa=self._repositorio.tiene_suspension_activa(id_poliza),
        )

    def listar_cartera_economica(
        self,
        filtro: FiltroCarteraEconomicaPolizaSeguro | None = None,
        hoy: date | None = None,
    ) -> tuple[ResumenEconomicoPolizaSeguro, ...]:
        fecha = hoy or date.today()
        filtro_aplicado = filtro or FiltroCarteraEconomicaPolizaSeguro()
        cuotas = self._repositorio.listar_cuotas()
        ids_poliza = tuple(sorted({item.id_poliza for item in cuotas}))
        resumenes = tuple(self.obtener_resumen_poliza(id_poliza, fecha) for id_poliza in ids_poliza)

        def cumple(item: ResumenEconomicoPolizaSeguro) -> bool:
            if filtro_aplicado.estado_pago and item.estado_pago is not filtro_aplicado.estado_pago:
                return False
            if filtro_aplicado.nivel_riesgo and item.nivel_riesgo is not filtro_aplicado.nivel_riesgo:
                return False
            if filtro_aplicado.solo_suspendidas and not item.suspendida:
                return False
            if filtro_aplicado.solo_reactivables and not item.reactivable:
                return False
            return True

        return tuple(item for item in resumenes if cumple(item))

    def construir_cartera_operativa(
        self,
        hoy: date | None = None,
    ) -> CarteraEconomicaPolizaSeguro:
        resumenes = self.listar_cartera_economica(hoy=hoy)
        return CarteraEconomicaPolizaSeguro(
            al_dia=tuple(item for item in resumenes if item.estado_pago is EstadoPagoPolizaSeguro.AL_DIA),
            proximas_a_vencer=tuple(
                item for item in resumenes if item.estado_pago is EstadoPagoPolizaSeguro.PROXIMA_A_VENCER
            ),
            vencidas=tuple(item for item in resumenes if item.estado_pago is EstadoPagoPolizaSeguro.VENCIDA),
            impagadas=tuple(item for item in resumenes if item.estado_pago is EstadoPagoPolizaSeguro.IMPAGADA),
            suspendidas=tuple(item for item in resumenes if item.estado_pago is EstadoPagoPolizaSeguro.SUSPENDIDA),
            reactivables=tuple(item for item in resumenes if item.estado_pago is EstadoPagoPolizaSeguro.REACTIVABLE),
        )
