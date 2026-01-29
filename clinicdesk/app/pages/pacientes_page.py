from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.application.pacientes_usecases import ListarPacientes, CrearPaciente
# Importamos casos de uso (application) para que la UI no dependa de infraestructura/SQLite.


class PacientesPage(QWidget):
    def __init__(self, listar_pacientes: ListarPacientes, crear_paciente: CrearPaciente) -> None:
        super().__init__()
        self.listar_pacientes = listar_pacientes
        self.crear_paciente = crear_paciente

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Pacientes"))

        formulario = QFormLayout()
        self.entrada_nombre = QLineEdit()
        self.entrada_telefono = QLineEdit()

        formulario.addRow("Nombre", self.entrada_nombre)
        formulario.addRow("Teléfono", self.entrada_telefono)

        botones = QHBoxLayout()
        self.boton_guardar = QPushButton("Guardar")
        botones.addWidget(self.boton_guardar)

        layout.addLayout(formulario)
        layout.addLayout(botones)

        self.tabla = QTableWidget(0, 3)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Teléfono"])
        layout.addWidget(self.tabla, 1)

        self.boton_guardar.clicked.connect(self._guardar)

    def on_show(self) -> None:
        """Hook llamado por MainWindow al mostrar la página."""
        self.recargar()

    def recargar(self) -> None:
        pacientes = self.listar_pacientes.ejecutar()
        self.tabla.setRowCount(0)

        for p in pacientes:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            self.tabla.setItem(fila, 0, QTableWidgetItem(str(p.id)))
            self.tabla.setItem(fila, 1, QTableWidgetItem(p.nombre))
            self.tabla.setItem(fila, 2, QTableWidgetItem(p.telefono))

    def _guardar(self) -> None:
        try:
            self.crear_paciente.ejecutar(
                self.entrada_nombre.text(),
                self.entrada_telefono.text(),
            )
        except ValueError as e:
            QMessageBox.warning(self, "Validación", str(e))
            return

        self.entrada_nombre.clear()
        self.entrada_telefono.clear()
        self.recargar()
