from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Protocol

from clinicdesk.app.application.seguros.comercial import GestionComercialSeguroService
from clinicdesk.app.domain.seguros import (
    EstadoOportunidadSeguro,
    OportunidadSeguro,
    RenovacionSeguro,
)


class ProveedorFecha(Protocol):
    def hoy(self) -> date: ...


class ProveedorFechaSistema:
    def hoy(self) -> date:
        return datetime.now(tz=UTC).date()


@dataclass(frozen=True, slots=True)
class MetricaFunnelSeguro:
    clave: str
    valor: int
    ratio: float | None
    riesgo_u_oportunidad: str
    accion_sugerida: str


@dataclass(frozen=True, slots=True)
class EstadoEmbudoSeguro:
    nombre: str
    total: int


@dataclass(frozen=True, slots=True)
class GrupoRenovacionSeguro:
    nombre: str
    total: int
    riesgo_u_oportunidad: str
    accion_sugerida: str


@dataclass(frozen=True, slots=True)
class CohorteSeguro:
    dimension: str
    nombre: str
    tamano: int
    tasa_conversion: float | None
    friccion_principal: str
    oportunidad_principal: str
    accion_sugerida: str


@dataclass(frozen=True, slots=True)
class InsightComercialSeguro:
    titulo: str
    lectura: str
    accion_sugerida: str


@dataclass(frozen=True, slots=True)
class CampaniaAccionableSeguro:
    id_campania: str
    titulo: str
    criterio: str
    tamano_estimado: int
    motivo: str
    accion_recomendada: str
    cautela: str
    ids_oportunidad: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ResumenEjecutivoSeguros:
    fecha_corte: date
    total_oportunidades: int
    oportunidades_abiertas: int
    convertidas: int
    rechazadas: int
    pospuestas: int
    renovaciones_pendientes: int
    renovaciones_en_riesgo: int
    ratio_conversion_global: float | None
    metrica_funnel: tuple[MetricaFunnelSeguro, ...]
    estado_embudo: tuple[EstadoEmbudoSeguro, ...]
    cohortes: tuple[CohorteSeguro, ...]
    grupos_renovacion: tuple[GrupoRenovacionSeguro, ...]
    campanias: tuple[CampaniaAccionableSeguro, ...]
    insights: tuple[InsightComercialSeguro, ...]


class AnaliticaEjecutivaSegurosService:
    _MIN_MUESTRA = 3

    def __init__(
        self,
        gestion: GestionComercialSeguroService,
        proveedor_fecha: ProveedorFecha | None = None,
    ) -> None:
        self._gestion = gestion
        self._proveedor_fecha = proveedor_fecha or ProveedorFechaSistema()

    def construir_resumen(self) -> ResumenEjecutivoSeguros:
        oportunidades = self._gestion.listar_cartera()
        renovaciones = self._gestion.listar_renovaciones_pendientes()
        estado_embudo = self._construir_estado_embudo(oportunidades)
        cohortes = self._construir_cohortes(oportunidades)
        grupos_renovacion = self._construir_grupos_renovacion(renovaciones)
        campanias = self._construir_campanias(oportunidades, renovaciones)
        metricas = self._construir_metricas_funnel(oportunidades, renovaciones)
        ratio_global = _calcular_ratio(_contar_convertidas(oportunidades), len(oportunidades), self._MIN_MUESTRA)
        return ResumenEjecutivoSeguros(
            fecha_corte=self._proveedor_fecha.hoy(),
            total_oportunidades=len(oportunidades),
            oportunidades_abiertas=_contar_abiertas(oportunidades),
            convertidas=_contar_convertidas(oportunidades),
            rechazadas=_contar_estado(oportunidades, EstadoOportunidadSeguro.RECHAZADA),
            pospuestas=_contar_estado(oportunidades, EstadoOportunidadSeguro.POSPUESTA),
            renovaciones_pendientes=len(renovaciones),
            renovaciones_en_riesgo=_contar_renovaciones_en_riesgo(renovaciones, self._proveedor_fecha.hoy()),
            ratio_conversion_global=ratio_global,
            metrica_funnel=metricas,
            estado_embudo=estado_embudo,
            cohortes=cohortes,
            grupos_renovacion=grupos_renovacion,
            campanias=campanias,
            insights=_construir_insights(metricas, cohortes),
        )

    def ids_oportunidad_por_campania(self, id_campania: str) -> tuple[str, ...]:
        for campania in self.construir_resumen().campanias:
            if campania.id_campania == id_campania:
                return campania.ids_oportunidad
        return ()

    def _construir_estado_embudo(self, oportunidades: tuple[OportunidadSeguro, ...]) -> tuple[EstadoEmbudoSeguro, ...]:
        conteo = Counter(item.estado_actual.value for item in oportunidades)
        return tuple(EstadoEmbudoSeguro(nombre=clave, total=conteo[clave]) for clave in sorted(conteo))

    def _construir_metricas_funnel(
        self,
        oportunidades: tuple[OportunidadSeguro, ...],
        renovaciones: tuple[RenovacionSeguro, ...],
    ) -> tuple[MetricaFunnelSeguro, ...]:
        total = len(oportunidades)
        return (
            _metrica(
                "oportunidades_abiertas",
                _contar_abiertas(oportunidades),
                None,
                "Carga comercial activa",
                "Priorizar cola diaria",
            ),
            _metrica(
                "convertidas",
                _contar_convertidas(oportunidades),
                _calcular_ratio(_contar_convertidas(oportunidades), total, self._MIN_MUESTRA),
                "Capacidad de cierre",
                "Replicar guiones de alta conversión",
            ),
            _metrica(
                "rechazadas",
                _contar_estado(oportunidades, EstadoOportunidadSeguro.RECHAZADA),
                _calcular_ratio(
                    _contar_estado(oportunidades, EstadoOportunidadSeguro.RECHAZADA), total, self._MIN_MUESTRA
                ),
                "Fricción comercial acumulada",
                "Revisar objeciones recurrentes",
            ),
            _metrica(
                "pospuestas",
                _contar_estado(oportunidades, EstadoOportunidadSeguro.POSPUESTA),
                _calcular_ratio(
                    _contar_estado(oportunidades, EstadoOportunidadSeguro.POSPUESTA), total, self._MIN_MUESTRA
                ),
                "Pipeline estancado",
                "Crear lotes de reactivación",
            ),
            _metrica(
                "renovaciones_pendientes",
                len(renovaciones),
                None,
                "Riesgo de fuga en cartera vigente",
                "Planificar llamadas de retención",
            ),
            _metrica(
                "renovaciones_en_riesgo",
                _contar_renovaciones_en_riesgo(renovaciones, self._proveedor_fecha.hoy()),
                None,
                "Impacto directo en ingreso recurrente",
                "Escalar revisión de renovación",
            ),
        )

    def _construir_cohortes(self, oportunidades: tuple[OportunidadSeguro, ...]) -> tuple[CohorteSeguro, ...]:
        cohortes: list[CohorteSeguro] = []
        cohortes.extend(
            self._cohortes_por_dimension(
                oportunidades, "segmento", lambda item: _valor_perfil(item, "segmento_cliente")
            )
        )
        cohortes.extend(self._cohortes_por_dimension(oportunidades, "plan", lambda item: item.plan_destino_id))
        cohortes.extend(
            self._cohortes_por_dimension(
                oportunidades,
                "fit",
                lambda item: item.evaluacion_fit.encaje_plan.value if item.evaluacion_fit else "SIN_FIT",
            )
        )
        cohortes.extend(
            self._cohortes_por_dimension(
                oportunidades, "objecion", lambda item: _valor_perfil(item, "objecion_principal")
            )
        )
        cohortes.extend(
            self._cohortes_por_dimension(
                oportunidades, "sensibilidad", lambda item: _valor_perfil(item, "sensibilidad_precio")
            )
        )
        cohortes.extend(
            self._cohortes_por_dimension(oportunidades, "origen", lambda item: _valor_perfil(item, "origen_cliente"))
        )
        return tuple(sorted(cohortes, key=lambda item: (item.dimension, -item.tamano, item.nombre))[:14])

    def _cohortes_por_dimension(
        self, oportunidades: tuple[OportunidadSeguro, ...], dimension: str, selector
    ) -> tuple[CohorteSeguro, ...]:
        grupos: dict[str, list[OportunidadSeguro]] = defaultdict(list)
        for oportunidad in oportunidades:
            grupos[selector(oportunidad)].append(oportunidad)
        resultado: list[CohorteSeguro] = []
        for nombre, items in grupos.items():
            conversiones = _contar_convertidas(tuple(items))
            resultado.append(
                CohorteSeguro(
                    dimension=dimension,
                    nombre=nombre,
                    tamano=len(items),
                    tasa_conversion=_calcular_ratio(conversiones, len(items), self._MIN_MUESTRA),
                    friccion_principal=_friccion_principal(tuple(items)),
                    oportunidad_principal=_oportunidad_principal(tuple(items)),
                    accion_sugerida=_accion_por_cohorte(dimension, nombre),
                )
            )
        return tuple(sorted(resultado, key=lambda item: item.tamano, reverse=True)[:2])

    def _construir_grupos_renovacion(
        self, renovaciones: tuple[RenovacionSeguro, ...]
    ) -> tuple[GrupoRenovacionSeguro, ...]:
        riesgo = _contar_renovaciones_en_riesgo(renovaciones, self._proveedor_fecha.hoy())
        return (
            GrupoRenovacionSeguro(
                "pendientes",
                len(renovaciones),
                "Backlog de renovación en curso",
                "Asignar agenda semanal de seguimiento",
            ),
            GrupoRenovacionSeguro(
                "en_riesgo",
                riesgo,
                "Renovaciones con fecha próxima o vencida",
                "Activar lote de retención y revisión de oferta",
            ),
        )

    def _construir_campanias(
        self,
        oportunidades: tuple[OportunidadSeguro, ...],
        renovaciones: tuple[RenovacionSeguro, ...],
    ) -> tuple[CampaniaAccionableSeguro, ...]:
        return (
            _campania_alta_conversion_pendiente(oportunidades),
            _campania_sensibles_precio(oportunidades),
            _campania_renovacion_en_riesgo(oportunidades, renovaciones, self._proveedor_fecha.hoy()),
            _campania_fit_alto_estancadas(oportunidades),
        )


def _metrica(clave: str, valor: int, ratio: float | None, riesgo: str, accion: str) -> MetricaFunnelSeguro:
    return MetricaFunnelSeguro(
        clave=clave, valor=valor, ratio=ratio, riesgo_u_oportunidad=riesgo, accion_sugerida=accion
    )


def _contar_estado(oportunidades: tuple[OportunidadSeguro, ...], estado: EstadoOportunidadSeguro) -> int:
    return sum(1 for item in oportunidades if item.estado_actual is estado)


def _contar_convertidas(oportunidades: tuple[OportunidadSeguro, ...]) -> int:
    estados = {
        EstadoOportunidadSeguro.CONVERTIDA,
        EstadoOportunidadSeguro.PENDIENTE_RENOVACION,
        EstadoOportunidadSeguro.RENOVADA,
    }
    return sum(1 for item in oportunidades if item.estado_actual in estados)


def _contar_abiertas(oportunidades: tuple[OportunidadSeguro, ...]) -> int:
    cerradas = {
        EstadoOportunidadSeguro.RECHAZADA,
        EstadoOportunidadSeguro.RENOVADA,
        EstadoOportunidadSeguro.NO_RENOVADA,
    }
    return sum(1 for item in oportunidades if item.estado_actual not in cerradas)


def _calcular_ratio(numerador: int, denominador: int, umbral: int) -> float | None:
    if denominador < umbral or denominador == 0:
        return None
    return round(numerador / denominador, 4)


def _valor_perfil(oportunidad: OportunidadSeguro, atributo: str) -> str:
    if oportunidad.perfil_comercial is None:
        return "SIN_PERFIL"
    valor = getattr(oportunidad.perfil_comercial, atributo)
    return valor.value if hasattr(valor, "value") else str(valor)


def _friccion_principal(oportunidades: tuple[OportunidadSeguro, ...]) -> str:
    objeciones = Counter(_valor_perfil(item, "objecion_principal") for item in oportunidades)
    return objeciones.most_common(1)[0][0] if objeciones else "SIN_DATO"


def _oportunidad_principal(oportunidades: tuple[OportunidadSeguro, ...]) -> str:
    conversiones = _contar_convertidas(oportunidades)
    return "Alta probabilidad de cierre" if conversiones >= 2 else "Requiere nurturing comercial"


def _accion_por_cohorte(dimension: str, nombre: str) -> str:
    if dimension == "objecion" and nombre == "PRECIO_PERCIBIDO_ALTO":
        return "Reforzar argumentario de valor clínico"
    if dimension == "sensibilidad" and nombre == "ALTA":
        return "Priorizar propuestas con ahorro anual"
    if dimension == "fit" and nombre == "ALTO":
        return "Asignar seguimiento de cierre en 48h"
    return "Planificar lote comercial específico"


def _contar_renovaciones_en_riesgo(renovaciones: tuple[RenovacionSeguro, ...], hoy: date) -> int:
    return sum(1 for item in renovaciones if item.revision_pendiente and (item.fecha_renovacion - hoy).days <= 21)


def _ids_por_estado(
    oportunidades: tuple[OportunidadSeguro, ...], estados: set[EstadoOportunidadSeguro]
) -> tuple[str, ...]:
    return tuple(item.id_oportunidad for item in oportunidades if item.estado_actual in estados)


def _campania_alta_conversion_pendiente(oportunidades: tuple[OportunidadSeguro, ...]) -> CampaniaAccionableSeguro:
    ids = tuple(
        item.id_oportunidad
        for item in oportunidades
        if item.evaluacion_fit
        and item.evaluacion_fit.encaje_plan.value == "ALTO"
        and item.estado_actual is EstadoOportunidadSeguro.EN_SEGUIMIENTO
    )
    return CampaniaAccionableSeguro(
        id_campania="campania_fit_alto_seguimiento",
        titulo="Seguimiento de fit alto sin cierre",
        criterio="Fit ALTO + estado EN_SEGUIMIENTO",
        tamano_estimado=len(ids),
        motivo="Hay valor claro sin cierre inmediato",
        accion_recomendada="Agendar contacto prioritario y cierre guiado",
        cautela="No forzar cierre si persiste objeción crítica",
        ids_oportunidad=ids,
    )


def _campania_sensibles_precio(oportunidades: tuple[OportunidadSeguro, ...]) -> CampaniaAccionableSeguro:
    ids = tuple(
        item.id_oportunidad
        for item in oportunidades
        if _valor_perfil(item, "sensibilidad_precio") == "ALTA"
        and item.estado_actual in {EstadoOportunidadSeguro.OFERTA_ENVIADA, EstadoOportunidadSeguro.EN_SEGUIMIENTO}
    )
    return CampaniaAccionableSeguro(
        id_campania="campania_precio_argumento",
        titulo="Sensibles a precio con oferta activa",
        criterio="Sensibilidad ALTA + oferta enviada/seguimiento",
        tamano_estimado=len(ids),
        motivo="Riesgo de rechazo por precio percibido",
        accion_recomendada="Activar argumentario coste-beneficio y alternativas de plan",
        cautela="Evitar descuentos indiscriminados sin validar margen",
        ids_oportunidad=ids,
    )


def _campania_renovacion_en_riesgo(
    oportunidades: tuple[OportunidadSeguro, ...], renovaciones: tuple[RenovacionSeguro, ...], hoy: date
) -> CampaniaAccionableSeguro:
    ids_riesgo = {
        item.id_oportunidad
        for item in renovaciones
        if item.revision_pendiente and (item.fecha_renovacion - hoy).days <= 21
    }
    ids = tuple(item.id_oportunidad for item in oportunidades if item.id_oportunidad in ids_riesgo)
    return CampaniaAccionableSeguro(
        id_campania="campania_renovacion_riesgo",
        titulo="Renovaciones críticas de la semana",
        criterio="Renovación pendiente con fecha <= 21 días",
        tamano_estimado=len(ids),
        motivo="Impacto directo en cartera vigente",
        accion_recomendada="Priorizar revisión de permanencia y contraoferta",
        cautela="Confirmar datos contractuales antes de compromiso",
        ids_oportunidad=ids,
    )


def _campania_fit_alto_estancadas(oportunidades: tuple[OportunidadSeguro, ...]) -> CampaniaAccionableSeguro:
    ids = _ids_por_estado(oportunidades, {EstadoOportunidadSeguro.POSPUESTA, EstadoOportunidadSeguro.OFERTA_PREPARADA})
    return CampaniaAccionableSeguro(
        id_campania="campania_estancadas",
        titulo="Oportunidades estancadas con potencial",
        criterio="Estado POSPUESTA u OFERTA_PREPARADA",
        tamano_estimado=len(ids),
        motivo="Existe oportunidad pero sin avance reciente",
        accion_recomendada="Lanzar lote de reactivación comercial",
        cautela="No contar como pipeline caliente hasta contacto efectivo",
        ids_oportunidad=ids,
    )


def _construir_insights(
    metricas: tuple[MetricaFunnelSeguro, ...],
    cohortes: tuple[CohorteSeguro, ...],
) -> tuple[InsightComercialSeguro, ...]:
    insight_metricas = next((item for item in metricas if item.clave == "pospuestas"), None)
    insight_cohorte = next((item for item in cohortes if item.dimension == "objecion"), None)
    resultado: list[InsightComercialSeguro] = []
    if insight_metricas:
        resultado.append(
            InsightComercialSeguro(
                titulo="Atasco principal del funnel",
                lectura=f"Casos pospuestos: {insight_metricas.valor}",
                accion_sugerida="Trabajar lote de reactivación y seguimiento.",
            )
        )
    if insight_cohorte:
        resultado.append(
            InsightComercialSeguro(
                titulo="Objeción dominante",
                lectura=f"{insight_cohorte.nombre} en {insight_cohorte.tamano} oportunidades",
                accion_sugerida=insight_cohorte.accion_sugerida,
            )
        )
    return tuple(resultado)
