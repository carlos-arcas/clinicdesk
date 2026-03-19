from __future__ import annotations

from string import Formatter
from typing import Callable

from clinicdesk.app.bootstrap_logging import get_logger
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

LOGGER = get_logger(__name__)
_FORMATTER = Formatter()

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


def _extraer_placeholders(texto: str) -> set[str]:
    placeholders: set[str] = set()
    for _, field_name, _, _ in _FORMATTER.parse(texto):
        if field_name:
            placeholders.add(field_name)
    return placeholders


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

    def t(self, key: str, **kwargs: object) -> str:
        texto = _TRANSLATIONS.get(self._language, {}).get(key, key)
        if not kwargs:
            return texto
        placeholders = _extraer_placeholders(texto)
        faltantes = sorted(placeholders.difference(kwargs))
        sobrantes = sorted(set(kwargs).difference(placeholders))
        if faltantes:
            LOGGER.warning(
                "i18n_missing_interpolation_values",
                extra={
                    "action": "i18n_missing_interpolation_values",
                    "key": key,
                    "language": self._language,
                    "missing": faltantes,
                },
            )
            return texto
        if not placeholders:
            LOGGER.warning(
                "i18n_unused_interpolation_values",
                extra={
                    "action": "i18n_unused_interpolation_values",
                    "key": key,
                    "language": self._language,
                    "unexpected": sorted(kwargs),
                },
            )
            return texto
        if sobrantes:
            LOGGER.warning(
                "i18n_unused_interpolation_values",
                extra={
                    "action": "i18n_unused_interpolation_values",
                    "key": key,
                    "language": self._language,
                    "unexpected": sobrantes,
                },
            )
        valores = {nombre: kwargs[nombre] for nombre in placeholders}
        try:
            return texto.format(**valores)
        except (IndexError, KeyError, ValueError):
            LOGGER.warning(
                "i18n_interpolation_failed",
                extra={
                    "action": "i18n_interpolation_failed",
                    "key": key,
                    "language": self._language,
                    "placeholders": sorted(placeholders),
                },
            )
            return texto

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
