from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtCore import QCoreApplication
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.pages.pacientes.workers_pacientes import RelayCargaPacientes


@pytest.mark.ui
@pytest.mark.uiqt
def test_relay_carga_pacientes_emite_contexto_tipado_en_hilo_principal() -> None:
    app = QCoreApplication.instance() or QCoreApplication([])
    relay = RelayCargaPacientes(token=7, seleccion_id=42)
    relay.moveToThread(app.thread())

    eventos: list[tuple[str, object]] = []
    relay.carga_ok.connect(lambda payload, token, selected_id: eventos.append(("ok", (payload, token, selected_id))))
    relay.carga_error.connect(lambda error, token: eventos.append(("error", (error, token))))
    relay.hilo_finalizado.connect(lambda token: eventos.append(("fin", token)))

    relay.on_worker_ok({"rows": [1], "total_base": 1})
    relay.on_worker_error("RuntimeError")
    relay.on_hilo_finalizado()

    assert eventos == [
        ("ok", ({"rows": [1], "total_base": 1}, 7, 42)),
        ("error", ("RuntimeError", 7)),
        ("fin", 7),
    ]
