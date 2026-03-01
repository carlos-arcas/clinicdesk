from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.application.prediccion_ausencias.cierre_citas_usecases import (
    CierreCitaItemRequest,
    CerrarCitasPendientesRequest,
    ESTADO_DEJAR_IGUAL,
    PaginacionPendientesCierre,
)
from clinicdesk.app.application.services.prediccion_ausencias_facade import PrediccionAusenciasFacade
from clinicdesk.app.i18n import I18nManager

_MAPA_RESULTADOS = {
    "prediccion_ausencias.cierre.resultado.vino": "REALIZADA",
    "prediccion_ausencias.cierre.resultado.no_vino": "NO_PRESENTADO",
    "prediccion_ausencias.cierre.resultado.cancelada": "CANCELADA",
    "prediccion_ausencias.cierre.resultado.dejar_igual": ESTADO_DEJAR_IGUAL,
}


class CerrarCitasAntiguasDialog(QDialog):
    def __init__(self, facade: PrediccionAusenciasFacade, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._facade = facade
        self._i18n = i18n
        self._items = []
        self._build_ui()
        self._i18n.subscribe(self._retranslate)
        self._retranslate()
        self._cargar_paso_1()

    def _build_ui(self) -> None:
        self.resize(980, 540)
        root = QVBoxLayout(self)
        self.lbl_titulo = QLabel()
        self.lbl_titulo.setObjectName("dialogTitle")
        root.addWidget(self.lbl_titulo)
        self.stacked = QStackedWidget()
        root.addWidget(self.stacked)
        self.stacked.addWidget(self._build_paso_1())
        self.stacked.addWidget(self._build_paso_2())
        self.stacked.addWidget(self._build_paso_3())

    def _build_paso_1(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.lbl_paso_1_titulo = QLabel()
        self.lbl_paso_1_estado = QLabel()
        self.lbl_paso_1_estado.setWordWrap(True)
        layout.addWidget(self.lbl_paso_1_titulo)
        layout.addWidget(self.lbl_paso_1_estado)
        row = QHBoxLayout()
        self.btn_paso_1_cerrar = QPushButton()
        self.btn_paso_1_continuar = QPushButton()
        self.btn_paso_1_cerrar.clicked.connect(self.reject)
        self.btn_paso_1_continuar.clicked.connect(lambda: self.stacked.setCurrentIndex(1))
        row.addWidget(self.btn_paso_1_cerrar)
        row.addStretch(1)
        row.addWidget(self.btn_paso_1_continuar)
        layout.addLayout(row)
        return panel

    def _build_paso_2(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.lbl_paso_2_titulo = QLabel()
        self.lbl_paso_2_contador = QLabel()
        layout.addWidget(self.lbl_paso_2_titulo)
        layout.addWidget(self.lbl_paso_2_contador)
        self.tabla = QTableWidget(0, 6)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabla)
        nav = QHBoxLayout()
        self.btn_paso_2_atras = QPushButton()
        self.btn_paso_2_cancelar = QPushButton()
        self.btn_paso_2_continuar = QPushButton()
        self.btn_paso_2_atras.clicked.connect(lambda: self.stacked.setCurrentIndex(0))
        self.btn_paso_2_cancelar.clicked.connect(self.reject)
        self.btn_paso_2_continuar.clicked.connect(self._mostrar_resumen)
        nav.addWidget(self.btn_paso_2_atras)
        nav.addWidget(self.btn_paso_2_cancelar)
        nav.addStretch(1)
        nav.addWidget(self.btn_paso_2_continuar)
        layout.addLayout(nav)
        return panel

    def _build_paso_3(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.lbl_paso_3_titulo = QLabel()
        self.lbl_paso_3_resumen = QLabel()
        self.lbl_paso_3_aviso = QLabel()
        self.lbl_paso_3_estado = QLabel()
        self.lbl_paso_3_estado.setWordWrap(True)
        layout.addWidget(self.lbl_paso_3_titulo)
        layout.addWidget(self.lbl_paso_3_resumen)
        layout.addWidget(self.lbl_paso_3_aviso)
        layout.addWidget(self.lbl_paso_3_estado)
        nav = QHBoxLayout()
        self.btn_paso_3_atras = QPushButton()
        self.btn_paso_3_cancelar = QPushButton()
        self.btn_paso_3_aplicar = QPushButton()
        self.btn_paso_3_atras.clicked.connect(lambda: self.stacked.setCurrentIndex(1))
        self.btn_paso_3_cancelar.clicked.connect(self.reject)
        self.btn_paso_3_aplicar.clicked.connect(self._aplicar_cambios)
        nav.addWidget(self.btn_paso_3_atras)
        nav.addWidget(self.btn_paso_3_cancelar)
        nav.addStretch(1)
        nav.addWidget(self.btn_paso_3_aplicar)
        layout.addLayout(nav)
        return panel

    def _retranslate(self) -> None:
        self.setWindowTitle(self._i18n.t("prediccion_ausencias.cierre.titulo"))
        self.lbl_titulo.setText(self._i18n.t("prediccion_ausencias.cierre.titulo"))
        self.lbl_paso_1_titulo.setText(self._i18n.t("prediccion_ausencias.cierre.paso_1.titulo"))
        self.lbl_paso_2_titulo.setText(self._i18n.t("prediccion_ausencias.cierre.paso_2.titulo"))
        self.lbl_paso_3_titulo.setText(self._i18n.t("prediccion_ausencias.cierre.paso_3.titulo"))
        self.btn_paso_1_cerrar.setText(self._i18n.t("prediccion_ausencias.cierre.boton.cerrar"))
        self.btn_paso_1_continuar.setText(self._i18n.t("prediccion_ausencias.cierre.boton.continuar"))
        self.btn_paso_2_atras.setText(self._i18n.t("prediccion_ausencias.cierre.boton.atras"))
        self.btn_paso_2_cancelar.setText(self._i18n.t("prediccion_ausencias.cierre.boton.cancelar"))
        self.btn_paso_2_continuar.setText(self._i18n.t("prediccion_ausencias.cierre.boton.continuar"))
        self.btn_paso_3_atras.setText(self._i18n.t("prediccion_ausencias.cierre.boton.atras"))
        self.btn_paso_3_cancelar.setText(self._i18n.t("prediccion_ausencias.cierre.boton.cancelar"))
        self.btn_paso_3_aplicar.setText(self._i18n.t("prediccion_ausencias.cierre.boton.aplicar_cambios"))
        self.tabla.setHorizontalHeaderLabels(
            [
                self._i18n.t("prediccion_ausencias.cierre.tabla.fecha"),
                self._i18n.t("prediccion_ausencias.cierre.tabla.hora"),
                self._i18n.t("prediccion_ausencias.cierre.tabla.paciente"),
                self._i18n.t("prediccion_ausencias.cierre.tabla.medico"),
                self._i18n.t("prediccion_ausencias.cierre.tabla.estado_actual"),
                self._i18n.t("prediccion_ausencias.cierre.tabla.resultado"),
            ]
        )

    def _cargar_paso_1(self) -> None:
        paginacion = PaginacionPendientesCierre(limite=200, offset=0)
        listado = self._facade.listar_citas_pendientes_cierre_uc.ejecutar(paginacion)
        self._items = listado.items
        if listado.total == 0:
            self.lbl_paso_1_estado.setText(self._i18n.t("prediccion_ausencias.cierre.todo_al_dia"))
        else:
            self.lbl_paso_1_estado.setText(
                self._i18n.t("prediccion_ausencias.cierre.encontradas").format(total=listado.total)
            )
        self.btn_paso_1_continuar.setEnabled(listado.total > 0)
        self._cargar_tabla()

    def _cargar_tabla(self) -> None:
        self.tabla.setRowCount(len(self._items))
        for row, item in enumerate(self._items):
            fecha, hora = self._separar_fecha_hora(item.inicio_local)
            self.tabla.setItem(row, 0, QTableWidgetItem(fecha))
            self.tabla.setItem(row, 1, QTableWidgetItem(hora))
            self.tabla.setItem(row, 2, QTableWidgetItem(item.paciente))
            self.tabla.setItem(row, 3, QTableWidgetItem(item.medico))
            self.tabla.setItem(
                row,
                4,
                QTableWidgetItem(self._i18n.t(f"prediccion_ausencias.estado_cita.{item.estado_actual.lower()}")),
            )
            combo = QComboBox()
            for key, estado in _MAPA_RESULTADOS.items():
                combo.addItem(self._i18n.t(key), estado)
            combo.currentIndexChanged.connect(self._actualizar_contador)
            self.tabla.setCellWidget(row, 5, combo)
        self._actualizar_contador()

    def _actualizar_contador(self) -> None:
        seleccionadas = self._contar_seleccionadas()
        self.lbl_paso_2_contador.setText(
            self._i18n.t("prediccion_ausencias.cierre.seleccionadas").format(total=seleccionadas)
        )
        self.btn_paso_2_continuar.setEnabled(seleccionadas > 0)

    def _mostrar_resumen(self) -> None:
        total = self._contar_seleccionadas()
        self.lbl_paso_3_resumen.setText(self._i18n.t("prediccion_ausencias.cierre.resumen").format(total=total))
        self.lbl_paso_3_aviso.setText(self._i18n.t("prediccion_ausencias.cierre.aviso"))
        self.lbl_paso_3_estado.clear()
        self.stacked.setCurrentIndex(2)

    def _contar_seleccionadas(self) -> int:
        total = 0
        for row in range(self.tabla.rowCount()):
            combo = self.tabla.cellWidget(row, 5)
            if isinstance(combo, QComboBox) and combo.currentData() != ESTADO_DEJAR_IGUAL:
                total += 1
        return total

    def _aplicar_cambios(self) -> None:
        self.lbl_paso_3_estado.setText(self._i18n.t("prediccion_ausencias.cierre.guardando"))
        self.btn_paso_3_aplicar.setEnabled(False)
        items = self._construir_request_items()
        request = CerrarCitasPendientesRequest(items=items)
        try:
            self._facade.cerrar_citas_pendientes_uc.ejecutar(request)
        except Exception:
            self.btn_paso_3_aplicar.setEnabled(True)
            QMessageBox.warning(self, self.windowTitle(), self._i18n.t("prediccion_ausencias.cierre.error_guardado"))
            return
        self.lbl_paso_3_estado.setText(self._i18n.t("prediccion_ausencias.cierre.listo"))
        self.accept()

    def _construir_request_items(self) -> list[CierreCitaItemRequest]:
        request_items: list[CierreCitaItemRequest] = []
        for row, item in enumerate(self._items):
            combo = self.tabla.cellWidget(row, 5)
            if not isinstance(combo, QComboBox):
                continue
            request_items.append(CierreCitaItemRequest(cita_id=item.cita_id, nuevo_estado=str(combo.currentData())))
        return request_items

    @staticmethod
    def _separar_fecha_hora(valor: str) -> tuple[str, str]:
        try:
            dt = datetime.fromisoformat(valor)
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
        except ValueError:
            if " " in valor:
                fecha, hora = valor.split(" ", 1)
                return fecha, hora[:5]
            return valor, ""
