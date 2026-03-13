from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from clinicdesk.app.application.seguridad_salida import serializar_cita_api_demo, serializar_paciente_api_demo
from clinicdesk.web.api.seguridad import validar_api_key
from clinicdesk.web.api.servicio_consultas import FiltrosCitasApi, ServicioConsultasApi


router = APIRouter(prefix="/api/v1", dependencies=[Depends(validar_api_key)])


def get_servicio_api() -> ServicioConsultasApi:  # pragma: no cover - se sobreescribe en app.py
    raise RuntimeError("Dependencia de servicio no configurada")


@router.get("/citas")
def get_citas(
    desde: str | None = Query(default=None),
    hasta: str | None = Query(default=None),
    estado: str = Query(default=""),
    texto: str = Query(default=""),
    servicio: ServicioConsultasApi = Depends(get_servicio_api),
) -> list[dict[str, object]]:
    _validar_rango(desde, hasta)
    filas = servicio.listar_citas(FiltrosCitasApi(desde=desde, hasta=hasta, estado=estado, texto=texto))
    return [serializar_cita_api_demo(fila) for fila in filas]


@router.get("/pacientes")
def get_pacientes(
    texto: str = Query(default=""),
    servicio: ServicioConsultasApi = Depends(get_servicio_api),
) -> list[dict[str, object]]:
    filas = servicio.buscar_pacientes(texto)
    return [serializar_paciente_api_demo(fila) for fila in filas]


def _validar_rango(desde: str | None, hasta: str | None) -> None:
    if desde:
        _validar_fecha_iso(desde, "desde")
    if hasta:
        _validar_fecha_iso(hasta, "hasta")
    if desde and hasta and desde > hasta:
        raise HTTPException(status_code=422, detail="El rango de fechas es inválido: desde > hasta.")


def _validar_fecha_iso(valor: str, nombre: str) -> None:
    try:
        date.fromisoformat(valor)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Fecha inválida en '{nombre}' (YYYY-MM-DD).") from exc
