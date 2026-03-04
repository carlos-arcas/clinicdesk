from __future__ import annotations


class DespachadorDebounce:
    def __init__(self, delay_ms: int) -> None:
        self._delay_ms = delay_ms
        self._texto_pendiente: str | None = None
        self._deadline_ms: int | None = None

    def registrar(self, texto: str, ahora_ms: int) -> None:
        self._texto_pendiente = texto
        self._deadline_ms = ahora_ms + self._delay_ms

    def extraer_si_listo(self, ahora_ms: int) -> str | None:
        if self._deadline_ms is None or self._texto_pendiente is None:
            return None
        if ahora_ms < self._deadline_ms:
            return None
        texto = self._texto_pendiente
        self._texto_pendiente = None
        self._deadline_ms = None
        return texto

    def siguiente_espera_ms(self, ahora_ms: int) -> int:
        if self._deadline_ms is None:
            return self._delay_ms
        return max(0, self._deadline_ms - ahora_ms)
