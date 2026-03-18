from __future__ import annotations

import logging

LOGGER = logging.getLogger(__name__)


class CoordinadorContextoConfirmaciones:
    def __init__(self) -> None:
        self._pagina_visible = False
        self._token_carga = 0
        self._token_busqueda_rapida = 0
        self._token_whatsapp_rapido = 0

    def sincronizar_para_pruebas(
        self,
        *,
        pagina_visible: bool | None = None,
        token_carga: int | None = None,
        token_busqueda_rapida: int | None = None,
        token_whatsapp_rapido: int | None = None,
    ) -> None:
        if pagina_visible is not None:
            self._pagina_visible = pagina_visible
        if token_carga is not None:
            self._token_carga = token_carga
        if token_busqueda_rapida is not None:
            self._token_busqueda_rapida = token_busqueda_rapida
        if token_whatsapp_rapido is not None:
            self._token_whatsapp_rapido = token_whatsapp_rapido

    @property
    def pagina_visible(self) -> bool:
        return self._pagina_visible

    @property
    def token_carga(self) -> int:
        return self._token_carga

    @property
    def token_busqueda_rapida(self) -> int:
        return self._token_busqueda_rapida

    @property
    def token_whatsapp_rapido(self) -> int:
        return self._token_whatsapp_rapido

    def on_show(self) -> None:
        self._pagina_visible = True

    def on_hide(self) -> None:
        self._pagina_visible = False
        self.invalidar_whatsapp_rapido()

    def es_contexto_operativo_vigente(self) -> bool:
        return self._pagina_visible

    def nuevo_token_carga(self) -> int:
        self._token_carga += 1
        return self._token_carga

    def nueva_busqueda_rapida(self) -> int:
        self._token_busqueda_rapida += 1
        return self._token_busqueda_rapida

    def nueva_operacion_whatsapp_rapido(self) -> int:
        self._token_whatsapp_rapido += 1
        return self._token_whatsapp_rapido

    def invalidar_whatsapp_rapido(self) -> None:
        self._token_whatsapp_rapido += 1

    def puede_consumir_carga(self, token: int) -> bool:
        if token != self._token_carga:
            self._log_omision("confirmaciones_carga_omitida", "token_obsoleto", token=token)
            return False
        if not self._pagina_visible:
            self._log_omision("confirmaciones_carga_omitida", "pagina_no_visible", token=token)
            return False
        return True

    def puede_consumir_busqueda_rapida(self, token: int) -> bool:
        if token != self._token_busqueda_rapida:
            self._log_omision(
                "confirmaciones_busqueda_rapida_omitida",
                "token_obsoleto",
                token=token,
            )
            return False
        if not self._pagina_visible:
            self._log_omision(
                "confirmaciones_busqueda_rapida_omitida",
                "pagina_no_visible",
                token=token,
            )
            return False
        return True

    def es_whatsapp_rapido_vigente(self, operation_id: int) -> bool:
        if operation_id != self._token_whatsapp_rapido:
            self._log_omision(
                "confirmaciones_whatsapp_rapido_omitido",
                "token_obsoleto",
                operation_id=operation_id,
            )
            return False
        if not self._pagina_visible:
            self._log_omision(
                "confirmaciones_whatsapp_rapido_omitido",
                "contexto_no_vigente",
                operation_id=operation_id,
            )
            return False
        return True

    def puede_mostrar_feedback_operativo(self, operation_id: int) -> bool:
        return self.es_whatsapp_rapido_vigente(operation_id) and self.es_contexto_operativo_vigente()

    def _log_omision(self, action: str, reason: str, **extra: int) -> None:
        LOGGER.info(action, extra={"action": action, "reason": reason, **extra})
