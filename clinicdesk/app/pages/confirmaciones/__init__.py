from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from clinicdesk.app.pages.confirmaciones.page import PageConfirmaciones


__all__ = ["PageConfirmaciones"]


def __getattr__(name: str):
    if name != "PageConfirmaciones":
        raise AttributeError(name)
    from clinicdesk.app.pages.confirmaciones.page import PageConfirmaciones

    return PageConfirmaciones
