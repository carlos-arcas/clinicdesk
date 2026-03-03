from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget
else:
    QWidget = object


@dataclass(frozen=True)
class PageDef:
    """Descriptor de página para navegación lazy."""

    key: str
    title: str
    factory: Callable[[], QWidget]
