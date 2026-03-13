from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_API", "pyside6")


@pytest.fixture()
def crear_dialogo_paciente(qtbot) -> Callable[[], Any]:
    def _crear() -> Any:
        from clinicdesk.app.pages.pacientes.dialogs.paciente_form import PacienteFormDialog

        dialogo = PacienteFormDialog()
        qtbot.addWidget(dialogo)
        return dialogo

    return _crear


@pytest.fixture()
def crear_dialogo_cita(qtbot, container) -> Callable[[], Any]:
    def _crear() -> Any:
        from clinicdesk.app.pages.citas.dialogs.dialog_cita_form import CitaFormDialog

        dialogo = CitaFormDialog(default_date="2025-01-01", container=container)
        qtbot.addWidget(dialogo)
        return dialogo

    return _crear


@pytest.fixture()
def completar_campos_minimos_paciente() -> Callable[[Any], None]:
    def _completar(dialogo: Any) -> None:
        dialogo.txt_documento.setText("12345678A")
        dialogo.txt_nombre.setText("Ana")
        dialogo.txt_apellidos.setText("Pérez")

    return _completar


@pytest.fixture()
def completar_campos_minimos_cita() -> Callable[[Any], None]:
    def _completar(dialogo: Any) -> None:
        dialogo._paciente_id = 1
        dialogo._medico_id = 2
        dialogo._sala_id = 3
        dialogo.ed_paciente.setText("Paciente 1")
        dialogo.ed_medico.setText("Médico 2")
        dialogo.ed_sala.setText("Sala 3")
        dialogo._on_form_changed()

    return _completar
