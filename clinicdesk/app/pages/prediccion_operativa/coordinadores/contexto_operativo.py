from __future__ import annotations

import logging

LOGGER = logging.getLogger(__name__)


class CoordinadorContextoPrediccionOperativa:
    def __init__(self) -> None:
        self._pagina_visible = False
        self._token_contexto = 0

    @property
    def pagina_visible(self) -> bool:
        return self._pagina_visible

    @property
    def token_contexto(self) -> int:
        return self._token_contexto

    def on_show(self) -> int:
        self._pagina_visible = True
        self._token_contexto += 1
        return self._token_contexto

    def on_hide(self) -> int:
        self._pagina_visible = False
        self._token_contexto += 1
        return self._token_contexto

    def contexto_vigente(self, token_contexto: int) -> bool:
        if token_contexto != self._token_contexto:
            self._log_omision("prediccion_contexto_omitido", "contexto_obsoleto", token_contexto=token_contexto)
            return False
        if not self._pagina_visible:
            self._log_omision("prediccion_contexto_omitido", "pagina_no_visible", token_contexto=token_contexto)
            return False
        return True

    def _log_omision(self, accion: str, razon: str, **extra: int) -> None:
        LOGGER.info(accion, extra={"action": accion, "reason": razon, **extra})
