from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.seguros.analisis_migracion import ResultadoSimulacionMigracionSeguro
from clinicdesk.app.domain.seguros.segmentacion import (
    EncajePlanSeguro,
    EvaluacionFitComercialSeguro,
    FriccionMigracionSeguro,
    MotivacionCompraSeguro,
    ObjecionComercialSeguro,
    PerfilComercialSeguro,
    SensibilidadPrecioSeguro,
)


@dataclass(frozen=True, slots=True)
class SolicitudFitComercialSeguro:
    perfil: PerfilComercialSeguro
    simulacion_migracion: ResultadoSimulacionMigracionSeguro


class MotorFitComercialSeguro:
    def evaluar(self, solicitud: SolicitudFitComercialSeguro) -> EvaluacionFitComercialSeguro:
        puntaje = _puntaje_base_clasificacion(solicitud.simulacion_migracion.clasificacion)
        puntaje += _puntaje_sensibilidad(solicitud.perfil.sensibilidad_precio)
        puntaje += _puntaje_friccion(solicitud.perfil.friccion_migracion)
        puntaje += _puntaje_objecion(solicitud.perfil.objecion_principal)
        puntaje += _puntaje_motivaciones(solicitud.perfil.motivaciones)
        puntaje -= len(solicitud.simulacion_migracion.advertencias)

        encaje = _encaje_por_puntaje(puntaje, solicitud.simulacion_migracion.clasificacion)
        return EvaluacionFitComercialSeguro(
            encaje_plan=encaje,
            motivo_principal=_motivo_principal(encaje, solicitud),
            riesgos_friccion=_riesgos(solicitud),
            argumentos_valor=_argumentos_valor(solicitud),
            conviene_insistir=encaje in {EncajePlanSeguro.ALTO, EncajePlanSeguro.MEDIO},
            revision_humana_recomendada=_requiere_revision(encaje, solicitud),
        )


def _puntaje_base_clasificacion(clasificacion: str) -> int:
    return {"FAVORABLE": 5, "REVISAR": 2, "DESFAVORABLE": -3}.get(clasificacion, 0)


def _puntaje_sensibilidad(sensibilidad: SensibilidadPrecioSeguro) -> int:
    return {
        SensibilidadPrecioSeguro.BAJA: 2,
        SensibilidadPrecioSeguro.MEDIA: 0,
        SensibilidadPrecioSeguro.ALTA: -2,
    }[sensibilidad]


def _puntaje_friccion(friccion: FriccionMigracionSeguro) -> int:
    return {FriccionMigracionSeguro.BAJA: 2, FriccionMigracionSeguro.MEDIA: 0, FriccionMigracionSeguro.ALTA: -3}[
        friccion
    ]


def _puntaje_objecion(objecion: ObjecionComercialSeguro) -> int:
    return {
        ObjecionComercialSeguro.PRECIO_PERCIBIDO_ALTO: -2,
        ObjecionComercialSeguro.DUDAS_COBERTURA: -2,
        ObjecionComercialSeguro.NO_TIENE_TIEMPO: -1,
        ObjecionComercialSeguro.MIEDO_CAMBIO: -2,
        ObjecionComercialSeguro.PERMANENCIA_ACTUAL: -3,
    }[objecion]


def _puntaje_motivaciones(motivaciones: tuple[MotivacionCompraSeguro, ...]) -> int:
    if not motivaciones:
        return -1
    bonus = {MotivacionCompraSeguro.CONFIANZA_EN_CLINICA, MotivacionCompraSeguro.MEJOR_RELACION_CALIDAD_PRECIO}
    return 1 + sum(1 for item in motivaciones if item in bonus)


def _encaje_por_puntaje(puntaje: int, clasificacion: str) -> EncajePlanSeguro:
    if clasificacion == "DESFAVORABLE" and puntaje <= -2:
        return EncajePlanSeguro.BAJO
    if clasificacion == "REVISAR" and puntaje < 1:
        return EncajePlanSeguro.REVISAR
    if puntaje >= 4:
        return EncajePlanSeguro.ALTO
    if puntaje >= 1:
        return EncajePlanSeguro.MEDIO
    return EncajePlanSeguro.BAJO


def _motivo_principal(encaje: EncajePlanSeguro, solicitud: SolicitudFitComercialSeguro) -> str:
    if encaje is EncajePlanSeguro.ALTO:
        return "fit_alto_por_migracion_favorable_y_objecion_controlable"
    if encaje is EncajePlanSeguro.MEDIO:
        return "fit_medio_con_valor_comercial_y_fricciones_manejables"
    if encaje is EncajePlanSeguro.REVISAR:
        return "fit_a_revisar_por_advertencias_o_informacion_insuficiente"
    if solicitud.perfil.sensibilidad_precio is SensibilidadPrecioSeguro.ALTA:
        return "fit_bajo_por_sensibilidad_precio_alta"
    return "fit_bajo_por_objeciones_criticas"


def _riesgos(solicitud: SolicitudFitComercialSeguro) -> tuple[str, ...]:
    riesgos = list(solicitud.simulacion_migracion.advertencias)
    if solicitud.perfil.objecion_principal is ObjecionComercialSeguro.PERMANENCIA_ACTUAL:
        riesgos.append("objecion:permanencia")
    if solicitud.perfil.friccion_migracion is FriccionMigracionSeguro.ALTA:
        riesgos.append("friccion_migracion_alta")
    return tuple(sorted(set(riesgos)))


def _argumentos_valor(solicitud: SolicitudFitComercialSeguro) -> tuple[str, ...]:
    argumentos = list(solicitud.simulacion_migracion.impactos_positivos)
    if solicitud.perfil.necesidad_principal.value == "CONTINUIDAD_MEDICA":
        argumentos.append("argumento:continuidad_medica_clinica")
    if MotivacionCompraSeguro.CONFIANZA_EN_CLINICA in solicitud.perfil.motivaciones:
        argumentos.append("argumento:confianza_equipo_clinico")
    return tuple(sorted(set(argumentos)))


def _requiere_revision(encaje: EncajePlanSeguro, solicitud: SolicitudFitComercialSeguro) -> bool:
    return encaje in {EncajePlanSeguro.REVISAR, EncajePlanSeguro.BAJO} or bool(
        solicitud.simulacion_migracion.advertencias
    )
