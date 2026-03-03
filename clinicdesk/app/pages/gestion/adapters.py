from __future__ import annotations

from clinicdesk.app.container import AppContainer


class PrediccionAusenciasGestionAdapter:
    def __init__(self, container: AppContainer) -> None:
        self._facade = container.prediccion_ausencias_facade

    def obtener_salud(self) -> str:
        return self._facade.obtener_salud_uc.ejecutar().estado

    def obtener_riesgo(self, citas: tuple) -> dict[int, str]:
        return self._facade.obtener_riesgo_agenda_uc.ejecutar(citas)


class PrediccionOperativaGestionAdapter:
    def __init__(self, container: AppContainer) -> None:
        self._facade = container.prediccion_operativa_facade

    def obtener_salud_duracion(self) -> str:
        return self._facade.obtener_salud_duracion().estado

    def obtener_salud_espera(self) -> str:
        return self._facade.obtener_salud_espera().estado

    def obtener_estimaciones_agenda(self) -> tuple[dict[int, str], dict[int, str]]:
        return self._facade.obtener_estimaciones_agenda()
