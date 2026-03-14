from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.seguros.analisis_migracion import (
    ResultadoComparacionSeguro,
    ResultadoSimulacionMigracionSeguro,
)
from clinicdesk.app.application.seguros.analisis_migracion import comparar_planes, simular_migracion
from clinicdesk.app.application.seguros.catalogo_planes import CatalogoPlanesSeguro
from clinicdesk.app.domain.seguros import PerfilCandidatoSeguro


@dataclass(frozen=True, slots=True)
class SolicitudAnalisisMigracionSeguro:
    plan_origen_id: str
    plan_destino_id: str
    edad: int | None
    residencia_pais: str | None
    historial_impagos: bool | None
    preexistencias_graves: bool | None


@dataclass(frozen=True, slots=True)
class RespuestaAnalisisMigracionSeguro:
    comparacion: ResultadoComparacionSeguro
    simulacion: ResultadoSimulacionMigracionSeguro


class AnalizarMigracionSeguroUseCase:
    def __init__(self, catalogo: CatalogoPlanesSeguro) -> None:
        self._catalogo = catalogo

    def execute(self, solicitud: SolicitudAnalisisMigracionSeguro) -> RespuestaAnalisisMigracionSeguro:
        origen = self._catalogo.obtener_por_id(solicitud.plan_origen_id)
        destino = self._catalogo.obtener_por_id(solicitud.plan_destino_id)
        perfil = PerfilCandidatoSeguro(
            edad=solicitud.edad,
            residencia_pais=solicitud.residencia_pais,
            historial_impagos=solicitud.historial_impagos,
            preexistencias_graves=solicitud.preexistencias_graves,
        )
        comparacion = comparar_planes(origen, destino)
        simulacion = simular_migracion(origen, destino, perfil)
        return RespuestaAnalisisMigracionSeguro(comparacion=comparacion, simulacion=simulacion)
