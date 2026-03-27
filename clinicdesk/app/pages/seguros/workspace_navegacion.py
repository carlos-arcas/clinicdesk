from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


SECCIONES_WORKSPACE_SEGUROS: tuple[str, ...] = (
    "preventa",
    "cartera",
    "campanias",
    "analitica",
    "agenda",
    "postventa",
    "economia",
)


@dataclass(slots=True)
class EstadoWorkspaceSeguros:
    seccion_activa: str = "cartera"

    def seleccionar(self, seccion: str) -> str:
        self.seccion_activa = normalizar_seccion_workspace(seccion)
        return self.seccion_activa


def normalizar_seccion_workspace(seccion: str | None) -> str:
    if seccion in SECCIONES_WORKSPACE_SEGUROS:
        return str(seccion)
    return SECCIONES_WORKSPACE_SEGUROS[0]


def construir_opciones_selector(i18n) -> list[tuple[str, str]]:
    return [(i18n.t(f"seguros.workspace.seccion.{seccion}"), seccion) for seccion in SECCIONES_WORKSPACE_SEGUROS]


def indice_seccion(seccion: str) -> int:
    return SECCIONES_WORKSPACE_SEGUROS.index(normalizar_seccion_workspace(seccion))


def restaurar_seccion_preferida(
    estado: EstadoWorkspaceSeguros,
    secciones_disponibles: Iterable[str] | None = None,
) -> str:
    if secciones_disponibles is None:
        return normalizar_seccion_workspace(estado.seccion_activa)
    disponibles = set(secciones_disponibles)
    if estado.seccion_activa in disponibles:
        return estado.seccion_activa
    return SECCIONES_WORKSPACE_SEGUROS[0]
