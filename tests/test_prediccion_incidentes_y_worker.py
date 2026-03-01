from __future__ import annotations

import json
from datetime import UTC, datetime

from clinicdesk.app.application.prediccion_ausencias import EntrenamientoPrediccionError
from clinicdesk.app.infrastructure.prediccion_ausencias.incidentes import (
    escribir_incidente_entrenamiento,
    nombre_incidente_seguro,
)
from clinicdesk.app.pages.prediccion_ausencias.entrenar_worker import construir_payload_error_entrenamiento


def test_nombre_incidente_seguro_sin_caracteres_invalidos() -> None:
    dt = datetime(2026, 3, 1, 17, 53, 28, tzinfo=UTC)
    nombre = nombre_incidente_seguro("run:id?*test", dt)

    assert nombre == "prediccion_entrenar_fail_20260301_175328_run_id__test.json"
    assert ":" not in nombre
    for invalid in '<>:"/\\|?*':
        assert invalid not in nombre


def test_escribir_incidente_entrenamiento_crea_directorio_y_json(tmp_path) -> None:
    ruta = escribir_incidente_entrenamiento(
        tmp_path / "logs",
        run_id="run-01",
        request_id="req-01",
        reason_code="save_failed",
        error_type="OSError",
        error_message="No se pudo escribir el archivo",
        stage="entrenar",
    )

    assert ruta.exists()
    assert ruta.parent.name == "incidents"
    contenido = json.loads(ruta.read_text(encoding="utf-8"))
    assert contenido["run_id"] == "run-01"
    assert contenido["request_id"] == "req-01"
    assert contenido["reason_code"] == "save_failed"
    assert contenido["error_type"] == "OSError"
    assert contenido["error_message"] == "No se pudo escribir el archivo"
    assert contenido["stage"] == "entrenar"


def test_construir_payload_error_entrenamiento_propaga_reason_code() -> None:
    err = EntrenamientoPrediccionError("dataset_empty")
    payload = construir_payload_error_entrenamiento(err)

    assert payload.reason_code == "dataset_empty"
    assert payload.error_type == "EntrenamientoPrediccionError"
    assert payload.error_message == "dataset_empty"
