from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from clinicdesk.app.application.historial_paciente.atributos import AtributoHistorial, sanear_columnas_solicitadas
from clinicdesk.app.application.historial_paciente.filtros import FiltrosHistorialPacienteDTO

BASE_KEY = "historial_paciente"


@dataclass(frozen=True, slots=True)
class EstadoPersistidoFiltros:
    preset: str
    desde_iso: str | None
    hasta_iso: str | None
    texto: str | None
    estado: str | None


def serializar_filtros(filtros: FiltrosHistorialPacienteDTO) -> EstadoPersistidoFiltros:
    estado = filtros.estados[0] if filtros.estados else None
    return EstadoPersistidoFiltros(
        preset=filtros.rango_preset,
        desde_iso=_to_iso(filtros.desde),
        hasta_iso=_to_iso(filtros.hasta),
        texto=filtros.texto,
        estado=estado,
    )


def deserializar_filtros(paciente_id: int, data: EstadoPersistidoFiltros) -> FiltrosHistorialPacienteDTO:
    return FiltrosHistorialPacienteDTO(
        paciente_id=paciente_id,
        rango_preset=data.preset,
        desde=_from_iso(data.desde_iso),
        hasta=_from_iso(data.hasta_iso),
        texto=data.texto,
        estados=(data.estado,) if data.estado else None,
    )


def sanear_columnas_guardadas(valor: str | None) -> tuple[str, ...]:
    if not valor:
        return ()
    columnas = [item.strip() for item in valor.split(",") if item.strip()]
    return tuple(dict.fromkeys(columnas))


def serializar_columnas(columnas: tuple[str, ...]) -> str:
    return ",".join(columnas)


def aplicar_columnas_seguras_desde_settings(
    valor_settings: str | None,
    contrato: tuple[AtributoHistorial, ...],
) -> tuple[tuple[str, ...], bool]:
    columnas_guardadas = sanear_columnas_guardadas(valor_settings)
    return sanear_columnas_solicitadas(columnas_guardadas, contrato)


def key_filtros() -> str:
    return f"{BASE_KEY}/filtros"


def key_columnas(tabla: str) -> str:
    return f"{BASE_KEY}/columnas/{tabla}"


def _to_iso(valor: datetime | None) -> str | None:
    return valor.isoformat() if valor else None


def _from_iso(valor: str | None) -> datetime | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        return None
