from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.citas.navigation_intent import CitasNavigationIntentDTO


@dataclass(frozen=True, slots=True)
class EstadoIntentPendienteCitas:
    intent: CitasNavigationIntentDTO | None
    obsoleto: bool
    token_pendiente: int | None
    token_vigente: int


class CoordinadorIntentsCitas:
    def __init__(self) -> None:
        self._token_vigente = 0
        self._token_pendiente: int | None = None
        self._intent_pendiente: CitasNavigationIntentDTO | None = None

    def registrar_intent(self, intent: CitasNavigationIntentDTO) -> None:
        self._token_vigente += 1
        self._token_pendiente = self._token_vigente
        self._intent_pendiente = intent

    def invalidar_intents(self) -> None:
        self._token_vigente += 1
        self._token_pendiente = None
        self._intent_pendiente = None

    def resolver_para_vista(self, vista: str, vista_activa: str) -> EstadoIntentPendienteCitas:
        if self._intent_pendiente is None or vista != vista_activa:
            return EstadoIntentPendienteCitas(None, False, self._token_pendiente, self._token_vigente)
        obsoleto = self._token_pendiente != self._token_vigente
        if obsoleto:
            return EstadoIntentPendienteCitas(None, True, self._token_pendiente, self._token_vigente)
        return EstadoIntentPendienteCitas(self._intent_pendiente, False, self._token_pendiente, self._token_vigente)

    def limpiar_pendiente(self) -> None:
        self._token_pendiente = None
        self._intent_pendiente = None
