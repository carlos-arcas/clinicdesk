from __future__ import annotations

from clinicdesk.app.application.seguros.comercial import FiltroCarteraSeguro
from clinicdesk.app.domain.seguros.comercial import (
    OfertaSeguro,
    OportunidadSeguro,
    RenovacionSeguro,
    ResultadoRenovacionSeguro,
    SeguimientoOportunidadSeguro,
)
from clinicdesk.app.domain.seguros.cola_operativa import GestionOperativaColaSeguro


class RepositorioComercialSeguroMemoria:
    def __init__(self) -> None:
        self._oportunidades: dict[str, OportunidadSeguro] = {}
        self._ofertas: dict[str, OfertaSeguro] = {}
        self._renovaciones: dict[str, RenovacionSeguro] = {}
        self._gestiones: dict[str, list[GestionOperativaColaSeguro]] = {}

    def guardar_oportunidad(self, oportunidad: OportunidadSeguro) -> None:
        self._oportunidades[oportunidad.id_oportunidad] = oportunidad

    def obtener_oportunidad(self, id_oportunidad: str) -> OportunidadSeguro:
        return self._oportunidades[id_oportunidad]

    def guardar_oferta(self, oferta: OfertaSeguro) -> None:
        self._ofertas[oferta.id_oportunidad] = oferta

    def obtener_oferta_por_oportunidad(self, id_oportunidad: str) -> OfertaSeguro | None:
        return self._ofertas.get(id_oportunidad)

    def guardar_renovacion(self, renovacion: RenovacionSeguro) -> None:
        self._renovaciones[renovacion.id_oportunidad] = renovacion

    def listar_renovaciones_pendientes(self) -> tuple[RenovacionSeguro, ...]:
        pendientes = [
            item
            for item in self._renovaciones.values()
            if item.revision_pendiente and item.resultado is ResultadoRenovacionSeguro.PENDIENTE
        ]
        return tuple(sorted(pendientes, key=lambda item: item.fecha_renovacion))

    def listar_oportunidades(self, filtro: FiltroCarteraSeguro) -> tuple[OportunidadSeguro, ...]:
        items = list(self._oportunidades.values())
        if filtro.estado:
            items = [item for item in items if item.estado_actual is filtro.estado]
        if filtro.plan_destino_id:
            items = [item for item in items if item.plan_destino_id == filtro.plan_destino_id]
        if filtro.clasificacion_migracion:
            items = [item for item in items if item.clasificacion_motor == filtro.clasificacion_migracion]
        if filtro.solo_renovacion_pendiente:
            ids = {item.id_oportunidad for item in self.listar_renovaciones_pendientes()}
            items = [item for item in items if item.id_oportunidad in ids]
        return tuple(items)

    def listar_seguimientos_recientes(self, limite: int = 20) -> tuple[SeguimientoOportunidadSeguro, ...]:
        todos: list[SeguimientoOportunidadSeguro] = []
        for oportunidad in self._oportunidades.values():
            todos.extend(oportunidad.seguimientos)
        todos.sort(key=lambda item: item.fecha_registro, reverse=True)
        return tuple(todos[:limite])

    def listar_historial_oportunidad(self, id_oportunidad: str) -> tuple[SeguimientoOportunidadSeguro, ...]:
        return self._oportunidades[id_oportunidad].seguimientos

    def listar_oportunidades_por_gestion_operativa(self) -> tuple[OportunidadSeguro, ...]:
        activos = {
            "DETECTADA",
            "ANALIZADA",
            "ELEGIBLE",
            "OFERTA_PREPARADA",
            "OFERTA_ENVIADA",
            "EN_SEGUIMIENTO",
            "CONVERTIDA",
            "POSPUESTA",
            "PENDIENTE_RENOVACION",
        }
        return tuple(item for item in self._oportunidades.values() if item.estado_actual.value in activos)

    def guardar_gestion_operativa(self, gestion: GestionOperativaColaSeguro) -> None:
        self._gestiones.setdefault(gestion.id_oportunidad, []).append(gestion)

    def obtener_ultima_gestion_operativa(self, id_oportunidad: str) -> GestionOperativaColaSeguro | None:
        historial = self._gestiones.get(id_oportunidad, [])
        return historial[-1] if historial else None

    def listar_gestiones_operativas(
        self, id_oportunidad: str, limite: int = 5
    ) -> tuple[GestionOperativaColaSeguro, ...]:
        historial = self._gestiones.get(id_oportunidad, [])
        return tuple(historial[-limite:])

    def construir_dataset_ml_comercial(self) -> list[dict[str, object]]:
        resultado: list[dict[str, object]] = []
        for oportunidad in self._oportunidades.values():
            perfil = oportunidad.perfil_comercial
            evaluacion = oportunidad.evaluacion_fit
            resultado.append(
                {
                    "id_oportunidad": oportunidad.id_oportunidad,
                    "plan_origen_id": oportunidad.plan_origen_id,
                    "plan_destino_id": oportunidad.plan_destino_id,
                    "clasificacion_motor": oportunidad.clasificacion_motor,
                    "estado_actual": oportunidad.estado_actual.value,
                    "segmento_cliente": perfil.segmento_cliente.value if perfil else None,
                    "origen_cliente": perfil.origen_cliente.value if perfil else None,
                    "necesidad_principal": perfil.necesidad_principal.value if perfil else None,
                    "objecion_principal": perfil.objecion_principal.value if perfil else None,
                    "sensibilidad_precio": perfil.sensibilidad_precio.value if perfil else None,
                    "friccion_migracion": perfil.friccion_migracion.value if perfil else None,
                    "fit_comercial": evaluacion.encaje_plan.value if evaluacion else None,
                    "fit_motivo": evaluacion.motivo_principal if evaluacion else None,
                    "resultado_comercial": oportunidad.resultado_comercial.value
                    if oportunidad.resultado_comercial
                    else None,
                    "dias_ciclo": len(oportunidad.seguimientos),
                    "total_seguimientos": len(oportunidad.seguimientos),
                    "renovada": False,
                }
            )
        return resultado
