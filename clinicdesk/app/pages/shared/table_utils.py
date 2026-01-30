from __future__ import annotations

from typing import Optional

from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem


INACTIVE_FOREGROUND = QBrush(QColor("#7a7a7a"))
INACTIVE_BACKGROUND = QBrush(QColor("#f2f2f2"))


def apply_row_style(
    table: QTableWidget,
    row: int,
    *,
    inactive: bool = False,
    tooltip: Optional[str] = None,
) -> None:
    for col in range(table.columnCount()):
        item = table.item(row, col)
        if not item:
            continue
        if tooltip:
            item.setToolTip(tooltip)
        if inactive:
            item.setForeground(INACTIVE_FOREGROUND)
            item.setBackground(INACTIVE_BACKGROUND)


def set_item(table: QTableWidget, row: int, col: int, value: str) -> QTableWidgetItem:
    item = QTableWidgetItem(value)
    table.setItem(row, col, item)
    return item
