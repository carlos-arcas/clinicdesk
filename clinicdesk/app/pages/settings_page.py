from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SettingsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("⚙️ Ajustes"))