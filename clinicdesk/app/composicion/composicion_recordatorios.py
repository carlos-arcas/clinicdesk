from __future__ import annotations

from clinicdesk.app.application.recordatorios.puertos import GatewayRecordatoriosCitas
from clinicdesk.app.application.services.recordatorios_citas_facade import RecordatoriosCitasFacade
from clinicdesk.app.application.usecases.recordatorios_citas import (
    MarcarRecordatoriosEnviadosEnLote,
    ObtenerEstadoRecordatorioCita,
    PrepararRecordatorioCita,
    PrepararRecordatoriosEnLote,
    RegistrarRecordatorioCita,
)
from clinicdesk.app.infrastructure.sqlite.proveedor_conexion_sqlite import ProveedorConexionSqlitePorHilo
from clinicdesk.app.infrastructure.sqlite.recordatorios_citas_gateway import RecordatoriosCitasSqliteGateway


def build_recordatorios_citas_facade(
    proveedor_conexion: ProveedorConexionSqlitePorHilo,
) -> RecordatoriosCitasFacade:
    gateway: GatewayRecordatoriosCitas = RecordatoriosCitasSqliteGateway(proveedor_conexion=proveedor_conexion)
    return RecordatoriosCitasFacade(
        preparar_uc=PrepararRecordatorioCita(gateway),
        registrar_uc=RegistrarRecordatorioCita(gateway),
        obtener_estado_uc=ObtenerEstadoRecordatorioCita(gateway),
        preparar_lote_uc=PrepararRecordatoriosEnLote(gateway),
        marcar_enviado_lote_uc=MarcarRecordatoriosEnviadosEnLote(gateway),
        proveedor_conexion=proveedor_conexion,
    )
