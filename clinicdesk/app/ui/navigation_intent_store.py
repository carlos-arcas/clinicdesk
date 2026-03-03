from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass
class IntentConsumible(Generic[T]):
    _intent_pendiente: T | None = None

    def guardar(self, intent: T) -> None:
        self._intent_pendiente = intent

    def consumir(self) -> T | None:
        intent = self._intent_pendiente
        self._intent_pendiente = None
        return intent
