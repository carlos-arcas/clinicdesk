from datetime import date
import sqlite3

from clinicdesk.app.application.seguros.postventa import FiltroCarteraPolizaSeguro
from clinicdesk.app.domain.seguros.postventa import (
    AseguradoPrincipalSeguro,
    BeneficiarioSeguro,
    CoberturaActivaPolizaSeguro,
    EstadoAseguradoSeguro,
    EstadoIncidenciaPolizaSeguro,
    EstadoPolizaSeguro,
    EstadoRenovacionPolizaSeguro,
    IncidenciaPolizaSeguro,
    PolizaSeguro,
    RenovacionPolizaSeguro,
    TipoIncidenciaPolizaSeguro,
    VigenciaPolizaSeguro,
)
from clinicdesk.app.infrastructure.seguros.repositorio_poliza_sqlite import RepositorioPolizaSeguroSqlite


def _repositorio() -> RepositorioPolizaSeguroSqlite:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return RepositorioPolizaSeguroSqlite(conn)


def _poliza(id_poliza: str, fecha_fin: date = date(2026, 12, 31)) -> PolizaSeguro:
    return PolizaSeguro(
        id_poliza=id_poliza,
        id_oportunidad_origen="opp-1",
        id_paciente="pac-1",
        id_plan="clinica_integral",
        estado=EstadoPolizaSeguro.ACTIVA,
        titular=AseguradoPrincipalSeguro(
            id_asegurado=f"tit-{id_poliza}",
            nombre="Ana",
            documento="DOC-1",
            estado=EstadoAseguradoSeguro.ACTIVO,
        ),
        beneficiarios=(
            BeneficiarioSeguro(
                id_beneficiario=f"ben-{id_poliza}",
                nombre="Luis",
                parentesco="hijo",
                estado=EstadoAseguradoSeguro.ACTIVO,
            ),
        ),
        vigencia=VigenciaPolizaSeguro(fecha_inicio=date(2026, 1, 1), fecha_fin=fecha_fin),
        renovacion=RenovacionPolizaSeguro(
            fecha_renovacion_prevista=fecha_fin,
            estado=EstadoRenovacionPolizaSeguro.PENDIENTE,
        ),
        coberturas=(CoberturaActivaPolizaSeguro(codigo_cobertura="COB_BASE", descripcion="base", activa=True),),
        incidencias=(),
    )


def test_persistencia_poliza_beneficiarios_e_incidencias() -> None:
    repo = _repositorio()
    poliza = _poliza("pol-1")

    repo.guardar_poliza(poliza)
    repo.guardar_incidencia(
        "pol-1",
        IncidenciaPolizaSeguro(
            id_incidencia="inc-1",
            tipo=TipoIncidenciaPolizaSeguro.ADMINISTRATIVA,
            descripcion="pendiente validacion",
            estado=EstadoIncidenciaPolizaSeguro.ABIERTA,
            fecha_apertura=date(2026, 2, 1),
        ),
    )

    recuperada = repo.obtener_poliza("pol-1")
    assert recuperada.titular.nombre == "Ana"
    assert len(recuperada.beneficiarios) == 1
    assert len(recuperada.incidencias) == 1


def test_filtros_cartera_poliza_postventa() -> None:
    repo = _repositorio()
    repo.guardar_poliza(_poliza("pol-1", date(2026, 1, 10)))
    repo.guardar_poliza(_poliza("pol-2", date(2027, 5, 1)))
    repo.guardar_incidencia(
        "pol-1",
        IncidenciaPolizaSeguro(
            id_incidencia="inc-1",
            tipo=TipoIncidenciaPolizaSeguro.RENOVACION_BLOQUEADA,
            descripcion="bloqueada",
            estado=EstadoIncidenciaPolizaSeguro.ABIERTA,
            fecha_apertura=date(2026, 1, 5),
        ),
    )

    con_incidencias = repo.listar_polizas(FiltroCarteraPolizaSeguro(solo_con_incidencias=True))
    por_plan = repo.listar_polizas(FiltroCarteraPolizaSeguro(id_plan="clinica_integral"))

    assert len(con_incidencias) == 1
    assert con_incidencias[0].id_poliza == "pol-1"
    assert len(por_plan) == 2
