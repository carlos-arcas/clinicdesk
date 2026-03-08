from __future__ import annotations

import re

CLAVES_METADATA_AUDITORIA_PERMITIDAS: frozenset[str] = frozenset(
    {
        "origen",
        "modulo",
        "vista",
        "accion_ui",
        "reason_code",
        "duracion_ms",
        "resultado",
        "contexto",
    }
)

CLAVES_CONTEXTO_TELEMETRIA_PERMITIDAS: frozenset[str] = frozenset(
    {
        "page",
        "origen",
        "tipo",
        "clave",
        "resultado",
        "destino",
        "vista",
        "found",
        "modulo",
        "accion_ui",
        "reason_code",
        "contexto",
        "tab",
        "detalle",
    }
)

PATRONES_CLAVE_SENSIBLE_AUDITORIA_TELEMETRIA: tuple[re.Pattern[str], ...] = (
    re.compile(r"email", re.IGNORECASE),
    re.compile(r"telefono|teléfono|tlf|movil|móvil", re.IGNORECASE),
    re.compile(r"dni|nif", re.IGNORECASE),
    re.compile(r"historia[_\s]?clinica|historia[_\s]?clínica", re.IGNORECASE),
    re.compile(r"direccion|dirección", re.IGNORECASE),
)


def es_clave_sensible_auditoria_telemetria(clave: str) -> bool:
    return any(pattern.search(clave) for pattern in PATRONES_CLAVE_SENSIBLE_AUDITORIA_TELEMETRIA)
