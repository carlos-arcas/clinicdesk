from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QPushButton, QWidget


def set_buttons_enabled(*, has_selection: bool, buttons: list[QPushButton]) -> None:
    for button in buttons:
        button.setEnabled(has_selection)


def confirm_deactivation(parent: QWidget, *, module_title: str, entity_label: str) -> bool:
    message = (
        f"¿Desactivar {entity_label}?\n"
        "El registro permanecerá en el sistema como inactivo."
    )
    return (
        QMessageBox.question(
            parent,
            module_title,
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        == QMessageBox.Yes
    )
