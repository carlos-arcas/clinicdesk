from __future__ import annotations

from clinicdesk.app.application.seguros.comercial import FiltroCarteraSeguro
from clinicdesk.app.domain.seguros.comercial import (
    OfertaSeguro,
    OportunidadSeguro,
    RenovacionSeguro,
    ResultadoRenovacionSeguro,
    SeguimientoOportunidadSeguro,
)


class RepositorioComercialSeguroMemoria:
    def __init__(self) -> None:
        self._oportunidades: dict[str, OportunidadSeguro] = {}
        self._ofertas: dict[str, OfertaSeguro] = {}
        self._renovaciones: dict[str, RenovacionSeguro] = {}

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
