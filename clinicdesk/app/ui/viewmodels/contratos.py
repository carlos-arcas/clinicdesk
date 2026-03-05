from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, Literal, TypeVar


ItemT = TypeVar("ItemT")


class EstadoPantalla(Enum):
    LOADING = "loading"
    EMPTY = "empty"
    ERROR = "error"
    CONTENT = "content"


@dataclass(slots=True)
class EstadoListado(Generic[ItemT]):
    estado_pantalla: EstadoPantalla = EstadoPantalla.LOADING
    items: list[ItemT] = field(default_factory=list)
    filtro_texto: str = ""
    error_key: str | None = None
    seleccion_id: int | None = None
    last_search_safe: str | None = None


@dataclass(slots=True)
class EventoUI:
    tipo: Literal["toast", "job", "nav"]
    payload: dict[str, object] = field(default_factory=dict)
