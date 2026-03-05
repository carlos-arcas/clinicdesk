from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

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
    proveedor_conexion: _ProveedorConexionConCierre | None = None

    def cerrar_conexion_hilo_actual(self) -> None:
        if self.proveedor_conexion is None:
            return
        self.proveedor_conexion.cerrar_conexion_del_hilo_actual()


class _ProveedorConexionConCierre(Protocol):
    def cerrar_conexion_del_hilo_actual(self) -> None: ...
