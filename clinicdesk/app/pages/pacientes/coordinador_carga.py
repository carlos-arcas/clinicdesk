from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SolicitudCargaPacientes:
    token: int
    seleccion_id: int | None
    activo: bool
    texto: str


class CoordinadorCargaPacientes:
    def __init__(self) -> None:
        self._en_curso: SolicitudCargaPacientes | None = None
        self._pendiente: SolicitudCargaPacientes | None = None

    def registrar(self, solicitud: SolicitudCargaPacientes) -> bool:
        if self._en_curso is None:
            self._en_curso = solicitud
            return True
        self._pendiente = solicitud
        return False

    def es_token_activo(self, token: int) -> bool:
        return self._en_curso is not None and self._en_curso.token == token

    def finalizar(self, token: int) -> SolicitudCargaPacientes | None:
        if not self.es_token_activo(token):
            return None
        self._en_curso = None
        if self._pendiente is None:
            return None
        siguiente = self._pendiente
        self._pendiente = None
        self._en_curso = siguiente
        return siguiente
