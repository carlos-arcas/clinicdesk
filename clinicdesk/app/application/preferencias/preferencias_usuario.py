from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Protocol

MARCADOR_REDACTADO = "[REDACTED]"
_PATRON_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_PATRON_DNI = re.compile(r"^(?:\d{8}[A-Za-z]|[XYZ]\d{7}[A-Za-z])$")
_PATRON_TELEFONO = re.compile(r"^\+?\d[\d\s().-]{7,}\d$")


@dataclass(slots=True)
class PreferenciasUsuario:
    pagina_ultima: str = "home"
    filtros_pacientes: dict[str, Any] = field(default_factory=dict)
    filtros_confirmaciones: dict[str, Any] = field(default_factory=dict)
    last_search_by_context: dict[str, str] = field(default_factory=dict)
    columnas_por_contexto: dict[str, list[str]] = field(default_factory=dict)


class PreferenciasRepository(Protocol):
    def get(self, perfil: str) -> PreferenciasUsuario: ...

    def set(self, perfil: str, preferencias: PreferenciasUsuario) -> None: ...


class PreferenciasService:
    def __init__(self, repositorio: PreferenciasRepository) -> None:
        self._repositorio = repositorio

    def get(self, perfil: str = "default") -> PreferenciasUsuario:
        return self._repositorio.get(perfil)

    def set(self, preferencias: PreferenciasUsuario, perfil: str = "default") -> None:
        self._repositorio.set(perfil, preferencias)


def sanitize_search_text(text: str) -> str | None:
    valor = (text or "").strip()
    if not valor:
        return None
    if _parece_pii(valor):
        return MARCADOR_REDACTADO
    return valor


def _parece_pii(valor: str) -> bool:
    sin_espacios = valor.replace(" ", "")
    if _PATRON_EMAIL.match(valor):
        return True
    if _PATRON_DNI.match(sin_espacios.upper()):
        return True
    if _PATRON_TELEFONO.match(valor) and sum(char.isdigit() for char in valor) >= 9:
        return True
    return False
