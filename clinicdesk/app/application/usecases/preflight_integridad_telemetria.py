from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class EstadoIntegridadTelemetria:
    ok: bool
    tabla: str | None = None
    primer_fallo_id: int | None = None


class IntegridadTelemetriaComprometidaError(Exception):
    def __init__(self, *, tabla: str | None, primer_fallo_id: int | None) -> None:
        super().__init__("telemetria_integridad_comprometida")
        self.reason_code = "telemetria_integridad_comprometida"
        self.tabla = tabla
        self.primer_fallo_id = primer_fallo_id


class VerificadorIntegridadTelemetriaGateway(Protocol):
    def verificar_integridad_telemetria(self) -> EstadoIntegridadTelemetria: ...


def exigir_integridad_telemetria(verificador: VerificadorIntegridadTelemetriaGateway) -> None:
    resultado = verificador.verificar_integridad_telemetria()
    if resultado.ok:
        return
    raise IntegridadTelemetriaComprometidaError(
        tabla=resultado.tabla,
        primer_fallo_id=resultado.primer_fallo_id,
    )

