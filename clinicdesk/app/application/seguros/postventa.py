from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol

from clinicdesk.app.domain.seguros.comercial import EstadoOportunidadSeguro, OportunidadSeguro
from clinicdesk.app.domain.seguros.postventa import (
    AseguradoPrincipalSeguro,
    BeneficiarioSeguro,
    CoberturaActivaPolizaSeguro,
    EstadoAseguradoSeguro,
    EstadoIncidenciaPolizaSeguro,
    EstadoPolizaSeguro,
    EstadoRenovacionPolizaSeguro,
    IncidenciaPolizaSeguro,
    PolizaSeguro,
    RenovacionPolizaSeguro,
    TipoIncidenciaPolizaSeguro,
    VigenciaPolizaSeguro,
)


class RepositorioPolizaSeguro(Protocol):
    def guardar_poliza(self, poliza: PolizaSeguro) -> None: ...

    def obtener_poliza(self, id_poliza: str) -> PolizaSeguro: ...

    def listar_polizas(self, filtro: "FiltroCarteraPolizaSeguro") -> tuple[PolizaSeguro, ...]: ...

    def guardar_incidencia(self, id_poliza: str, incidencia: IncidenciaPolizaSeguro) -> None: ...


class RepositorioOportunidadSeguro(Protocol):
    def obtener_oportunidad(self, id_oportunidad: str) -> OportunidadSeguro: ...


@dataclass(frozen=True, slots=True)
class SolicitudAltaPolizaDesdeConversion:
    id_oportunidad: str
    id_poliza: str
    nombre_titular: str
    documento_titular: str
    fecha_inicio: date
    beneficiarios: tuple[BeneficiarioSeguro, ...] = ()


@dataclass(frozen=True, slots=True)
class SolicitudRegistrarIncidenciaPoliza:
    id_poliza: str
    id_incidencia: str
    tipo: TipoIncidenciaPolizaSeguro
    descripcion: str
    fecha_apertura: date


@dataclass(frozen=True, slots=True)
class FiltroCarteraPolizaSeguro:
    estado: EstadoPolizaSeguro | None = None
    id_plan: str | None = None
    solo_con_incidencias: bool = False
    proximos_a_vencer_dias: int | None = None
    renovacion_pendiente: bool = False


class GestionPostventaPolizaSeguroService:
    def __init__(
        self,
        repositorio_poliza: RepositorioPolizaSeguro,
        repositorio_oportunidad: RepositorioOportunidadSeguro,
    ) -> None:
        self._repositorio_poliza = repositorio_poliza
        self._repositorio_oportunidad = repositorio_oportunidad

    def materializar_poliza_desde_conversion(self, solicitud: SolicitudAltaPolizaDesdeConversion) -> PolizaSeguro:
        oportunidad = self._repositorio_oportunidad.obtener_oportunidad(solicitud.id_oportunidad)
        self._validar_oportunidad_convertida(oportunidad)
        fecha_fin = solicitud.fecha_inicio + timedelta(days=365)
        poliza = PolizaSeguro(
            id_poliza=solicitud.id_poliza,
            id_oportunidad_origen=oportunidad.id_oportunidad,
            id_paciente=oportunidad.candidato.id_paciente,
            id_plan=oportunidad.plan_destino_id,
            estado=EstadoPolizaSeguro.ACTIVA,
            titular=AseguradoPrincipalSeguro(
                id_asegurado=f"tit-{solicitud.id_poliza}",
                nombre=solicitud.nombre_titular,
                documento=solicitud.documento_titular,
                estado=EstadoAseguradoSeguro.ACTIVO,
            ),
            beneficiarios=solicitud.beneficiarios,
            vigencia=VigenciaPolizaSeguro(fecha_inicio=solicitud.fecha_inicio, fecha_fin=fecha_fin),
            renovacion=RenovacionPolizaSeguro(
                fecha_renovacion_prevista=fecha_fin,
                estado=EstadoRenovacionPolizaSeguro.PENDIENTE,
            ),
            coberturas=(
                CoberturaActivaPolizaSeguro(
                    codigo_cobertura="COB_BASE",
                    descripcion="Cobertura base contratada",
                    activa=True,
                ),
            ),
            incidencias=(),
        )
        self._repositorio_poliza.guardar_poliza(poliza)
        return poliza

    def registrar_incidencia(self, solicitud: SolicitudRegistrarIncidenciaPoliza) -> IncidenciaPolizaSeguro:
        incidencia = IncidenciaPolizaSeguro(
            id_incidencia=solicitud.id_incidencia,
            tipo=solicitud.tipo,
            descripcion=solicitud.descripcion,
            estado=EstadoIncidenciaPolizaSeguro.ABIERTA,
            fecha_apertura=solicitud.fecha_apertura,
        )
        self._repositorio_poliza.guardar_incidencia(solicitud.id_poliza, incidencia)
        return incidencia

    def listar_cartera(self, filtro: FiltroCarteraPolizaSeguro | None = None) -> tuple[PolizaSeguro, ...]:
        return self._repositorio_poliza.listar_polizas(filtro or FiltroCarteraPolizaSeguro())

    @staticmethod
    def _validar_oportunidad_convertida(oportunidad: OportunidadSeguro) -> None:
        estados_validos = {
            EstadoOportunidadSeguro.CONVERTIDA,
            EstadoOportunidadSeguro.PENDIENTE_RENOVACION,
            EstadoOportunidadSeguro.RENOVADA,
        }
        if oportunidad.estado_actual not in estados_validos:
            msg = "La oportunidad no está en estado válido para materializar póliza"
            raise ValueError(msg)
