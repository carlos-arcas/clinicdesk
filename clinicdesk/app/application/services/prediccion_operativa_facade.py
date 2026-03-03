from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from clinicdesk.app.application.prediccion_operativa.agenda import ObtenerEstimacionesAgenda
from clinicdesk.app.application.prediccion_operativa.usecases import (
    ComprobarDatosPrediccionOperativa,
    EntrenarPrediccionOperativa,
    ListarProximasCitasOperativas,
    ObtenerExplicacionPrediccionOperativa,
    ObtenerSaludPrediccionOperativa,
    PrevisualizarPrediccionOperativa,
)


@dataclass(slots=True)
class PrediccionOperativaFacade:
    comprobar_duracion_uc: ComprobarDatosPrediccionOperativa
    entrenar_duracion_uc: EntrenarPrediccionOperativa
    previsualizar_duracion_uc: PrevisualizarPrediccionOperativa
    salud_duracion_uc: ObtenerSaludPrediccionOperativa
    explicar_duracion_uc: ObtenerExplicacionPrediccionOperativa
    comprobar_espera_uc: ComprobarDatosPrediccionOperativa
    entrenar_espera_uc: EntrenarPrediccionOperativa
    previsualizar_espera_uc: PrevisualizarPrediccionOperativa
    salud_espera_uc: ObtenerSaludPrediccionOperativa
    explicar_espera_uc: ObtenerExplicacionPrediccionOperativa
    agenda_uc: ObtenerEstimacionesAgenda
    listar_proximas_citas_uc: ListarProximasCitasOperativas
    cerrar_conexion_hilo_actual: Callable[[], None] | None = None

    def obtener_estimaciones_agenda(self) -> tuple[dict[int, str], dict[int, str]]:
        return self.agenda_uc.ejecutar()

    def obtener_salud_duracion(self):
        return self.salud_duracion_uc.ejecutar()

    def obtener_salud_espera(self):
        return self.salud_espera_uc.ejecutar()

    def obtener_explicacion_duracion(self, cita_id: int, nivel: str):
        return self.explicar_duracion_uc.ejecutar(cita_id, nivel)

    def obtener_explicacion_espera(self, cita_id: int, nivel: str):
        return self.explicar_espera_uc.ejecutar(cita_id, nivel)
