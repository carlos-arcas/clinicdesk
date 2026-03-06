from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta

from clinicdesk.app.bootstrap import bootstrap_database
from clinicdesk.app.container import build_container
from clinicdesk.app.queries.citas_queries import CitasQueries
from clinicdesk.app.queries.pacientes_queries import PacientesQueries


@dataclass(frozen=True, slots=True)
class FiltrosCitasApi:
    desde: str | None
    hasta: str | None
    estado: str
    texto: str


class ServicioConsultasApi:
    def __init__(self, citas_queries: CitasQueries, pacientes_queries: PacientesQueries) -> None:
        self._citas_queries = citas_queries
        self._pacientes_queries = pacientes_queries

    def listar_citas(self, filtros: FiltrosCitasApi) -> list[dict[str, object]]:
        desde, hasta = _resolver_rango_fechas(filtros.desde, filtros.hasta)
        rows = self._citas_queries.search_listado(
            desde=desde,
            hasta=hasta,
            texto=filtros.texto.strip(),
            estado=filtros.estado.strip(),
        )
        return [asdict(row) for row in rows]

    def buscar_pacientes(self, texto: str) -> list[dict[str, object]]:
        rows = self._pacientes_queries.search(texto=texto, limit=100)
        return [asdict(row) for row in rows]


class _ServicioConsultasApiDb(ServicioConsultasApi):
    def __init__(self) -> None:
        self._con = bootstrap_database(apply_schema=True)
        container = build_container(self._con)
        super().__init__(CitasQueries(container), PacientesQueries(self._con))


def construir_servicio_consultas() -> ServicioConsultasApi:
    return _ServicioConsultasApiDb()


def _resolver_rango_fechas(desde: str | None, hasta: str | None) -> tuple[str, str]:
    if desde and hasta:
        return desde, hasta
    hoy = date.today()
    if hasta:
        return (date.fromisoformat(hasta) - timedelta(days=30)).isoformat(), hasta
    if desde:
        return desde, hoy.isoformat()
    return (hoy - timedelta(days=30)).isoformat(), hoy.isoformat()
