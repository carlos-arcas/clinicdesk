from __future__ import annotations

from collections.abc import Callable

from clinicdesk.app.application.citas import ResultadoLoteHitosDTO


def construir_resumen_lote(dto: ResultadoLoteHitosDTO) -> tuple[int, int]:
    return dto.aplicadas, dto.ya_estaban + dto.omitidas_por_orden


def construir_texto_resumen_lote(hechas: int, omitidas: int, traducir: Callable[[str], str]) -> str:
    resumen = traducir("citas.hitos.lote.hecho_resumen").format(hechas=hechas, omitidas=omitidas)
    if omitidas == 0:
        return resumen
    return f"{resumen}. {traducir('citas.hitos.lote.omitidas_generico')}"
