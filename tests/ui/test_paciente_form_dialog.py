from __future__ import annotations

from PySide6.QtWidgets import QMessageBox

from clinicdesk.app.pages.pacientes.dialogs.paciente_form import PacienteFormDialog


def test_paciente_form_validacion_inline_y_cta(qtbot) -> None:
    dialog = PacienteFormDialog()
    qtbot.addWidget(dialog)

    assert not dialog._btn_guardar.isEnabled()

    qtbot.keyClicks(dialog.txt_documento, "12345678A")
    qtbot.keyClicks(dialog.txt_nombre, "Ana")
    qtbot.keyClicks(dialog.txt_apellidos, "Pérez")

    assert dialog._btn_guardar.isEnabled()

    dialog.txt_email.setText("email-invalido")
    assert not dialog._btn_guardar.isEnabled()
    assert dialog._labels_error["email"].isVisible()


def test_paciente_form_confirma_descartar_cambios(monkeypatch, qtbot) -> None:
    dialog = PacienteFormDialog()
    qtbot.addWidget(dialog)
    dialog.txt_documento.setText("DOC-1")

    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.No)
    dialog.reject()
    assert dialog.result() == 0

    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)
    dialog.reject()
    assert dialog.result() == QMessageBox.Rejected


def test_paciente_form_prevenir_doble_guardado(monkeypatch, qtbot) -> None:
    dialog = PacienteFormDialog()
    qtbot.addWidget(dialog)
    dialog.txt_documento.setText("12345678A")
    dialog.txt_nombre.setText("Ana")
    dialog.txt_apellidos.setText("Pérez")

    llamados = {"accept": 0}

    def _accept_once() -> None:
        llamados["accept"] += 1

    monkeypatch.setattr(dialog, "accept", _accept_once)
    dialog._on_guardar_click()
    dialog._on_guardar_click()

    assert llamados["accept"] == 1


def test_paciente_form_foco_en_primer_error(qtbot) -> None:
    dialog = PacienteFormDialog()
    qtbot.addWidget(dialog)
    dialog._on_guardar_click()
    assert dialog.txt_documento.hasFocus()
