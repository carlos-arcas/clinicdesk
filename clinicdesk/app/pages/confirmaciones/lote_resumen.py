from __future__ import annotations

from collections.abc import Callable

from clinicdesk.app.application.usecases.recordatorios_citas import ResultadoLoteRecordatoriosDTO


def construir_resumen_lote(dto: ResultadoLoteRecordatoriosDTO) -> tuple[int, int]:
    hechas = dto.preparadas + dto.enviadas
    omitidas = dto.omitidas_sin_contacto + dto.omitidas_ya_enviado
    return hechas, omitidas


def construir_texto_resumen_lote(hechas: int, omitidas: int, traducir: Callable[[str], str]) -> str:
    resumen = traducir("confirmaciones.lote.hecho_resumen").format(hechas=hechas, omitidas=omitidas)
    if omitidas == 0:
        return resumen
    return f"{resumen}. {traducir('confirmaciones.lote.omitidas_generico')}"
