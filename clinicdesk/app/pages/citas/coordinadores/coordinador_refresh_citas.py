from __future__ import annotations


class CoordinadorRefreshCitas:
    def __init__(self) -> None:
        self._token_vigente = 0
        self._pagina_visible = False

    def activar_pagina(self) -> None:
        self._pagina_visible = True

    def desactivar_pagina(self) -> int:
        self._pagina_visible = False
        return self.invalidar_vigente()

    def solicitar_token(self) -> int | None:
        if not self._pagina_visible:
            return None
        self._token_vigente += 1
        return self._token_vigente

    def invalidar_vigente(self) -> int:
        token_prev = self._token_vigente
        self._token_vigente += 1
        return token_prev

    def es_vigente(self, token_refresh: int) -> bool:
        return self._pagina_visible and token_refresh == self._token_vigente

    def pagina_visible(self) -> bool:
        return self._pagina_visible

    def token_vigente(self) -> int:
        return self._token_vigente
