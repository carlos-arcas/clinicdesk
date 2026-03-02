from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResultadoListadoDTO:
    items: tuple[dict[str, object], ...]
    total: int


@dataclass(frozen=True, slots=True)
class ResumenHistorialDTO:
    total_citas: int
    no_presentados: int
    total_recetas: int
    recetas_activas: int


@dataclass(frozen=True, slots=True)
class ErrorValidacionDTO:
    code: str
    i18n_key: str
    campo: str | None


@dataclass(frozen=True, slots=True)
class ResultadoValidacionDTO:
    ok: bool
    errores: tuple[ErrorValidacionDTO, ...]
