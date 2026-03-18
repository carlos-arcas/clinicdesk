from __future__ import annotations

import logging
from dataclasses import dataclass

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RunEntrenamiento:
    tipo: str
    token: int
    token_contexto: int


class CoordinadorRunsEntrenamientoPrediccionOperativa:
    def __init__(self) -> None:
        self._tokens_por_tipo: dict[str, int] = {"duracion": 0, "espera": 0}
        self._contexto_por_tipo: dict[str, int] = {"duracion": 0, "espera": 0}

    def token_actual(self, tipo: str) -> int:
        return self._tokens_por_tipo[tipo]

    def iniciar_run(self, tipo: str, token_contexto: int) -> RunEntrenamiento:
        token = self._tokens_por_tipo[tipo] + 1
        self._tokens_por_tipo[tipo] = token
        self._contexto_por_tipo[tipo] = token_contexto
        return RunEntrenamiento(tipo=tipo, token=token, token_contexto=token_contexto)

    def invalidar_todos(self) -> None:
        for tipo in self._tokens_por_tipo:
            self._tokens_por_tipo[tipo] += 1

    def run_vigente(self, tipo: str, token: int) -> bool:
        if token != self._tokens_por_tipo[tipo]:
            self._log_omision(tipo, token, "token_obsoleto")
            return False
        return True

    def contexto_de_run(self, tipo: str) -> int:
        return self._contexto_por_tipo[tipo]

    def _log_omision(self, tipo: str, token: int, razon: str) -> None:
        LOGGER.info(
            "prediccion_entrenamiento_omitido",
            extra={"action": "prediccion_entrenamiento_omitido", "tipo": tipo, "token": token, "reason": razon},
        )
