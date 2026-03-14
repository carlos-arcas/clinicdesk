from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Protocol

from clinicdesk.app.application.seguros.analisis_migracion import ResultadoSimulacionMigracionSeguro
from clinicdesk.app.application.seguros.fit_comercial import MotorFitComercialSeguro, SolicitudFitComercialSeguro
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
from clinicdesk.app.domain.seguros.segmentacion import (
    FriccionMigracionSeguro,
    MotivacionCompraSeguro,
    NecesidadPrincipalSeguro,
    ObjecionComercialSeguro,
    OrigenClienteSeguro,
    PerfilComercialSeguro,
    SegmentoClienteSeguro,
    SensibilidadPrecioSeguro,
)


class RepositorioComercialSeguro(Protocol):
    def guardar_oportunidad(self, oportunidad: OportunidadSeguro) -> None: ...

    def obtener_oportunidad(self, id_oportunidad: str) -> OportunidadSeguro: ...

    def guardar_oferta(self, oferta: OfertaSeguro) -> None: ...

    def obtener_oferta_por_oportunidad(self, id_oportunidad: str) -> OfertaSeguro | None: ...

    def guardar_renovacion(self, renovacion: RenovacionSeguro) -> None: ...

    def listar_renovaciones_pendientes(self) -> tuple[RenovacionSeguro, ...]: ...

    def listar_oportunidades(self, filtro: "FiltroCarteraSeguro") -> tuple[OportunidadSeguro, ...]: ...

    def listar_seguimientos_recientes(self, limite: int = 20) -> tuple[SeguimientoOportunidadSeguro, ...]: ...

    def listar_historial_oportunidad(self, id_oportunidad: str) -> tuple[SeguimientoOportunidadSeguro, ...]: ...

    def construir_dataset_ml_comercial(self) -> list[dict[str, object]]: ...


@dataclass(frozen=True, slots=True)
class FiltroCarteraSeguro:
    estado: EstadoOportunidadSeguro | None = None
    plan_destino_id: str | None = None
    clasificacion_migracion: str | None = None
    fecha_desde: date | None = None
    solo_renovacion_pendiente: bool = False


@dataclass(frozen=True, slots=True)
class SolicitudNuevaOportunidadSeguro:
    id_oportunidad: str
    id_candidato: str
    id_paciente: str
    segmento_cliente: SegmentoClienteSeguro
    origen_cliente: OrigenClienteSeguro
    necesidad_principal: NecesidadPrincipalSeguro
    motivaciones: tuple[MotivacionCompraSeguro, ...]
    objecion_principal: ObjecionComercialSeguro
    sensibilidad_precio: SensibilidadPrecioSeguro
    friccion_migracion: FriccionMigracionSeguro
    plan_origen_id: str
    plan_destino_id: str


class GestionComercialSeguroService:
    def __init__(self, analizador: AnalizarMigracionSeguroUseCase, repositorio: RepositorioComercialSeguro) -> None:
        self._analizador = analizador
        self._repositorio = repositorio
        self._motor_fit = MotorFitComercialSeguro()

    def abrir_oportunidad(self, solicitud: SolicitudNuevaOportunidadSeguro) -> OportunidadSeguro:
        oportunidad = OportunidadSeguro(
            id_oportunidad=solicitud.id_oportunidad,
            candidato=CandidatoSeguro(solicitud.id_candidato, solicitud.id_paciente, solicitud.segmento_cliente.value),
            plan_origen_id=solicitud.plan_origen_id,
            plan_destino_id=solicitud.plan_destino_id,
            estado_actual=EstadoOportunidadSeguro.DETECTADA,
            clasificacion_motor="PENDIENTE",
            perfil_comercial=PerfilComercialSeguro(
                segmento_cliente=solicitud.segmento_cliente,
                origen_cliente=solicitud.origen_cliente,
                necesidad_principal=solicitud.necesidad_principal,
                motivaciones=solicitud.motivaciones,
                objecion_principal=solicitud.objecion_principal,
                sensibilidad_precio=solicitud.sensibilidad_precio,
                friccion_migracion=solicitud.friccion_migracion,
            ),
            evaluacion_fit=None,
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
        if oportunidad.perfil_comercial:
            evaluacion = self._motor_fit.evaluar(
                SolicitudFitComercialSeguro(
                    perfil=oportunidad.perfil_comercial, simulacion_migracion=analisis.simulacion
                )
            )
            oportunidad = self._registrar_fit(oportunidad, evaluacion)
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
                perfil_comercial=oportunidad.perfil_comercial,
                evaluacion_fit=oportunidad.evaluacion_fit,
                seguimientos=oportunidad.seguimientos,
                resultado_comercial=resultado,
            )
        )
        if resultado is ResultadoComercialSeguro.CONVERTIDO:
            self._programar_renovacion(oportunidad)
        return self._repositorio.obtener_oportunidad(id_oportunidad)

    def listar_renovaciones_pendientes(self) -> tuple[RenovacionSeguro, ...]:
        return self._repositorio.listar_renovaciones_pendientes()

    def listar_cartera(self, filtro: FiltroCarteraSeguro | None = None) -> tuple[OportunidadSeguro, ...]:
        return self._repositorio.listar_oportunidades(filtro or FiltroCarteraSeguro())

    def listar_oportunidades_por_estado(self, estado: EstadoOportunidadSeguro) -> tuple[OportunidadSeguro, ...]:
        return self._repositorio.listar_oportunidades(FiltroCarteraSeguro(estado=estado))

    def listar_seguimiento_reciente(self, limite: int = 20) -> tuple[SeguimientoOportunidadSeguro, ...]:
        return self._repositorio.listar_seguimientos_recientes(limite)

    def recuperar_historial(self, id_oportunidad: str) -> tuple[SeguimientoOportunidadSeguro, ...]:
        return self._repositorio.listar_historial_oportunidad(id_oportunidad)

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
            perfil_comercial=oportunidad.perfil_comercial,
            evaluacion_fit=oportunidad.evaluacion_fit,
            seguimientos=oportunidad.seguimientos,
            resultado_comercial=oportunidad.resultado_comercial,
        )

    def _registrar_fit(self, oportunidad: OportunidadSeguro, evaluacion) -> OportunidadSeguro:
        return OportunidadSeguro(
            id_oportunidad=oportunidad.id_oportunidad,
            candidato=oportunidad.candidato,
            plan_origen_id=oportunidad.plan_origen_id,
            plan_destino_id=oportunidad.plan_destino_id,
            estado_actual=oportunidad.estado_actual,
            clasificacion_motor=oportunidad.clasificacion_motor,
            perfil_comercial=oportunidad.perfil_comercial,
            evaluacion_fit=evaluacion,
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
