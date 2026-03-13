from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtWidgets import QMessageBox
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

pytestmark = [pytest.mark.ui, pytest.mark.uiqt]


def test_paciente_form_validacion_inline_y_cta(
    qtbot,
    crear_dialogo_paciente,
    completar_campos_minimos_paciente,
) -> None:
    dialogo = crear_dialogo_paciente()

    assert not dialogo._btn_guardar.isEnabled()

    completar_campos_minimos_paciente(dialogo)
    assert dialogo._btn_guardar.isEnabled()

    dialogo.txt_email.setText("email-invalido")
    assert not dialogo._btn_guardar.isEnabled()
    assert dialogo._labels_error["email"].isVisible()


def test_paciente_form_confirma_descartar_cambios(monkeypatch, crear_dialogo_paciente) -> None:
    dialogo = crear_dialogo_paciente()
    dialogo.txt_documento.setText("DOC-1")

    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.No)
    dialogo.reject()
    assert dialogo.result() == 0

    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)
    dialogo.reject()
    assert dialogo.result() == QMessageBox.Rejected


def test_paciente_form_prevenir_doble_guardado(
    monkeypatch,
    crear_dialogo_paciente,
    completar_campos_minimos_paciente,
) -> None:
    dialogo = crear_dialogo_paciente()
    completar_campos_minimos_paciente(dialogo)

    llamados = {"accept": 0}

    def _accept_once() -> None:
        llamados["accept"] += 1

    monkeypatch.setattr(dialogo, "accept", _accept_once)
    dialogo._on_guardar_click()
    dialogo._on_guardar_click()

    assert llamados["accept"] == 1


def test_paciente_form_foco_en_primer_error(crear_dialogo_paciente) -> None:
    dialogo = crear_dialogo_paciente()
    dialogo._on_guardar_click()
    assert dialogo.txt_documento.hasFocus()
