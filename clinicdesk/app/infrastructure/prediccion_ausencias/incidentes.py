from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


def escribir_incidente_entrenamiento(
    base_logs: Path | str,
    *,
    run_id: str,
    request_id: str,
    reason_code: str,
    mensaje_usuario: str,
) -> Path:
    carpeta = Path(base_logs) / "incidents"
    carpeta.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=UTC)
    marca = timestamp.strftime("%Y%m%dT%H%M%S%fZ")
    ruta = carpeta / f"prediccion_entrenar_fail_{marca}_{run_id}.json"
    contenido = {
        "timestamp": timestamp.isoformat(),
        "run_id": run_id,
        "request_id": request_id,
        "reason_code": reason_code,
        "mensaje_usuario": mensaje_usuario,
    }
    ruta.write_text(json.dumps(contenido, ensure_ascii=False), encoding="utf-8")
    return ruta
