from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QWidget
# QWidget es la clase base de widgets Qt; una página será un QWidget.

@dataclass(frozen=True)
class PageDef:
    """
    Descriptor de página:
    - key: identificador interno
    - title: texto visible en sidebar
    - factory: función que crea la página bajo demanda (lazy)
    """
    key: str
    title: str
    factory: Callable[[], QWidget]
