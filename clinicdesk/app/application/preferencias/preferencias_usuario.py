from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Protocol

_PATRON_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_PATRON_DNI = re.compile(r"^(?:\d{8}[A-Za-z]|[XYZ]\d{7}[A-Za-z])$")
_PATRON_TELEFONO = re.compile(r"^\+?\d[\d\s().-]{7,}\d$")
_PATRON_DIRECCION = re.compile(
    r"\b(?:calle|avda\.?|avenida|plaza|paseo|c/|numero|nº|portal|piso|puerta)\b", re.IGNORECASE
)
_LONGITUD_MAXIMA_BUSQUEDA = 120

ValorFiltro = str | int | bool | None
ValorColumna = int | str


@dataclass(slots=True)
class PreferenciasUsuario:
    pagina_ultima: str | None = None
    restaurar_pagina_ultima_en_arranque: bool = False
    filtros_pacientes: dict[str, ValorFiltro] = field(default_factory=dict)
    filtros_confirmaciones: dict[str, ValorFiltro] = field(default_factory=dict)
    last_search_by_context: dict[str, str] = field(default_factory=dict)
    columnas_por_contexto: dict[str, dict[str, ValorColumna]] = field(default_factory=dict)


class PreferenciasRepository(Protocol):
    def get(self, perfil_id: str | None) -> PreferenciasUsuario: ...

    def set(self, perfil_id: str | None, preferencias: PreferenciasUsuario) -> None: ...


class PreferenciasService:
    def __init__(self, repositorio: PreferenciasRepository) -> None:
        self._repositorio = repositorio

    def get(self, perfil_id: str | None = None) -> PreferenciasUsuario:
        return self._repositorio.get(perfil_id)

    def set(self, prefs: PreferenciasUsuario, perfil_id: str | None = None) -> None:
        self._repositorio.set(perfil_id, prefs)


def sanitize_search_text(text: str) -> str | None:
    """Normaliza texto de búsqueda y bloquea persistencia de posibles PII.

    Política: ante sospecha de PII o entrada abusiva, devuelve ``None`` para no persistir.
    """

    texto_normalizado = " ".join((text or "").strip().split())
    if not texto_normalizado or len(texto_normalizado) > _LONGITUD_MAXIMA_BUSQUEDA:
        return None
    if _parece_pii(texto_normalizado):
        return None
    return texto_normalizado


def _parece_pii(valor: str) -> bool:
    sin_espacios = valor.replace(" ", "")
    if _PATRON_EMAIL.match(valor):
        return True
    if _PATRON_DNI.match(sin_espacios.upper()):
        return True
    if _PATRON_TELEFONO.match(valor) and sum(char.isdigit() for char in valor) >= 9:
        return True
    if _PATRON_DIRECCION.search(valor):
        return True
    return False
