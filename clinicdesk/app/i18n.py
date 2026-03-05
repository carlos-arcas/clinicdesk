from __future__ import annotations

from typing import Callable

from clinicdesk.app.i18n_catalog import _TRANSLATIONS
from clinicdesk.app.i18n_confirmaciones_catalog import CONFIRMACIONES_TRANSLATIONS
from clinicdesk.app.i18n_historial_catalog import HISTORIAL_TRANSLATIONS
from clinicdesk.app.i18n_prediccion_cierre import TRADUCCIONES_CIERRE_PREDICCION
from clinicdesk.app.i18n_prediccion_entrenar_catalog import TRANSLATIONS_PREDICCION_ENTRENAR
from clinicdesk.app.i18n_citas_ui_catalog import CITAS_UI_TRANSLATIONS
from clinicdesk.app.i18n_auditoria_catalog import AUDITORIA_TRANSLATIONS
from clinicdesk.app.i18n_placeholder_catalog import PLACEHOLDER_TRANSLATIONS
from clinicdesk.app.i18n_prediccion_operativa_catalog import PREDICCION_OPERATIVA_TRANSLATIONS
from clinicdesk.app.i18n_dashboard_gestion_catalog import DASHBOARD_GESTION_TRANSLATIONS

for idioma, traducciones in TRADUCCIONES_CIERRE_PREDICCION.items():
    _TRANSLATIONS.setdefault(idioma, {}).update(traducciones)

for idioma, traducciones in CONFIRMACIONES_TRANSLATIONS.items():
    _TRANSLATIONS.setdefault(idioma, {}).update(traducciones)

for idioma, traducciones in TRANSLATIONS_PREDICCION_ENTRENAR.items():
    _TRANSLATIONS.setdefault(idioma, {}).update(traducciones)

for idioma, traducciones in HISTORIAL_TRANSLATIONS.items():
    _TRANSLATIONS.setdefault(idioma, {}).update(traducciones)

for idioma, traducciones in AUDITORIA_TRANSLATIONS.items():
    _TRANSLATIONS.setdefault(idioma, {}).update(traducciones)


class I18nManager:
    def __init__(self, language: str = "es") -> None:
        self._language = language if language in _TRANSLATIONS else "es"
        self._listeners: list[Callable[[], None]] = []

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, language: str) -> None:
        if language not in _TRANSLATIONS or language == self._language:
            return
        self._language = language
        for listener in list(self._listeners):
            listener()

    def t(self, key: str) -> str:
        return _TRANSLATIONS.get(self._language, {}).get(key, key)

    def subscribe(self, callback: Callable[[], None]) -> None:
        self._listeners.append(callback)


for idioma, traducciones in CITAS_UI_TRANSLATIONS.items():
    _TRANSLATIONS.setdefault(idioma, {}).update(traducciones)


for idioma, traducciones in PREDICCION_OPERATIVA_TRANSLATIONS.items():
    _TRANSLATIONS.setdefault(idioma, {}).update(traducciones)

for idioma, traducciones in PLACEHOLDER_TRANSLATIONS.items():
    _TRANSLATIONS.setdefault(idioma, {}).update(traducciones)

for idioma, traducciones in DASHBOARD_GESTION_TRANSLATIONS.items():
    _TRANSLATIONS.setdefault(idioma, {}).update(traducciones)
