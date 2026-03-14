from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Protocol

from clinicdesk.app.application.seguros.analisis_migracion import ResultadoSimulacionMigracionSeguro
from clinicdesk.app.application.seguros.usecases import AnalizarMigracionSeguroUseCase, SolicitudAnalisisMigracionSeguro
from clinicdesk.app.domain.seguros.comercial import (
    CandidatoSeguro,
    EstadoOportunidadSeguro,
    OfertaSeguro,
    OportunidadSeguro,
    RenovacionSeguro,
    ResultadoComercialSeguro,
    ResultadoRenovacionSeguro,
    SeguimientoOportunidadSeguro,
)


class RepositorioComercialSeguro(Protocol):
    def guardar_oportunidad(self, oportunidad: OportunidadSeguro) -> None: ...

    def obtener_oportunidad(self, id_oportunidad: str) -> OportunidadSeguro: ...

    def guardar_oferta(self, oferta: OfertaSeguro) -> None: ...

    def obtener_oferta_por_oportunidad(self, id_oportunidad: str) -> OfertaSeguro | None: ...

    def guardar_renovacion(self, renovacion: RenovacionSeguro) -> None: ...

    def listar_renovaciones_pendientes(self) -> tuple[RenovacionSeguro, ...]: ...


@dataclass(frozen=True, slots=True)
class SolicitudNuevaOportunidadSeguro:
    id_oportunidad: str
    id_candidato: str
    id_paciente: str
    segmento: str
    plan_origen_id: str
    plan_destino_id: str


class GestionComercialSeguroService:
    def __init__(self, analizador: AnalizarMigracionSeguroUseCase, repositorio: RepositorioComercialSeguro) -> None:
        self._analizador = analizador
        self._repositorio = repositorio

    def abrir_oportunidad(self, solicitud: SolicitudNuevaOportunidadSeguro) -> OportunidadSeguro:
        oportunidad = OportunidadSeguro(
            id_oportunidad=solicitud.id_oportunidad,
            candidato=CandidatoSeguro(solicitud.id_candidato, solicitud.id_paciente, solicitud.segmento),
            plan_origen_id=solicitud.plan_origen_id,
            plan_destino_id=solicitud.plan_destino_id,
            estado_actual=EstadoOportunidadSeguro.DETECTADA,
            clasificacion_motor="PENDIENTE",
            seguimientos=(),
            resultado_comercial=None,
        )
        oportunidad = oportunidad.cambiar_estado(EstadoOportunidadSeguro.ANALIZADA)
        analisis = self._analizador.execute(
            SolicitudAnalisisMigracionSeguro(
                plan_origen_id=solicitud.plan_origen_id,
                plan_destino_id=solicitud.plan_destino_id,
                edad=34,
                residencia_pais="ES",
                historial_impagos=False,
                preexistencias_graves=False,
            )
        )
        oportunidad = oportunidad.cambiar_estado(EstadoOportunidadSeguro.ELEGIBLE)
        oportunidad = self._registrar_motor(oportunidad, analisis.simulacion)
        self._repositorio.guardar_oportunidad(oportunidad)
        return oportunidad

    def preparar_oferta(self, id_oportunidad: str, notas: tuple[str, ...]) -> OfertaSeguro:
        oportunidad = self._repositorio.obtener_oportunidad(id_oportunidad)
        analisis = self._analizador.execute(
            SolicitudAnalisisMigracionSeguro(
                plan_origen_id=oportunidad.plan_origen_id,
                plan_destino_id=oportunidad.plan_destino_id,
                edad=34,
                residencia_pais="ES",
                historial_impagos=False,
                preexistencias_graves=False,
            )
        )
        oferta = construir_oferta_desde_analisis(
            oportunidad.id_oportunidad, oportunidad.plan_destino_id, analisis.simulacion, notas
        )
        self._repositorio.guardar_oferta(oferta)
        self._repositorio.guardar_oportunidad(oportunidad.cambiar_estado(EstadoOportunidadSeguro.OFERTA_PREPARADA))
        return oferta

    def registrar_seguimiento(
        self,
        id_oportunidad: str,
        estado: EstadoOportunidadSeguro,
        accion_comercial: str,
        nota: str,
        siguiente_paso: str,
    ) -> OportunidadSeguro:
        oportunidad = self._repositorio.obtener_oportunidad(id_oportunidad)
        seguimiento = SeguimientoOportunidadSeguro(datetime.now(UTC), estado, accion_comercial, nota, siguiente_paso)
        actualizada = oportunidad.agregar_seguimiento(seguimiento)
        self._repositorio.guardar_oportunidad(actualizada)
        return actualizada

    def cerrar_oportunidad(self, id_oportunidad: str, resultado: ResultadoComercialSeguro) -> OportunidadSeguro:
        estado_destino = {
            ResultadoComercialSeguro.CONVERTIDO: EstadoOportunidadSeguro.CONVERTIDA,
            ResultadoComercialSeguro.RECHAZADO: EstadoOportunidadSeguro.RECHAZADA,
            ResultadoComercialSeguro.POSPUESTO: EstadoOportunidadSeguro.POSPUESTA,
            ResultadoComercialSeguro.PENDIENTE_REVISION: EstadoOportunidadSeguro.EN_SEGUIMIENTO,
        }[resultado]
        oportunidad = self._repositorio.obtener_oportunidad(id_oportunidad)
        oportunidad = oportunidad.cambiar_estado(estado_destino)
        self._repositorio.guardar_oportunidad(
            OportunidadSeguro(
                id_oportunidad=oportunidad.id_oportunidad,
                candidato=oportunidad.candidato,
                plan_origen_id=oportunidad.plan_origen_id,
                plan_destino_id=oportunidad.plan_destino_id,
                estado_actual=oportunidad.estado_actual,
                clasificacion_motor=oportunidad.clasificacion_motor,
                seguimientos=oportunidad.seguimientos,
                resultado_comercial=resultado,
            )
        )
        if resultado is ResultadoComercialSeguro.CONVERTIDO:
            self._programar_renovacion(oportunidad)
        return self._repositorio.obtener_oportunidad(id_oportunidad)

    def listar_renovaciones_pendientes(self) -> tuple[RenovacionSeguro, ...]:
        return self._repositorio.listar_renovaciones_pendientes()

    def registrar_resultado_renovacion(self, id_oportunidad: str, renovada: bool) -> None:
        estado = ResultadoRenovacionSeguro.RENOVADA if renovada else ResultadoRenovacionSeguro.NO_RENOVADA
        oportunidad = self._repositorio.obtener_oportunidad(id_oportunidad)
        oportunidad = oportunidad.cambiar_estado(
            EstadoOportunidadSeguro.RENOVADA if renovada else EstadoOportunidadSeguro.NO_RENOVADA
        )
        self._repositorio.guardar_oportunidad(oportunidad)
        self._repositorio.guardar_renovacion(
            RenovacionSeguro(
                id_renovacion=f"ren-{id_oportunidad}",
                id_oportunidad=id_oportunidad,
                plan_vigente_id=oportunidad.plan_destino_id,
                fecha_renovacion=date.today(),
                revision_pendiente=False,
                resultado=estado,
            )
        )

    def _registrar_motor(
        self, oportunidad: OportunidadSeguro, simulacion: ResultadoSimulacionMigracionSeguro
    ) -> OportunidadSeguro:
        return OportunidadSeguro(
            id_oportunidad=oportunidad.id_oportunidad,
            candidato=oportunidad.candidato,
            plan_origen_id=oportunidad.plan_origen_id,
            plan_destino_id=oportunidad.plan_destino_id,
            estado_actual=oportunidad.estado_actual,
            clasificacion_motor=simulacion.clasificacion,
            seguimientos=oportunidad.seguimientos,
            resultado_comercial=oportunidad.resultado_comercial,
        )

    def _programar_renovacion(self, oportunidad: OportunidadSeguro) -> None:
        self._repositorio.guardar_oportunidad(oportunidad.cambiar_estado(EstadoOportunidadSeguro.PENDIENTE_RENOVACION))
        self._repositorio.guardar_renovacion(
            RenovacionSeguro(
                id_renovacion=f"ren-{oportunidad.id_oportunidad}",
                id_oportunidad=oportunidad.id_oportunidad,
                plan_vigente_id=oportunidad.plan_destino_id,
                fecha_renovacion=date.today() + timedelta(days=330),
                revision_pendiente=True,
                resultado=ResultadoRenovacionSeguro.PENDIENTE,
            )
        )


def construir_oferta_desde_analisis(
    id_oportunidad: str,
    plan_propuesto_id: str,
    simulacion: ResultadoSimulacionMigracionSeguro,
    notas: tuple[str, ...],
) -> OfertaSeguro:
    return OfertaSeguro(
        id_oferta=f"of-{id_oportunidad}",
        id_oportunidad=id_oportunidad,
        plan_propuesto_id=plan_propuesto_id,
        resumen_valor=simulacion.resumen_ejecutivo,
        puntos_fuertes=simulacion.impactos_positivos,
        riesgos_revision=simulacion.advertencias + simulacion.impactos_negativos,
        clasificacion_migracion=simulacion.clasificacion,
        notas_comerciales=notas,
    )
