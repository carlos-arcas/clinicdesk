from __future__ import annotations

from clinicdesk.app.application.usecases.paginacion_incremental import calcular_siguiente_offset


def test_calcular_siguiente_offset_flujo_completo() -> None:
    total = 120
    limit = 50
    offset = 0

    assert offset == 0
    offset = calcular_siguiente_offset(offset, limit, total)
    assert offset == 50
    offset = calcular_siguiente_offset(offset, limit, total)
    assert offset == 100
    offset = calcular_siguiente_offset(offset, limit, total)
    assert offset == 120
