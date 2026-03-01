from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FiltrosCitasEstado:
    desde: str
    hasta: str
    texto: str
    estado: str
