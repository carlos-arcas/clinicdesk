from __future__ import annotations


def calcular_siguiente_offset(offset: int, limit: int, total: int) -> int:
    if total <= 0:
        return 0
    offset_actual = max(0, int(offset))
    limite = max(1, int(limit))
    return min(offset_actual + limite, total)
