from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class EstadoIntegridadAuditoria:
    ok: bool
    tabla: str | None = None
    primer_fallo_id: int | None = None


class IntegridadAuditoriaComprometidaError(Exception):
    def __init__(self, *, tabla: str | None, primer_fallo_id: int | None) -> None:
        super().__init__("auditoria_integridad_comprometida")
        self.reason_code = "auditoria_integridad_comprometida"
        self.tabla = tabla
        self.primer_fallo_id = primer_fallo_id


class VerificadorIntegridadAuditoriaGateway(Protocol):
    def verificar_integridad_auditoria(self) -> EstadoIntegridadAuditoria: ...


def exigir_integridad_auditoria(verificador: VerificadorIntegridadAuditoriaGateway | None) -> None:
    if verificador is None:
        return
    resultado = verificador.verificar_integridad_auditoria()
    if resultado.ok:
        return
    raise IntegridadAuditoriaComprometidaError(
        tabla=resultado.tabla,
        primer_fallo_id=resultado.primer_fallo_id,
    )
