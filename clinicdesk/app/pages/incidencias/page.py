from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.container import AppContainer
from clinicdesk.app.domain.enums import EstadoIncidencia, SeveridadIncidencia, TipoIncidencia
from clinicdesk.app.queries.incidencias_queries import IncidenciasQueries, IncidenciaRow


class PageIncidencias(QWidget):
    def __init__(self, container: AppContainer, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._queries = IncidenciasQueries(container.connection)

        self._build_ui()
        self._connect_signals()
        self._refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        filters = QHBoxLayout()
        self.cbo_tipo = QComboBox()
        self.cbo_tipo.addItem("Todos")
        self.cbo_tipo.addItems([t.value for t in TipoIncidencia])
        self.cbo_tipo.addItems(["STOCK", "DISPENSACION", "CITA", "CALENDARIO"])

        self.cbo_estado = QComboBox()
        self.cbo_estado.addItem("Todos")
        self.cbo_estado.addItems([e.value for e in EstadoIncidencia])
        self.cbo_estado.addItems(["ABIERTA", "EN_REVISION", "RESUELTA", "DESCARTADA", "CERRADA"])

        self.cbo_severidad = QComboBox()
        self.cbo_severidad.addItem("Todos")
        self.cbo_severidad.addItems([s.value for s in SeveridadIncidencia])
        self.cbo_severidad.addItems(["BAJA", "MEDIA", "ALTA"])

        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(QDate.currentDate().addMonths(-1))
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(QDate.currentDate())

        self.txt_texto = QLineEdit()
        self.btn_filtrar = QPushButton("Filtrar")

        filters.addWidget(QLabel("Tipo"))
        filters.addWidget(self.cbo_tipo)
        filters.addWidget(QLabel("Estado"))
        filters.addWidget(self.cbo_estado)
        filters.addWidget(QLabel("Severidad"))
        filters.addWidget(self.cbo_severidad)
        filters.addWidget(QLabel("Desde"))
        filters.addWidget(self.date_desde)
        filters.addWidget(QLabel("Hasta"))
        filters.addWidget(self.date_hasta)
        filters.addWidget(QLabel("Texto"))
        filters.addWidget(self.txt_texto)
        filters.addWidget(self.btn_filtrar)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Fecha", "Tipo", "Severidad", "Estado", "Descripción"]
        )
        self.table.setColumnHidden(0, False)
        self.table.horizontalHeader().setStretchLastSection(True)

        detail_layout = QFormLayout()
        self.lbl_confirmado_por = QLabel("—")
        self.lbl_referencias = QLabel("—")
        self.txt_descripcion = QTextEdit()
        self.txt_descripcion.setReadOnly(True)
        self.txt_nota_override = QTextEdit()
        self.txt_nota_override.setReadOnly(True)

        self.cbo_estado_update = QComboBox()
        self.cbo_estado_update.addItems(["ABIERTA", "EN_REVISION", "RESUELTA", "DESCARTADA"])
        self.btn_estado = QPushButton("Cambiar estado")

        detail_layout.addRow("Confirmado por", self.lbl_confirmado_por)
        detail_layout.addRow("Referencias", self.lbl_referencias)
        detail_layout.addRow("Descripción", self.txt_descripcion)
        detail_layout.addRow("Nota override", self.txt_nota_override)
        detail_layout.addRow("Nuevo estado", self.cbo_estado_update)
        detail_layout.addRow("", self.btn_estado)

        root.addLayout(filters)
        root.addWidget(QLabel("Listado"))
        root.addWidget(self.table, 3)
        root.addWidget(QLabel("Detalle"))
        root.addLayout(detail_layout, 2)

    def _connect_signals(self) -> None:
        self.btn_filtrar.clicked.connect(self._refresh)
        self.table.itemSelectionChanged.connect(self._load_detail)
        self.btn_estado.clicked.connect(self._change_estado)

    def on_show(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        tipo = self._combo_value(self.cbo_tipo)
        estado = self._combo_value(self.cbo_estado)
        severidad = self._combo_value(self.cbo_severidad)
        fecha_desde = self.date_desde.date().toString("yyyy-MM-dd")
        fecha_hasta = self.date_hasta.date().toString("yyyy-MM-dd")
        texto = self.txt_texto.text().strip() or None

        rows = self._queries.list(
            tipo=tipo,
            estado=estado,
            severidad=severidad,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            texto=texto,
        )
        self._render_table(rows)

    def _render_table(self, rows: list[IncidenciaRow]) -> None:
        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(r.id)))
            self.table.setItem(row, 1, QTableWidgetItem(r.fecha_hora))
            self.table.setItem(row, 2, QTableWidgetItem(r.tipo))
            self.table.setItem(row, 3, QTableWidgetItem(r.severidad))
            self.table.setItem(row, 4, QTableWidgetItem(r.estado))
            short_desc = r.descripcion.split("\n")[0][:80]
            self.table.setItem(row, 5, QTableWidgetItem(short_desc))

    def _load_detail(self) -> None:
        incidencia_id = self._selected_id()
        if incidencia_id is None:
            return

        row = self._queries.get_by_id(incidencia_id)
        if not row:
            return

        self.lbl_confirmado_por.setText(row.confirmado_por_nombre)
        refs = []
        if row.cita_id:
            refs.append(f"Cita #{row.cita_id}")
        if row.receta_id:
            refs.append(f"Receta #{row.receta_id}")
        if row.dispensacion_id:
            refs.append(f"Dispensación #{row.dispensacion_id}")
        if row.medico_nombre:
            refs.append(f"Médico: {row.medico_nombre}")
        if row.personal_nombre:
            refs.append(f"Personal: {row.personal_nombre}")
        self.lbl_referencias.setText(" | ".join(refs) if refs else "—")
        self.txt_descripcion.setPlainText(row.descripcion)
        self.txt_nota_override.setPlainText(row.nota_override or "")
        if row.estado:
            self.cbo_estado_update.setCurrentText(row.estado)

    def _change_estado(self) -> None:
        incidencia_id = self._selected_id()
        if incidencia_id is None:
            return

        nuevo_estado = self.cbo_estado_update.currentText()
        try:
            self._container.incidencias_repo.update_state(incidencia_id, nuevo_estado)
        except Exception as exc:
            QMessageBox.warning(self, "Incidencias", str(exc))
            return

        self._refresh()

    def _selected_id(self) -> Optional[int]:
        items = self.table.selectedItems()
        if not items:
            return None
        try:
            return int(items[0].text())
        except ValueError:
            return None

    @staticmethod
    def _combo_value(combo: QComboBox) -> Optional[str]:
        value = combo.currentText()
        return None if value == "Todos" else value
