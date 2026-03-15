import sqlite3
from datetime import date

from clinicdesk.app.application.seguros.economia_poliza import (
    GestionEconomicaPolizaSeguroService,
    SolicitudEmitirCuotaPolizaSeguro,
    SolicitudRegistrarImpagoSeguro,
    SolicitudRegistrarReactivacionPolizaSeguro,
    SolicitudRegistrarSuspensionPolizaSeguro,
)
from clinicdesk.app.domain.seguros.economia_poliza import EstadoPagoPolizaSeguro
from clinicdesk.app.infrastructure.seguros.repositorio_economia_poliza_sqlite import (
    RepositorioEconomiaPolizaSeguroSqlite,
)
from clinicdesk.app.infrastructure.seguros.repositorio_poliza_sqlite import RepositorioPolizaSeguroSqlite
from clinicdesk.app.domain.seguros.postventa import (
    AseguradoPrincipalSeguro,
    EstadoAseguradoSeguro,
    EstadoPolizaSeguro,
    EstadoRenovacionPolizaSeguro,
    PolizaSeguro,
    RenovacionPolizaSeguro,
    VigenciaPolizaSeguro,
)


def _crear_oportunidad_minima(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT INTO seguro_oportunidades (
            id_oportunidad, id_candidato, id_paciente, segmento, plan_origen_id, plan_destino_id,
            estado_actual, clasificacion_motor, creado_en, actualizado_en
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """,
        ("opp-1", "cand-1", "pac-1", "SEG", "origen", "plan-1", "CONVERTIDA", "ALTA"),
    )
    connection.commit()


def _crear_poliza_minima(repo_poliza: RepositorioPolizaSeguroSqlite, id_poliza: str) -> None:
    repo_poliza.guardar_poliza(
        PolizaSeguro(
            id_poliza=id_poliza,
            id_oportunidad_origen="opp-1",
            id_paciente="pac-1",
            id_plan="plan-1",
            estado=EstadoPolizaSeguro.ACTIVA,
            titular=AseguradoPrincipalSeguro(
                id_asegurado="tit-1",
                nombre="Ana",
                documento="DOC-1",
                estado=EstadoAseguradoSeguro.ACTIVO,
            ),
            beneficiarios=(),
            vigencia=VigenciaPolizaSeguro(fecha_inicio=date(2026, 1, 1), fecha_fin=date(2027, 1, 1)),
            renovacion=RenovacionPolizaSeguro(
                fecha_renovacion_prevista=date(2027, 1, 1),
                estado=EstadoRenovacionPolizaSeguro.PENDIENTE,
            ),
            coberturas=(),
            incidencias=(),
        )
    )


def test_persistencia_economica_sqlite_flujo_basico() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    repo_poliza = RepositorioPolizaSeguroSqlite(connection)
    _crear_oportunidad_minima(connection)
    _crear_poliza_minima(repo_poliza, "pol-1")
    repo = RepositorioEconomiaPolizaSeguroSqlite(connection)
    servicio = GestionEconomicaPolizaSeguroService(repo)

    servicio.emitir_cuota(
        SolicitudEmitirCuotaPolizaSeguro(
            id_cuota="c-1",
            id_poliza="pol-1",
            periodo="2026-01",
            fecha_emision=date(2026, 1, 1),
            fecha_vencimiento=date(2026, 1, 2),
            importe=90,
        )
    )
    servicio.registrar_impago(
        SolicitudRegistrarImpagoSeguro(
            id_evento="imp-1",
            id_poliza="pol-1",
            id_cuota="c-1",
            fecha_evento=date(2026, 1, 4),
            motivo="rechazo",
        )
    )
    servicio.registrar_suspension(
        SolicitudRegistrarSuspensionPolizaSeguro(
            id_evento="sus-1",
            id_poliza="pol-1",
            fecha_evento=date(2026, 1, 5),
            motivo="riesgo alto",
        )
    )

    resumen_suspendida = servicio.obtener_resumen_poliza("pol-1", hoy=date(2026, 1, 5))
    assert resumen_suspendida.estado_pago is EstadoPagoPolizaSeguro.SUSPENDIDA

    servicio.registrar_reactivacion(
        SolicitudRegistrarReactivacionPolizaSeguro(
            id_evento="rea-1",
            id_poliza="pol-1",
            fecha_evento=date(2026, 1, 6),
            motivo="regularizada",
        )
    )
    cartera = servicio.listar_cartera_economica(hoy=date(2026, 1, 6))
    assert len(cartera) == 1
