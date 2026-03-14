from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import mean

from clinicdesk.app.application.seguros.comercial import RepositorioComercialSeguro
from clinicdesk.app.domain.seguros.comercial import OportunidadSeguro


class BandaPropensionSeguro(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"
    INCIERTA = "INCIERTA"


class NivelPrioridadComercialSeguro(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"
    NO_PRIORITARIA = "NO_PRIORITARIA"


class SemaforoComercialSeguro(str, Enum):
    VERDE = "VERDE"
    AMARILLO = "AMARILLO"
    ROJO = "ROJO"


class AccionComercialSugerida(str, Enum):
    INSISTIR_SEGUIMIENTO = "INSISTIR_SEGUIMIENTO"
    PREPARAR_MEJOR_OFERTA = "PREPARAR_MEJOR_OFERTA"
    REVISAR_OBJECION_PRECIO = "REVISAR_OBJECION_PRECIO"
    REVISAR_ELEGIBILIDAD_MIGRACION = "REVISAR_ELEGIBILIDAD_MIGRACION"
    POSPONER_Y_REEVALUAR = "POSPONER_Y_REEVALUAR"
    NO_PRIORIZAR_POR_AHORA = "NO_PRIORIZAR_POR_AHORA"


@dataclass(frozen=True, slots=True)
class RegistroDatasetComercialSeguro:
    id_oportunidad: str
    segmento_cliente: str
    origen_cliente: str
    sensibilidad_precio: str
    objecion_principal: str
    friccion_migracion: str
    clasificacion_motor: str
    fit_comercial: str
    plan_destino_id: str
    total_seguimientos: int
    dias_ciclo: int
    estado_actual: str
    renovada: bool
    resultado_comercial: str


@dataclass(frozen=True, slots=True)
class PrediccionComercialSeguro:
    id_oportunidad: str
    propension_conversion: float
    propension_migracion_favorable: float
    banda_conversion: BandaPropensionSeguro
    banda_migracion: BandaPropensionSeguro
    confianza_relativa: float
    motivo_principal: str
    cautela_limite: str


@dataclass(frozen=True, slots=True)
class PrioridadOportunidadSeguro:
    id_oportunidad: str
    score_prioridad: float
    prioridad: NivelPrioridadComercialSeguro
    semaforo: SemaforoComercialSeguro
    accion_sugerida: AccionComercialSugerida
    motivo_principal: str
    cautela_limite: str
    confianza_relativa: float


@dataclass(frozen=True, slots=True)
class InterpretacionHumanaComercialSeguro:
    significado: str
    utilidad_practica: str
    porque_priorizada: str
    cautela: str
    accion_humana_recomendada: str


@dataclass(frozen=True, slots=True)
class CarteraPriorizadaSeguro:
    oportunidades: tuple[PrioridadOportunidadSeguro, ...]
    oportunidad_mas_caliente: PrioridadOportunidadSeguro | None
    oportunidades_vigilar: tuple[PrioridadOportunidadSeguro, ...]
    oportunidades_no_prioritarias: tuple[PrioridadOportunidadSeguro, ...]


class ScoringComercialSeguroService:
    def __init__(self, repositorio: RepositorioComercialSeguro, minimo_muestras: int = 8) -> None:
        self._repositorio = repositorio
        self._minimo_muestras = minimo_muestras

    def construir_dataset(self) -> tuple[RegistroDatasetComercialSeguro, ...]:
        filas = self._repositorio.construir_dataset_ml_comercial()
        return tuple(_mapear_registro(item) for item in filas)

    def priorizar_cartera(self, oportunidades: tuple[OportunidadSeguro, ...]) -> CarteraPriorizadaSeguro:
        dataset = self.construir_dataset()
        predicciones = [self._predecir(item, dataset) for item in oportunidades]
        prioridades = tuple(
            sorted((self._priorizar(item) for item in predicciones), key=lambda p: p.score_prioridad, reverse=True)
        )
        calientes = tuple(item for item in prioridades if item.prioridad is NivelPrioridadComercialSeguro.ALTA)
        vigilar = tuple(item for item in prioridades if item.prioridad is NivelPrioridadComercialSeguro.MEDIA)
        no_prioritarias = tuple(
            item for item in prioridades if item.prioridad is NivelPrioridadComercialSeguro.NO_PRIORITARIA
        )
        return CarteraPriorizadaSeguro(
            oportunidades=prioridades,
            oportunidad_mas_caliente=calientes[0] if calientes else (prioridades[0] if prioridades else None),
            oportunidades_vigilar=vigilar,
            oportunidades_no_prioritarias=no_prioritarias,
        )

    def interpretar(self, prioridad: PrioridadOportunidadSeguro) -> InterpretacionHumanaComercialSeguro:
        return InterpretacionHumanaComercialSeguro(
            significado=_significado_prioridad(prioridad.prioridad),
            utilidad_practica="Orienta el orden de contacto comercial sin automatizar decisiones.",
            porque_priorizada=prioridad.motivo_principal,
            cautela=prioridad.cautela_limite,
            accion_humana_recomendada=_accion_humana(prioridad.accion_sugerida),
        )

    def _predecir(
        self, oportunidad: OportunidadSeguro, dataset: tuple[RegistroDatasetComercialSeguro, ...]
    ) -> PrediccionComercialSeguro:
        base_conversion = _probabilidad_base(dataset, "CONVERTIDO")
        base_migracion = _probabilidad_migracion_favorable(dataset)
        ajuste = _ajuste_oportunidad(oportunidad)
        confianza = min(1.0, len(dataset) / max(self._minimo_muestras * 2, 1))
        if len(dataset) < self._minimo_muestras:
            cautela = (
                "Base historica insuficiente: usar score como orientacion inicial y validar con criterio comercial."
            )
        else:
            cautela = "Score orientativo: no sustituye revision humana del contexto de cliente."
        conversion = _acotar(base_conversion + ajuste * 0.55)
        migracion = _acotar(base_migracion + ajuste * 0.45)
        return PrediccionComercialSeguro(
            id_oportunidad=oportunidad.id_oportunidad,
            propension_conversion=conversion,
            propension_migracion_favorable=migracion,
            banda_conversion=_banda(conversion, confianza),
            banda_migracion=_banda(migracion, confianza),
            confianza_relativa=round(confianza, 3),
            motivo_principal=_motivo_prediccion(oportunidad),
            cautela_limite=cautela,
        )

    def _priorizar(self, prediccion: PrediccionComercialSeguro) -> PrioridadOportunidadSeguro:
        score = round((prediccion.propension_conversion * 0.6 + prediccion.propension_migracion_favorable * 0.4), 4)
        if prediccion.confianza_relativa < 0.35:
            prioridad = NivelPrioridadComercialSeguro.MEDIA if score >= 0.55 else NivelPrioridadComercialSeguro.BAJA
            semaforo = SemaforoComercialSeguro.AMARILLO
        elif score >= 0.72:
            prioridad = NivelPrioridadComercialSeguro.ALTA
            semaforo = SemaforoComercialSeguro.VERDE
        elif score >= 0.52:
            prioridad = NivelPrioridadComercialSeguro.MEDIA
            semaforo = SemaforoComercialSeguro.AMARILLO
        elif score >= 0.35:
            prioridad = NivelPrioridadComercialSeguro.BAJA
            semaforo = SemaforoComercialSeguro.ROJO
        else:
            prioridad = NivelPrioridadComercialSeguro.NO_PRIORITARIA
            semaforo = SemaforoComercialSeguro.ROJO
        return PrioridadOportunidadSeguro(
            id_oportunidad=prediccion.id_oportunidad,
            score_prioridad=score,
            prioridad=prioridad,
            semaforo=semaforo,
            accion_sugerida=_siguiente_accion(prediccion, prioridad),
            motivo_principal=prediccion.motivo_principal,
            cautela_limite=prediccion.cautela_limite,
            confianza_relativa=prediccion.confianza_relativa,
        )


def _mapear_registro(raw: dict[str, object]) -> RegistroDatasetComercialSeguro:
    return RegistroDatasetComercialSeguro(
        id_oportunidad=str(raw.get("id_oportunidad", "")),
        segmento_cliente=str(raw.get("segmento_cliente") or "SIN_SEGMENTO"),
        origen_cliente=str(raw.get("origen_cliente") or "SIN_ORIGEN"),
        sensibilidad_precio=str(raw.get("sensibilidad_precio") or "SIN_DATO"),
        objecion_principal=str(raw.get("objecion_principal") or "SIN_OBJECION"),
        friccion_migracion=str(raw.get("friccion_migracion") or "SIN_DATO"),
        clasificacion_motor=str(raw.get("clasificacion_motor") or "PENDIENTE"),
        fit_comercial=str(raw.get("fit_comercial") or "SIN_FIT"),
        plan_destino_id=str(raw.get("plan_destino_id") or ""),
        total_seguimientos=int(raw.get("total_seguimientos") or 0),
        dias_ciclo=max(int(raw.get("dias_ciclo") or 0), 0),
        estado_actual=str(raw.get("estado_actual") or "DESCONOCIDO"),
        renovada=bool(raw.get("renovada")),
        resultado_comercial=str(raw.get("resultado_comercial") or "PENDIENTE"),
    )


def _probabilidad_base(dataset: tuple[RegistroDatasetComercialSeguro, ...], objetivo: str) -> float:
    if not dataset:
        return 0.5
    return mean(1.0 if item.resultado_comercial == objetivo else 0.0 for item in dataset)


def _probabilidad_migracion_favorable(dataset: tuple[RegistroDatasetComercialSeguro, ...]) -> float:
    if not dataset:
        return 0.5
    valores = []
    for item in dataset:
        favorable = item.clasificacion_motor == "FAVORABLE" or item.renovada
        valores.append(1.0 if favorable else 0.0)
    return mean(valores)


def _ajuste_oportunidad(oportunidad: OportunidadSeguro) -> float:
    ajuste = 0.0
    perfil = oportunidad.perfil_comercial
    evaluacion = oportunidad.evaluacion_fit
    if oportunidad.clasificacion_motor == "FAVORABLE":
        ajuste += 0.2
    if oportunidad.clasificacion_motor == "REVISION":
        ajuste -= 0.12
    if evaluacion and evaluacion.encaje_plan.value == "ALTO":
        ajuste += 0.18
    if evaluacion and evaluacion.encaje_plan.value == "BAJO":
        ajuste -= 0.2
    if perfil and perfil.sensibilidad_precio.value == "ALTA":
        ajuste -= 0.12
    if perfil and perfil.objecion_principal.value == "PRECIO_PERCIBIDO_ALTO":
        ajuste -= 0.08
    if perfil and perfil.friccion_migracion.value == "BAJA":
        ajuste += 0.1
    if perfil and perfil.friccion_migracion.value == "ALTA":
        ajuste -= 0.1
    if len(oportunidad.seguimientos) >= 3:
        ajuste -= 0.06
    return ajuste


def _motivo_prediccion(oportunidad: OportunidadSeguro) -> str:
    evaluacion = oportunidad.evaluacion_fit
    if evaluacion:
        return evaluacion.motivo_principal
    return "Sin evaluacion de fit consolidada; se usa baseline historico y estado comercial."


def _banda(score: float, confianza: float) -> BandaPropensionSeguro:
    if confianza < 0.3:
        return BandaPropensionSeguro.INCIERTA
    if score >= 0.67:
        return BandaPropensionSeguro.ALTA
    if score >= 0.45:
        return BandaPropensionSeguro.MEDIA
    return BandaPropensionSeguro.BAJA


def _siguiente_accion(
    prediccion: PrediccionComercialSeguro, prioridad: NivelPrioridadComercialSeguro
) -> AccionComercialSugerida:
    motivo = prediccion.motivo_principal.upper()
    if "ELEGIBIL" in motivo or "REVISION" in motivo:
        return AccionComercialSugerida.REVISAR_ELEGIBILIDAD_MIGRACION
    if "PRECIO" in motivo:
        return AccionComercialSugerida.REVISAR_OBJECION_PRECIO
    if prioridad is NivelPrioridadComercialSeguro.ALTA:
        return AccionComercialSugerida.INSISTIR_SEGUIMIENTO
    if prioridad is NivelPrioridadComercialSeguro.MEDIA:
        return AccionComercialSugerida.PREPARAR_MEJOR_OFERTA
    if prioridad is NivelPrioridadComercialSeguro.BAJA:
        return AccionComercialSugerida.POSPONER_Y_REEVALUAR
    return AccionComercialSugerida.NO_PRIORIZAR_POR_AHORA


def _significado_prioridad(prioridad: NivelPrioridadComercialSeguro) -> str:
    if prioridad is NivelPrioridadComercialSeguro.ALTA:
        return "Oportunidad caliente: conviene contactar primero y cerrar siguiente paso concreto."
    if prioridad is NivelPrioridadComercialSeguro.MEDIA:
        return "Oportunidad viable: necesita propuesta afinada o seguimiento planificado."
    if prioridad is NivelPrioridadComercialSeguro.BAJA:
        return "Oportunidad debil por ahora: mantener observacion activa sin sobreinvertir tiempo."
    return "No prioritaria en este ciclo: reservar esfuerzo para casos con mayor retorno esperado."


def _accion_humana(accion: AccionComercialSugerida) -> str:
    acciones = {
        AccionComercialSugerida.INSISTIR_SEGUIMIENTO: "Llamar hoy y dejar compromiso de avance en 24-48h.",
        AccionComercialSugerida.PREPARAR_MEJOR_OFERTA: "Reformular propuesta destacando valor clinico y ahorro total.",
        AccionComercialSugerida.REVISAR_OBJECION_PRECIO: "Trabajar objecion de precio con comparativa transparente.",
        AccionComercialSugerida.REVISAR_ELEGIBILIDAD_MIGRACION: "Validar elegibilidad y fricciones antes de insistir.",
        AccionComercialSugerida.POSPONER_Y_REEVALUAR: "Posponer seguimiento intensivo y revaluar con nueva senal.",
        AccionComercialSugerida.NO_PRIORIZAR_POR_AHORA: "No asignar esfuerzo comercial activo en este momento.",
    }
    return acciones[accion]


def _acotar(score: float) -> float:
    return round(min(max(score, 0.02), 0.98), 4)
