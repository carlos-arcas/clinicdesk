from __future__ import annotations

from pathlib import Path

_CLAVE_ULTIMA_RUTA_EXPORTACION = "auditoria/exportacion/ultima_ruta"


def clave_ultima_ruta_exportacion_auditoria() -> str:
    return _CLAVE_ULTIMA_RUTA_EXPORTACION


def normalizar_ruta_sugerida_exportacion(ultima_ruta: str | None, nombre_archivo: str) -> str:
    if ultima_ruta:
        path = Path(ultima_ruta)
        if path.suffix.lower() == ".csv":
            return str(path.with_name(nombre_archivo))
        return str(path / nombre_archivo)
    return nombre_archivo
