from __future__ import annotations

from typing import Optional


def _extraer_altura_desde_size_hint(widget: object) -> Optional[int]:
    size_hint = getattr(widget, "sizeHint", None)
    if not callable(size_hint):
        return None
    hint = size_hint()
    if hint is None:
        return None
    height = getattr(hint, "height", None)
    if not callable(height):
        return None
    return height()


def _extraer_altura_directa(widget: object) -> Optional[int]:
    height = getattr(widget, "height", None)
    if not callable(height):
        return None
    return height()


def resolver_altura_objetivo(widgets: list[object]) -> int | None:
    alturas: list[int] = []
    for widget in widgets:
        altura = _extraer_altura_desde_size_hint(widget)
        if altura is None:
            altura = _extraer_altura_directa(widget)
        if isinstance(altura, int):
            alturas.append(altura)
    if not alturas:
        return None
    return max(alturas)


def aplicar_altura(widgets: list[object], altura: int) -> None:
    for widget in widgets:
        set_fixed_height = getattr(widget, "setFixedHeight", None)
        if callable(set_fixed_height):
            set_fixed_height(altura)


def normalizar_alturas_inputs(widgets: list[object]) -> None:
    altura = resolver_altura_objetivo(widgets)
    if altura is None:
        return
    aplicar_altura(widgets, altura)
