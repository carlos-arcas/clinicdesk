from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from clinicdesk.app.common.politica_placeholders_pii import (
    TOKEN_PII_CAMPO_SENSIBLE,
    TOKEN_PII_DIRECCION,
    TOKEN_PII_DNI_NIF,
    TOKEN_PII_EMAIL,
    TOKEN_PII_HISTORIA_CLINICA,
    TOKEN_PII_TELEFONO,
)

_RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_RE_DNI_NIF = re.compile(r"\b(?:\d{7,8}[A-Za-z]?|[A-Za-z]\d{7,8}[A-Za-z]?)\b")
_RE_TELEFONO = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)")
_RE_HISTORIA = re.compile(r"\b(?:hc|historia(?:\s+cl[ií]nica)?)\s*[:#-]?\s*[A-Za-z0-9-]{3,}\b", re.IGNORECASE)
_RE_DIRECCION = re.compile(r"\b(?:c/|calle|avda\.?|avenida|paseo|plaza)\b", re.IGNORECASE)

_PATRONES_CLAVE_SENSIBLE: tuple[re.Pattern[str], ...] = (
    re.compile(r"email|correo|mail", re.IGNORECASE),
    re.compile(r"telefono|teléfono|tlf|movil|móvil", re.IGNORECASE),
    re.compile(r"dni|nif|documento", re.IGNORECASE),
    re.compile(r"historia[_\s]?clinica|historia[_\s]?clínica|hc", re.IGNORECASE),
    re.compile(r"direccion|dirección", re.IGNORECASE),
    re.compile(r"identificador|id[_\s]?(?:paciente|persona|clinico|cl[ií]nico)", re.IGNORECASE),
)


def redactar_texto_pii(texto: str) -> tuple[str, bool]:
    redacted = _RE_EMAIL.sub(TOKEN_PII_EMAIL, texto)
    redacted = _RE_DNI_NIF.sub(TOKEN_PII_DNI_NIF, redacted)
    redacted = _RE_TELEFONO.sub(TOKEN_PII_TELEFONO, redacted)
    redacted = _RE_HISTORIA.sub(TOKEN_PII_HISTORIA_CLINICA, redacted)
    redacted = _RE_DIRECCION.sub(TOKEN_PII_DIRECCION, redacted)
    return redacted, redacted != texto


def sanear_valor_pii(value: Any, *, clave: str | None = None) -> tuple[Any, bool]:
    if value is None:
        return None, False
    if clave and _es_clave_sensible(clave):
        return TOKEN_PII_CAMPO_SENSIBLE, True
    if isinstance(value, str):
        return redactar_texto_pii(value)
    if isinstance(value, Mapping):
        saneado: dict[str, Any] = {}
        redaccion_aplicada = False
        for nested_key, nested_value in value.items():
            nested_saneado, nested_redactado = sanear_valor_pii(nested_value, clave=str(nested_key))
            saneado[str(nested_key)] = nested_saneado
            redaccion_aplicada = redaccion_aplicada or nested_redactado
        return saneado, redaccion_aplicada
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        saneada_lista: list[Any] = []
        redaccion_aplicada = False
        for item in value:
            item_saneado, item_redactado = sanear_valor_pii(item, clave=clave)
            saneada_lista.append(item_saneado)
            redaccion_aplicada = redaccion_aplicada or item_redactado
        return saneada_lista, redaccion_aplicada
    return value, False


def _es_clave_sensible(clave: str) -> bool:
    return any(pattern.search(clave) for pattern in _PATRONES_CLAVE_SENSIBLE)
