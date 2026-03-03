from __future__ import annotations

from clinicdesk.app.container import AppContainer
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.page_def import PageDef
from clinicdesk.app.pages.pages_registry import PageRegistry
from clinicdesk.app.pages.prediccion_ausencias.page import PagePrediccionAusencias
from clinicdesk.app.application.usecases.registrar_telemetria import RegistrarTelemetria


def register(registry: PageRegistry, container: AppContainer, i18n: I18nManager) -> None:
    registry.register(
        PageDef(
            key="prediccion_ausencias",
            title=i18n.t("nav.prediccion_ausencias"),
            factory=lambda: PagePrediccionAusencias(
                container.prediccion_ausencias_facade,
                i18n,
                RegistrarTelemetria(container.telemetria_eventos_repo),
                container.user_context,
            ),
        )
    )
