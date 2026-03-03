from __future__ import annotations

import sqlite3

from clinicdesk.app.application.recordatorios.puertos import GatewayRecordatoriosCitas
from clinicdesk.app.infrastructure.sqlite.recordatorios_citas_gateway import RecordatoriosCitasSqliteGateway


def _acepta_gateway_recordatorios(gateway: GatewayRecordatoriosCitas) -> GatewayRecordatoriosCitas:
    return gateway


def test_gateway_sqlite_cumple_protocol_recordatorios() -> None:
    connection = sqlite3.connect(":memory:")
    try:
        gateway = RecordatoriosCitasSqliteGateway(connection=connection)
        adaptador = _acepta_gateway_recordatorios(gateway)
        assert isinstance(adaptador, GatewayRecordatoriosCitas)
    finally:
        connection.close()
