from clinicdesk.app.application.security import Action, AutorizadorAcciones, Role, UserContext
from clinicdesk.app.application.services.politica_seguridad_prediccion_operativa import (
    PoliticaSeguridadPrediccionOperativa,
)


def test_politica_permita_entrenamiento_para_admin() -> None:
    politica = PoliticaSeguridadPrediccionOperativa(
        autorizador=AutorizadorAcciones(),
        contexto_usuario=UserContext(role=Role.ADMIN, username="admin"),
    )

    decision = politica.decidir_entrenamiento()

    assert decision.permitido is True
    assert decision.accion is Action.ML_ENTRENAR
    assert decision.motivo_i18n is None


def test_politica_deniegue_entrenamiento_para_readonly() -> None:
    politica = PoliticaSeguridadPrediccionOperativa(
        autorizador=AutorizadorAcciones(),
        contexto_usuario=UserContext(role=Role.READONLY, username="readonly"),
    )

    decision = politica.decidir_entrenamiento()

    assert decision.permitido is False
    assert decision.accion is Action.ML_ENTRENAR
    assert decision.motivo_i18n == "prediccion_operativa.seguridad.sin_permiso_entrenar"


def test_politica_mantiene_lectura_y_explicacion_para_roles_lectura() -> None:
    politica = PoliticaSeguridadPrediccionOperativa(
        autorizador=AutorizadorAcciones(),
        contexto_usuario=UserContext(role=Role.READONLY, username="readonly"),
    )

    assert politica.puede_ver_estimaciones() is True
    assert politica.puede_ver_explicacion() is True
