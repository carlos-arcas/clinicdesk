from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtWidgets import QMessageBox
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

pytestmark = [pytest.mark.ui, pytest.mark.uiqt]


def test_cita_form_cta_habilitado_con_campos_minimos(crear_dialogo_cita, completar_campos_minimos_cita) -> None:
    dialogo = crear_dialogo_cita()

    assert not dialogo.btn_ok.isEnabled()

    completar_campos_minimos_cita(dialogo)
    assert dialogo.btn_ok.isEnabled()


def test_cita_form_confirma_descartar_cambios(monkeypatch, crear_dialogo_cita) -> None:
    dialogo = crear_dialogo_cita()
    dialogo.ed_motivo.setText("Control")

    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.No)
    dialogo.reject()
    assert dialogo.result() == 0

    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)
    dialogo.reject()
    assert dialogo.result() == QMessageBox.Rejected


def test_cita_form_prevenir_doble_submit(
    monkeypatch,
    crear_dialogo_cita,
    completar_campos_minimos_cita,
) -> None:
    dialogo = crear_dialogo_cita()
    completar_campos_minimos_cita(dialogo)

    llamados = {"accept": 0}

    def _accept_once() -> None:
        llamados["accept"] += 1

    monkeypatch.setattr(dialogo, "accept", _accept_once)

    dialogo._on_ok()
    dialogo._on_ok()

    assert llamados["accept"] == 1


def test_cita_form_foco_en_primer_error(qtbot, crear_dialogo_cita) -> None:
    dialogo = crear_dialogo_cita()
    dialogo.show()
    qtbot.waitUntil(dialogo.isVisible)
    dialogo.ed_fin.setFocus()
    qtbot.waitUntil(dialogo.ed_fin.hasFocus)
    dialogo._on_ok()
    qtbot.waitUntil(dialogo.ed_inicio.hasFocus)
    assert dialogo.ed_inicio.hasFocus()
