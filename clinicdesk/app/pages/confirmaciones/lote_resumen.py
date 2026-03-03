from __future__ import annotations

from clinicdesk.app.application.usecases.recordatorios_citas import ResultadoLoteRecordatoriosDTO


def construir_resumen_lote(dto: ResultadoLoteRecordatoriosDTO) -> tuple[int, int]:
    hechas = dto.preparadas + dto.enviadas
    omitidas = dto.omitidas_sin_contacto + dto.omitidas_ya_enviado
    return hechas, omitidas
