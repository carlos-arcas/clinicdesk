from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

_STATE_COLORS = {"ok": "#1b8f3d", "warn": "#c58900", "bad": "#b3261e", "neutral": "#8892a0"}


class KpiCard(QFrame):
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self._title = QLabel(title)
        self._value = QLabel("—")
        self._subtitle = QLabel("")
        self._title.setObjectName("kpiTitle")
        self._value.setObjectName("kpiValue")
        self._subtitle.setObjectName("kpiSubtitle")
        self._subtitle.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addWidget(self._value)
        layout.addWidget(self._subtitle)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._apply_style("neutral")

    def set_data(self, value: str, subtitle: str = "", state: str = "neutral") -> None:
        self._value.setText(value)
        self._subtitle.setText(subtitle)
        self._apply_style(state)

    def _apply_style(self, state: str) -> None:
        color = _STATE_COLORS.get(state, _STATE_COLORS["neutral"])
        self.setStyleSheet(
            "QFrame {border: 2px solid "
            f"{color}; border-radius: 8px; padding: 8px; background: #ffffff;}}"
            "QLabel#kpiTitle {font-size: 12px; color: #425466;}"
            "QLabel#kpiValue {font-size: 22px; font-weight: 700; color: #0f172a;}"
            f"QLabel#kpiSubtitle {{font-size: 11px; color: {color};}}"
        )
