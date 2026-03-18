from __future__ import annotations

import logging

LOGGER = logging.getLogger(__name__)


class CoordinadorContextoPacientes:
    def __init__(self) -> None:
        self._pagina_visible = False
        self._token_carga = 0
        self._token_busqueda_rapida = 0
        self._token_on_show = 0
        self._token_refresh_programado = 0
        self._refresh_diferido_pendiente = False

    @property
    def pagina_visible(self) -> bool:
        return self._pagina_visible

    @property
    def token_carga(self) -> int:
        return self._token_carga

    @property
    def token_busqueda_rapida(self) -> int:
        return self._token_busqueda_rapida

    def on_show(self) -> int:
        self._pagina_visible = True
        self._token_on_show += 1
        return self._token_on_show

    def on_hide(self) -> None:
        self._pagina_visible = False
        self._token_carga += 1
        self._token_busqueda_rapida += 1

    def programar_refresh_on_show(self, token_on_show: int) -> bool:
        self._token_refresh_programado = token_on_show
        if self._refresh_diferido_pendiente:
            return False
        self._refresh_diferido_pendiente = True
        return True

    def consumir_refresh_programado(self) -> bool:
        self._refresh_diferido_pendiente = False
        if self._token_refresh_programado != self._token_on_show:
            self._log_refresh_omitido("on_show_obsoleto")
            return False
        if not self._pagina_visible:
            self._log_refresh_omitido("pagina_no_visible")
            return False
        return True

    def nuevo_token_carga(self) -> int:
        self._token_carga += 1
        return self._token_carga

    def nueva_busqueda_rapida(self) -> int:
        self._token_busqueda_rapida += 1
        return self._token_busqueda_rapida

    def puede_consumir_carga(self, token: int) -> bool:
        if token != self._token_carga:
            self._log_omision("pacientes_carga_omitida", "token_obsoleto", token=token)
            return False
        if not self._pagina_visible:
            self._log_omision("pacientes_carga_omitida", "pagina_no_visible", token=token)
            return False
        return True

    def puede_consumir_busqueda_rapida(self, token: int) -> bool:
        if token != self._token_busqueda_rapida:
            self._log_omision(
                "pacientes_busqueda_rapida_omitida",
                "token_obsoleto",
                token=token,
            )
            return False
        if not self._pagina_visible:
            self._log_omision(
                "pacientes_busqueda_rapida_omitida",
                "pagina_no_visible",
                token=token,
            )
            return False
        return True

    def _log_refresh_omitido(self, reason: str) -> None:
        LOGGER.info(
            "pacientes_refresh_omitido",
            extra={
                "action": "pacientes_refresh_omitido",
                "reason": reason,
                "token_on_show": self._token_on_show,
            },
        )

    def _log_omision(self, action: str, reason: str, **extra: int) -> None:
        LOGGER.info(action, extra={"action": action, "reason": reason, **extra})
