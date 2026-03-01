from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.application.auditoria_acceso import AccionAuditoriaAcceso, EntidadAuditoriaAcceso
from clinicdesk.app.application.usecases.buscar_auditoria_accesos import BuscarAuditoriaAccesos
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.shared.table_utils import set_item
from clinicdesk.app.queries.auditoria_accesos_queries import AuditoriaAccesosQueries, FiltrosAuditoriaAccesos


@dataclass(frozen=True, slots=True)
class _FiltroCombo:
    key_i18n: str
    value: Optional[str]


class PageAuditoria(QWidget):
    _PAGE_SIZE = 20

    def __init__(self, connection, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._i18n = I18nManager("es")
        self._queries = AuditoriaAccesosQueries(connection)
        self._usecase = BuscarAuditoriaAccesos(self._queries)
        self._offset = 0
        self._total = 0

        self._build_ui()
        self._retranslate()
        self._buscar()

    def on_show(self) -> None:
        self._buscar()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        filtros = QHBoxLayout()

        self.input_usuario = QLineEdit()
        self.input_desde = QLineEdit()
        self.input_hasta = QLineEdit()
        self.combo_accion = QComboBox()
        self.combo_entidad = QComboBox()
        self.btn_buscar = QPushButton()
        self.btn_limpiar = QPushButton()

        filtros.addWidget(QLabel(self._tr("auditoria.filtro.usuario")))
        filtros.addWidget(self.input_usuario)
        filtros.addWidget(QLabel(self._tr("auditoria.filtro.accion")))
        filtros.addWidget(self.combo_accion)
        filtros.addWidget(QLabel(self._tr("auditoria.filtro.entidad")))
        filtros.addWidget(self.combo_entidad)
        filtros.addWidget(QLabel(self._tr("auditoria.filtro.desde")))
        filtros.addWidget(self.input_desde)
        filtros.addWidget(QLabel(self._tr("auditoria.filtro.hasta")))
        filtros.addWidget(self.input_hasta)
        filtros.addWidget(self.btn_buscar)
        filtros.addWidget(self.btn_limpiar)

        self.tabla = QTableWidget(0, 6)
        self.lbl_estado = QLabel()
        paginacion = QHBoxLayout()
        self.btn_anterior = QPushButton()
        self.btn_siguiente = QPushButton()

        paginacion.addWidget(self.lbl_estado)
        paginacion.addStretch(1)
        paginacion.addWidget(self.btn_anterior)
        paginacion.addWidget(self.btn_siguiente)

        root.addLayout(filtros)
        root.addWidget(self.tabla)
        root.addLayout(paginacion)

        self.btn_buscar.clicked.connect(self._on_buscar)
        self.btn_limpiar.clicked.connect(self._on_limpiar)
        self.btn_anterior.clicked.connect(self._on_anterior)
        self.btn_siguiente.clicked.connect(self._on_siguiente)

    def _retranslate(self) -> None:
        self.btn_buscar.setText(self._tr("auditoria.accion.buscar"))
        self.btn_limpiar.setText(self._tr("auditoria.accion.limpiar"))
        self.btn_anterior.setText(self._tr("auditoria.accion.anterior"))
        self.btn_siguiente.setText(self._tr("auditoria.accion.siguiente"))
        self.input_desde.setPlaceholderText(self._tr("auditoria.filtro.fecha_placeholder"))
        self.input_hasta.setPlaceholderText(self._tr("auditoria.filtro.fecha_placeholder"))
        self.tabla.setHorizontalHeaderLabels(
            [
                self._tr("auditoria.columna.fecha_hora"),
                self._tr("auditoria.columna.usuario"),
                self._tr("auditoria.columna.demo"),
                self._tr("auditoria.columna.accion"),
                self._tr("auditoria.columna.entidad"),
                self._tr("auditoria.columna.id"),
            ]
        )
        self._cargar_combos()
        self._actualizar_estado(0)

    def _cargar_combos(self) -> None:
        self.combo_accion.clear()
        for item in self._opciones_accion():
            self.combo_accion.addItem(self._tr(item.key_i18n), item.value)

        self.combo_entidad.clear()
        for item in self._opciones_entidad():
            self.combo_entidad.addItem(self._tr(item.key_i18n), item.value)

    def _opciones_accion(self) -> tuple[_FiltroCombo, ...]:
        return (
            _FiltroCombo("auditoria.filtro.todas", None),
            _FiltroCombo("auditoria.accion.ver_historial", AccionAuditoriaAcceso.VER_HISTORIAL_PACIENTE.value),
            _FiltroCombo("auditoria.accion.ver_detalle_cita", AccionAuditoriaAcceso.VER_DETALLE_CITA.value),
            _FiltroCombo("auditoria.accion.copiar_informe", AccionAuditoriaAcceso.COPIAR_INFORME_CITA.value),
            _FiltroCombo("auditoria.accion.ver_detalle_receta", AccionAuditoriaAcceso.VER_DETALLE_RECETA.value),
        )

    def _opciones_entidad(self) -> tuple[_FiltroCombo, ...]:
        return (
            _FiltroCombo("auditoria.filtro.todas", None),
            _FiltroCombo("auditoria.entidad.paciente", EntidadAuditoriaAcceso.PACIENTE.value),
            _FiltroCombo("auditoria.entidad.cita", EntidadAuditoriaAcceso.CITA.value),
            _FiltroCombo("auditoria.entidad.receta", EntidadAuditoriaAcceso.RECETA.value),
        )

    def _on_buscar(self) -> None:
        self._offset = 0
        self._buscar()

    def _on_limpiar(self) -> None:
        self.input_usuario.clear()
        self.input_desde.clear()
        self.input_hasta.clear()
        self.combo_accion.setCurrentIndex(0)
        self.combo_entidad.setCurrentIndex(0)
        self._offset = 0
        self._buscar()

    def _on_anterior(self) -> None:
        self._offset = max(0, self._offset - self._PAGE_SIZE)
        self._buscar()

    def _on_siguiente(self) -> None:
        if self._offset + self._PAGE_SIZE >= self._total:
            return
        self._offset += self._PAGE_SIZE
        self._buscar()

    def _buscar(self) -> None:
        filtros = self._build_filtros()
        if filtros is None:
            return
        resultado = self._usecase.execute(filtros, self._PAGE_SIZE, self._offset)
        self._total = resultado.total
        self._render_filas(resultado.items)
        self._actualizar_estado(len(resultado.items))

    def _build_filtros(self) -> FiltrosAuditoriaAccesos | None:
        desde = self._parse_fecha_iso(self.input_desde.text().strip())
        hasta = self._parse_fecha_iso(self.input_hasta.text().strip())
        if self.input_desde.text().strip() and desde is None:
            self._mostrar_fecha_invalida(self._tr("auditoria.filtro.desde"))
            return None
        if self.input_hasta.text().strip() and hasta is None:
            self._mostrar_fecha_invalida(self._tr("auditoria.filtro.hasta"))
            return None
        return FiltrosAuditoriaAccesos(
            usuario_contiene=self.input_usuario.text().strip() or None,
            accion=self.combo_accion.currentData(),
            entidad_tipo=self.combo_entidad.currentData(),
            desde_utc=desde,
            hasta_utc=hasta,
        )

    def _parse_fecha_iso(self, value: str) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _mostrar_fecha_invalida(self, campo: str) -> None:
        mensaje = self._tr("auditoria.error.fecha_invalida").format(campo=campo)
        QMessageBox.warning(self, self._tr("auditoria.titulo"), mensaje)

    def _render_filas(self, items) -> None:
        self.tabla.setRowCount(0)
        for item in items:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            set_item(self.tabla, row, 0, item.timestamp_utc)
            set_item(self.tabla, row, 1, item.usuario)
            set_item(self.tabla, row, 2, self._tr("comun.si") if item.modo_demo else self._tr("comun.no"))
            set_item(self.tabla, row, 3, item.accion)
            set_item(self.tabla, row, 4, item.entidad_tipo)
            set_item(self.tabla, row, 5, item.entidad_id)

    def _actualizar_estado(self, mostrados: int) -> None:
        self.lbl_estado.setText(self._tr("auditoria.paginacion.mostrando").format(mostrados=mostrados, total=self._total))
        self.btn_anterior.setEnabled(self._offset > 0)
        self.btn_siguiente.setEnabled(self._offset + mostrados < self._total)

    def _tr(self, key: str) -> str:
        return self._i18n.t(key)
