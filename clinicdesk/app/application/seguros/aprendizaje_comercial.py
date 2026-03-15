from __future__ import annotations

from collections import defaultdict

from clinicdesk.app.application.seguros.aprendizaje_contratos import (
    EfectividadCampaniaSeguro,
    InsightArgumentoSeguro,
    InsightPlanSeguro,
    InsightSegmentoSeguro,
    MetricaAprendizajeComercialSeguro,
    PanelAprendizajeComercialSeguro,
    PlaybookComercialSeguro,
    RecomendacionCampaniaSeguro,
)
from clinicdesk.app.application.seguros.campanias import GestionCampaniasSeguroService
from clinicdesk.app.application.seguros.comercial import GestionComercialSeguroService
from clinicdesk.app.domain.seguros import CampaniaSeguro, EstadoOportunidadSeguro, OportunidadSeguro


class AprendizajeComercialSegurosService:
    def __init__(
        self,
        gestion: GestionComercialSeguroService,
        campanias: GestionCampaniasSeguroService,
        muestra_minima: int = 3,
    ) -> None:
        self._gestion = gestion
        self._campanias = campanias
        self._muestra_minima = muestra_minima

    def construir_panel(self) -> PanelAprendizajeComercialSeguro:
        oportunidades = self._gestion.listar_cartera()
        return PanelAprendizajeComercialSeguro(
            efectividad_campanias=self._efectividad_campanias(),
            insights_segmentos=self._insights_segmento(oportunidades),
            insights_argumentos=self._insights_argumento(oportunidades),
            insights_planes=self._insights_plan(oportunidades),
            playbooks=self._playbooks(oportunidades),
            recomendaciones_campania=self._recomendaciones_campania(oportunidades),
        )

    def _efectividad_campanias(self) -> tuple[EfectividadCampaniaSeguro, ...]:
        resultado: list[EfectividadCampaniaSeguro] = []
        for campania in self._campanias.listar_campanias():
            muestra = campania.resultado_agregado.trabajados
            ratio = _ratio(campania.resultado_agregado.convertidos, muestra, self._muestra_minima)
            resultado.append(
                EfectividadCampaniaSeguro(
                    id_campania=campania.id_campania,
                    nombre_campania=campania.nombre,
                    poblacion_analizada=f"lote:{campania.tamano_lote}",
                    tamano_muestra=muestra,
                    metrica_principal=ratio,
                    senal_efectividad=_clasificar_campania(campania, ratio, self._muestra_minima),
                    cautela_muestral=_cautela(muestra, self._muestra_minima),
                    accion_recomendada=_accion_campania(campania, ratio, self._muestra_minima),
                )
            )
        return tuple(sorted(resultado, key=lambda item: (-item.tamano_muestra, item.id_campania)))

    def _insights_segmento(self, oportunidades: tuple[OportunidadSeguro, ...]) -> tuple[InsightSegmentoSeguro, ...]:
        resultado: list[InsightSegmentoSeguro] = []
        resultado.extend(
            self._insight_por_eje(oportunidades, "segmento", lambda item: _valor_perfil(item, "segmento_cliente"))
        )
        resultado.extend(
            self._insight_por_eje(oportunidades, "objecion", lambda item: _valor_perfil(item, "objecion_principal"))
        )
        resultado.extend(
            self._insight_por_eje(
                oportunidades, "sensibilidad", lambda item: _valor_perfil(item, "sensibilidad_precio")
            )
        )
        resultado.extend(
            self._insight_por_eje(
                oportunidades,
                "fit",
                lambda item: item.evaluacion_fit.encaje_plan.value if item.evaluacion_fit else "SIN_FIT",
            )
        )
        resultado.extend(
            self._insight_por_eje(oportunidades, "origen", lambda item: _valor_perfil(item, "origen_cliente"))
        )
        return tuple(sorted(resultado, key=lambda item: (item.eje, -item.tamano_muestra, item.valor))[:10])

    def _insight_por_eje(
        self, oportunidades: tuple[OportunidadSeguro, ...], eje: str, selector
    ) -> list[InsightSegmentoSeguro]:
        grupos: dict[str, list[OportunidadSeguro]] = defaultdict(list)
        for oportunidad in oportunidades:
            grupos[selector(oportunidad)].append(oportunidad)
        insights: list[InsightSegmentoSeguro] = []
        for valor, items in grupos.items():
            muestra = len(items)
            ratio = _ratio(_contar_convertidas(tuple(items)), muestra, self._muestra_minima)
            insights.append(_crear_insight_segmento(eje, valor, muestra, ratio, self._muestra_minima))
        return sorted(insights, key=lambda item: item.tamano_muestra, reverse=True)[:2]

    def _insights_argumento(self, oportunidades: tuple[OportunidadSeguro, ...]) -> tuple[InsightArgumentoSeguro, ...]:
        grupos: dict[tuple[str, str], list[OportunidadSeguro]] = defaultdict(list)
        for oportunidad in oportunidades:
            grupos[(_valor_perfil(oportunidad, "segmento_cliente"), _argumento_principal(oportunidad))].append(
                oportunidad
            )
        return tuple(_crear_insights_argumento(grupos, self._muestra_minima))

    def _insights_plan(self, oportunidades: tuple[OportunidadSeguro, ...]) -> tuple[InsightPlanSeguro, ...]:
        grupos: dict[tuple[str, str], list[OportunidadSeguro]] = defaultdict(list)
        for oportunidad in oportunidades:
            grupos[(_valor_perfil(oportunidad, "segmento_cliente"), oportunidad.plan_destino_id)].append(oportunidad)
        return tuple(_crear_insights_plan(grupos, self._muestra_minima))

    def _playbooks(self, oportunidades: tuple[OportunidadSeguro, ...]) -> tuple[PlaybookComercialSeguro, ...]:
        return tuple(
            _crear_playbooks(
                oportunidades,
                self._insights_argumento(oportunidades),
                self._insights_plan(oportunidades),
                self._muestra_minima,
            )
        )

    def _recomendaciones_campania(
        self, oportunidades: tuple[OportunidadSeguro, ...]
    ) -> tuple[RecomendacionCampaniaSeguro, ...]:
        return tuple(_crear_recomendaciones(oportunidades, self._playbooks(oportunidades), self._muestra_minima))


def _crear_insight_segmento(
    eje: str, valor: str, muestra: int, ratio: float | None, muestra_minima: int
) -> InsightSegmentoSeguro:
    return InsightSegmentoSeguro(
        eje=eje,
        valor=valor,
        poblacion_analizada=f"{eje}:{valor}",
        tamano_muestra=muestra,
        metrica_principal=ratio,
        senal_efectividad=_senal_ratio(ratio, muestra, muestra_minima),
        cautela_muestral=_cautela(muestra, muestra_minima),
        accion_recomendada=f"Priorizar guion para {eje}={valor}",
    )


def _crear_insights_argumento(
    grupos: dict[tuple[str, str], list[OportunidadSeguro]], muestra_minima: int
) -> list[InsightArgumentoSeguro]:
    resultado: list[InsightArgumentoSeguro] = []
    for (segmento, argumento), items in grupos.items():
        muestra = len(items)
        ratio = _ratio(_contar_convertidas(tuple(items)), muestra, muestra_minima)
        resultado.append(
            InsightArgumentoSeguro(
                segmento=segmento,
                argumento=argumento,
                poblacion_analizada=f"segmento:{segmento}",
                tamano_muestra=muestra,
                metrica_principal=ratio,
                senal_efectividad=_senal_ratio(ratio, muestra, muestra_minima),
                cautela_muestral=_cautela(muestra, muestra_minima),
                accion_recomendada="Repetir argumento en siguientes lotes" if ratio else "Capturar más ejecuciones",
            )
        )
    return sorted(resultado, key=lambda item: (-item.tamano_muestra, item.segmento))[:6]


def _crear_insights_plan(
    grupos: dict[tuple[str, str], list[OportunidadSeguro]], muestra_minima: int
) -> list[InsightPlanSeguro]:
    resultado: list[InsightPlanSeguro] = []
    for (segmento, plan), items in grupos.items():
        muestra = len(items)
        ratio = _ratio(_contar_convertidas(tuple(items)), muestra, muestra_minima)
        resultado.append(
            InsightPlanSeguro(
                segmento=segmento,
                plan_propuesto_id=plan,
                poblacion_analizada=f"segmento:{segmento}",
                tamano_muestra=muestra,
                metrica_principal=ratio,
                senal_efectividad=_senal_ratio(ratio, muestra, muestra_minima),
                cautela_muestral=_cautela(muestra, muestra_minima),
                accion_recomendada="Mantener plan en playbook" if ratio else "Validar oferta alternativa",
            )
        )
    return sorted(resultado, key=lambda item: (-item.tamano_muestra, item.segmento))[:6]


def _crear_playbooks(
    oportunidades: tuple[OportunidadSeguro, ...],
    insights_argumento: tuple[InsightArgumentoSeguro, ...],
    insights_plan: tuple[InsightPlanSeguro, ...],
    muestra_minima: int,
) -> list[PlaybookComercialSeguro]:
    mejores_argumentos = {item.segmento: item for item in insights_argumento if item.metrica_principal is not None}
    mejores_planes = {item.segmento: item for item in insights_plan if item.metrica_principal is not None}
    segmentos = sorted(set(mejores_argumentos) | set(mejores_planes))
    playbooks: list[PlaybookComercialSeguro] = []
    for segmento in segmentos:
        insight_argumento = mejores_argumentos.get(segmento)
        insight_plan = mejores_planes.get(segmento)
        playbooks.append(
            PlaybookComercialSeguro(
                segmento_objetivo=segmento,
                plan_sugerido=insight_plan.plan_propuesto_id if insight_plan else "SIN_BASE",
                argumento_principal=insight_argumento.argumento if insight_argumento else "SIN_BASE",
                objecion_a_vigilar=_objecion_segmento(oportunidades, segmento),
                siguiente_accion_sugerida="Ejecutar lote y registrar resultado por ítem",
                cautela_muestral=insight_argumento.cautela_muestral
                if insight_argumento
                else _cautela(0, muestra_minima),
            )
        )
    return playbooks[:4]


def _crear_recomendaciones(
    oportunidades: tuple[OportunidadSeguro, ...], playbooks: tuple[PlaybookComercialSeguro, ...], muestra_minima: int
) -> list[RecomendacionCampaniaSeguro]:
    recomendaciones: list[RecomendacionCampaniaSeguro] = []
    for playbook in playbooks:
        muestra = _tamano_segmento(oportunidades, playbook.segmento_objetivo)
        recomendaciones.append(
            RecomendacionCampaniaSeguro(
                segmento=playbook.segmento_objetivo,
                campania_recomendada=f"reactivacion_{playbook.segmento_objetivo.lower()}",
                metrica_base=MetricaAprendizajeComercialSeguro(
                    poblacion_analizada=playbook.segmento_objetivo,
                    tamano_muestra=muestra,
                    metrica_principal=_ratio(
                        _conversiones_segmento(oportunidades, playbook.segmento_objetivo), muestra, muestra_minima
                    ),
                    senal_efectividad="repetir"
                    if "insuficiente" not in playbook.cautela_muestral.lower()
                    else "validar",
                    cautela_muestral=playbook.cautela_muestral,
                    accion_recomendada=playbook.siguiente_accion_sugerida,
                ),
            )
        )
    return recomendaciones


def _valor_perfil(oportunidad: OportunidadSeguro, atributo: str) -> str:
    if oportunidad.perfil_comercial is None:
        return "SIN_PERFIL"
    valor = getattr(oportunidad.perfil_comercial, atributo)
    return valor.value if hasattr(valor, "value") else str(valor)


def _contar_convertidas(oportunidades: tuple[OportunidadSeguro, ...]) -> int:
    estados = {
        EstadoOportunidadSeguro.CONVERTIDA,
        EstadoOportunidadSeguro.PENDIENTE_RENOVACION,
        EstadoOportunidadSeguro.RENOVADA,
    }
    return sum(1 for item in oportunidades if item.estado_actual in estados)


def _ratio(convertidos: int, muestra: int, muestra_minima: int) -> float | None:
    if muestra < muestra_minima or muestra == 0:
        return None
    return round(convertidos / muestra, 4)


def _cautela(muestra: int, muestra_minima: int) -> str:
    return f"Muestra insuficiente (<{muestra_minima})" if muestra < muestra_minima else "Muestra aceptable"


def _senal_ratio(ratio: float | None, muestra: int, muestra_minima: int) -> str:
    if muestra < muestra_minima:
        return "muestra_insuficiente"
    if ratio is None:
        return "sin_senal"
    if ratio >= 0.45:
        return "prometedora"
    if ratio >= 0.25:
        return "razonable"
    return "floja"


def _clasificar_campania(campania: CampaniaSeguro, ratio: float | None, muestra_minima: int) -> str:
    return _senal_ratio(ratio, campania.resultado_agregado.trabajados, muestra_minima)


def _accion_campania(campania: CampaniaSeguro, ratio: float | None, muestra_minima: int) -> str:
    senal = _clasificar_campania(campania, ratio, muestra_minima)
    if senal == "prometedora":
        return "Escalar segmento y repetir argumentario"
    if senal == "razonable":
        return "Iterar guion y continuar seguimiento"
    if senal == "floja":
        return "Replantear público y propuesta de valor"
    return "Capturar más resultados antes de decidir"


def _argumento_principal(oportunidad: OportunidadSeguro) -> str:
    if oportunidad.evaluacion_fit and oportunidad.evaluacion_fit.argumentos_valor:
        return oportunidad.evaluacion_fit.argumentos_valor[0]
    return oportunidad.seguimientos[-1].accion_comercial if oportunidad.seguimientos else "SIN_ARGUMENTO"


def _objecion_segmento(oportunidades: tuple[OportunidadSeguro, ...], segmento: str) -> str:
    conteo: dict[str, int] = defaultdict(int)
    for oportunidad in oportunidades:
        if _valor_perfil(oportunidad, "segmento_cliente") == segmento:
            conteo[_valor_perfil(oportunidad, "objecion_principal")] += 1
    return max(conteo.items(), key=lambda item: item[1])[0] if conteo else "SIN_BASE"


def _tamano_segmento(oportunidades: tuple[OportunidadSeguro, ...], segmento: str) -> int:
    return sum(1 for item in oportunidades if _valor_perfil(item, "segmento_cliente") == segmento)


def _conversiones_segmento(oportunidades: tuple[OportunidadSeguro, ...], segmento: str) -> int:
    seleccion = tuple(item for item in oportunidades if _valor_perfil(item, "segmento_cliente") == segmento)
    return _contar_convertidas(seleccion)
