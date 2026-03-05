from __future__ import annotations

from typing import Protocol

from clinicdesk.app.application.telemetria import EventoTelemetriaDTO


class RepositorioTelemetria(Protocol):
    def registrar(self, evento: EventoTelemetriaDTO) -> None: ...
