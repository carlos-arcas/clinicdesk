from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.usecases.recordatorios_citas import (
    MarcarRecordatoriosEnviadosEnLote,
    ObtenerEstadoRecordatorioCita,
    PrepararRecordatorioCita,
    PrepararRecordatoriosEnLote,
    RegistrarRecordatorioCita,
)


@dataclass(slots=True)
class RecordatoriosCitasFacade:
    preparar_uc: PrepararRecordatorioCita
    registrar_uc: RegistrarRecordatorioCita
    obtener_estado_uc: ObtenerEstadoRecordatorioCita
    preparar_lote_uc: PrepararRecordatoriosEnLote
    marcar_enviado_lote_uc: MarcarRecordatoriosEnviadosEnLote
