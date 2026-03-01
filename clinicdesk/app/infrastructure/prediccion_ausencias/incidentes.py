from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_INVALID_WINDOWS_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]')
_MAX_ERROR_MESSAGE_LEN = 300


def nombre_incidente_seguro(run_id: str, timestamp: datetime) -> str:
    marca = timestamp.astimezone(UTC).strftime("%Y%m%d_%H%M%S")
    run_id_seguro = _sanitizar_fragmento_filename(run_id)
    return f"prediccion_entrenar_fail_{marca}_{run_id_seguro}.json"


def escribir_incidente_entrenamiento(
    base_logs: Path | str,
    *,
    run_id: str,
    request_id: str,
    reason_code: str,
    error_type: str,
    error_message: str,
    stage: str = "entrenar",
) -> Path:
    carpeta = Path(base_logs) / "incidents"
    carpeta.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=UTC)
    ruta = carpeta / nombre_incidente_seguro(run_id, timestamp)
    contenido = {
        "timestamp_utc": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_id": run_id,
        "request_id": request_id,
        "reason_code": reason_code,
        "error_type": error_type,
        "error_message": _limitar_texto(error_message),
        "stage": stage,
    }
    with ruta.open("w", encoding="utf-8") as file:
        json.dump(contenido, file, ensure_ascii=False, indent=2)
        file.flush()
        os.fsync(file.fileno())
    return ruta


def _sanitizar_fragmento_filename(value: str) -> str:
    limpio = _INVALID_WINDOWS_FILENAME_CHARS.sub("_", value.strip())
    return limpio or "sin_run_id"


def _limitar_texto(value: str, max_len: int = _MAX_ERROR_MESSAGE_LEN) -> str:
    texto = (value or "").strip()
    return texto[:max_len]


def construir_payload_incidente(*, run_id: str, request_id: str, reason_code: str, error_type: str, error_message: str) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "request_id": request_id,
        "reason_code": reason_code,
        "error_type": error_type,
        "error_message": _limitar_texto(error_message),
    }
