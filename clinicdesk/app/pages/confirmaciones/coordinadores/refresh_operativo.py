from __future__ import annotations

import logging
from collections.abc import Callable

from clinicdesk.app.pages.confirmaciones.coordinadores.contexto_operativo import CoordinadorContextoConfirmaciones

LOGGER = logging.getLogger(__name__)


class CoordinadorRefreshOperativoConfirmaciones:
    def __init__(
        self,
        *,
        contexto: CoordinadorContextoConfirmaciones,
        on_refresh: Callable[[bool], None],
    ) -> None:
        self._contexto = contexto
        self._on_refresh = on_refresh
        self._token_refresh_operativo = 0

    @property
    def token_refresh_operativo(self) -> int:
        return self._token_refresh_operativo

    def solicitar_desde_whatsapp(self, *, origen: str, operation_id: int) -> bool:
        if operation_id != self._contexto.token_whatsapp_rapido:
            self._log_omision("token_obsoleto", origen, operation_id)
            return False
        if not self._contexto.es_contexto_operativo_vigente():
            self._log_omision("contexto_no_vigente", origen, operation_id)
            return False
        self._token_refresh_operativo += 1
        self._on_refresh(False)
        return True

    def solicitar_desde_lote(self, operation_id: int) -> bool:
        if not self._contexto.es_contexto_operativo_vigente():
            LOGGER.info(
                "confirmaciones_lote_refresh_omitido",
                extra={
                    "action": "confirmaciones_lote_refresh_omitido",
                    "reason": "contexto_no_vigente",
                    "operation_id": operation_id,
                },
            )
            return False
        self._on_refresh(False)
        return True

    def _log_omision(self, reason: str, origen: str, operation_id: int) -> None:
        LOGGER.info(
            "confirmaciones_refresh_operativo_omitido",
            extra={
                "action": "confirmaciones_refresh_operativo_omitido",
                "reason": reason,
                "origen": origen,
                "operation_id": operation_id,
            },
        )
