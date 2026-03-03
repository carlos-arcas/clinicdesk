from __future__ import annotations

import csv
import errno
from dataclasses import dataclass
from datetime import UTC, datetime
from io import StringIO
from typing import Any, Mapping, Protocol

from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.application.usecases.filtros_auditoria import aplicar_preset_rango_auditoria, redactar_texto_filtro_auditoria
from clinicdesk.app.queries.auditoria_accesos_queries import AuditoriaAccesoItemQuery, FiltrosAuditoriaAccesos

COLUMNAS_EXPORTACION_AUDITORIA = (
    "timestamp_utc",
    "usuario",
    "modo_demo",
    "accion",
    "entidad_tipo",
    "entidad_id",
)


LOGGER = get_logger(__name__)

class ExportacionAuditoriaError(Exception):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


class ExportacionAuditoriaDemasiadasFilasError(ExportacionAuditoriaError):
    def __init__(self) -> None:
        super().__init__("demasiadas_filas")


@dataclass(frozen=True, slots=True)
class ExportacionCSVDTO:
    nombre_archivo_sugerido: str
    csv_texto: str
    filas: int


class ExportarAuditoriaCSVGateway(Protocol):
    def buscar_auditoria_accesos(
        self,
        filtros: FiltrosAuditoriaAccesos,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditoriaAccesoItemQuery], int]:
        ...

    def exportar_auditoria_accesos(
        self,
        filtros: FiltrosAuditoriaAccesos,
        max_filas: int | None = None,
    ) -> list[AuditoriaAccesoItemQuery]:
        ...


class ExportarAuditoriaCSV:
    _MAX_FILAS_DEFENSIVO = 10_000

    def __init__(self, gateway: ExportarAuditoriaCSVGateway) -> None:
        self._gateway = gateway

    def execute(self, filtros: FiltrosAuditoriaAccesos, preset_rango: str | None = None) -> ExportacionCSVDTO:
        filtros_finales = aplicar_preset_rango_auditoria(filtros, preset_rango)
        _, total = self._gateway.buscar_auditoria_accesos(filtros_finales, limit=1, offset=0)
        if total > self._MAX_FILAS_DEFENSIVO:
            LOGGER.warning("auditoria_exportacion_denegada_limite", extra=_payload_log_exportacion_auditoria(filtros_finales, "auditoria_exportacion_denegada_limite"))
            raise ExportacionAuditoriaDemasiadasFilasError()
        filas = self._gateway.exportar_auditoria_accesos(filtros_finales, max_filas=self._MAX_FILAS_DEFENSIVO)
        LOGGER.info("auditoria_exportacion_generada", extra=_payload_log_exportacion_auditoria(filtros_finales, "auditoria_exportacion_generada"))
        return ExportacionCSVDTO(
            nombre_archivo_sugerido=_build_file_name(),
            csv_texto=_render_csv(filas),
            filas=len(filas),
        )


def _build_file_name() -> str:
    return f"auditoria_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"


def _render_csv(filas: list[AuditoriaAccesoItemQuery | Mapping[str, Any]]) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(list(COLUMNAS_EXPORTACION_AUDITORIA))
    for item in filas:
        writer.writerow([_obtener_columna_permitida(item, columna) for columna in COLUMNAS_EXPORTACION_AUDITORIA])
    return output.getvalue()


def _obtener_columna_permitida(item: AuditoriaAccesoItemQuery | Mapping[str, Any], columna: str) -> str:
    if isinstance(item, Mapping):
        valor = item.get(columna)
    else:
        valor = getattr(item, columna, None)
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return str(valor)
    return str(valor)


def _payload_log_exportacion_auditoria(filtros: FiltrosAuditoriaAccesos, accion: str) -> dict[str, object]:
    return {
        "action": accion,
        "usuario_contiene": redactar_texto_filtro_auditoria(filtros.usuario_contiene),
        "filtro_accion": filtros.accion,
        "filtro_entidad_tipo": filtros.entidad_tipo,
    }


def mapear_error_exportacion(exc: BaseException) -> str:
    texto_error = str(exc).lower()
    if _es_archivo_en_uso(exc, texto_error):
        return "archivo_en_uso"
    if isinstance(exc, PermissionError):
        return "sin_permisos"
    if _es_ruta_invalida(exc):
        return "ruta_invalida"
    return "io_error"


def _es_archivo_en_uso(exc: BaseException, texto_error: str) -> bool:
    if "winerror 32" in texto_error or "being used" in texto_error:
        return True
    if not isinstance(exc, OSError):
        return False
    if getattr(exc, "winerror", None) == 32:
        return True
    return "being used" in texto_error


def _es_ruta_invalida(exc: BaseException) -> bool:
    if isinstance(exc, FileNotFoundError):
        return True
    if not isinstance(exc, OSError):
        return False
    return exc.errno == errno.ENOENT
