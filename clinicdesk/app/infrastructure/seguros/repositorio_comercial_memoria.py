from __future__ import annotations

from clinicdesk.app.domain.seguros.comercial import (
    OfertaSeguro,
    OportunidadSeguro,
    RenovacionSeguro,
    ResultadoRenovacionSeguro,
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
