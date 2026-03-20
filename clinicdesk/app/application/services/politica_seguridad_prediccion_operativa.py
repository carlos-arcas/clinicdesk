from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.security import Action, AutorizadorAcciones, UserContext


@dataclass(frozen=True, slots=True)
class DecisionPermisoPrediccionOperativa:
    permitido: bool
    accion: Action
    motivo_i18n: str | None = None


@dataclass(slots=True)
class PoliticaSeguridadPrediccionOperativa:
    autorizador: AutorizadorAcciones
    contexto_usuario: UserContext

    def decidir_entrenamiento(self) -> DecisionPermisoPrediccionOperativa:
        permitido = self.autorizador.puede(self.contexto_usuario, Action.ML_ENTRENAR)
        return DecisionPermisoPrediccionOperativa(
            permitido=permitido,
            accion=Action.ML_ENTRENAR,
            motivo_i18n=None if permitido else "prediccion_operativa.seguridad.sin_permiso_entrenar",
        )

    def puede_ver_estimaciones(self) -> bool:
        return True

    def puede_ver_explicacion(self) -> bool:
        return self.puede_ver_estimaciones()
