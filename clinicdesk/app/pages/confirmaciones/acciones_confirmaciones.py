from __future__ import annotations


def navegar_prediccion(parent) -> None:
    window = parent.window()
    if hasattr(window, "navigate"):
        window.navigate("prediccion_ausencias")
