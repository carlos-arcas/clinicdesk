from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
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
from clinicdesk.app.application.usecases.exportar_auditoria_csv import (
    ExportacionAuditoriaError,
    ExportacionAuditoriaDemasiadasFilasError,
    ExportarAuditoriaCSV,
    mapear_error_exportacion,
)
from clinicdesk.app.application.usecases.filtros_auditoria import PRESET_30_DIAS, PRESET_7_DIAS, PRESET_HOY, PRESET_PERSONALIZADO
from clinicdesk.app.application.usecases.obtener_resumen_auditoria import ObtenerResumenAuditoria
from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.auditoria.persistencia_exportacion_settings import (
    clave_ultima_ruta_exportacion_auditoria,
    normalizar_ruta_sugerida_exportacion,
)
from clinicdesk.app.pages.shared.table_utils import set_item
from clinicdesk.app.queries.auditoria_accesos_queries import AuditoriaAccesosQueries, FiltrosAuditoriaAccesos


LOGGER = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class _FiltroCombo:
    key_i18n: str
    value: Optional[str]


class PageAuditoria(QWidget):
    _PAGE_SIZE = 20

    def __init__(self, connection, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._i18n = I18nManager("es")
        self._settings = QSettings("clinicdesk", "ui")
        self._queries = AuditoriaAccesosQueries(connection)
        self._uc_buscar = BuscarAuditoriaAccesos(self._queries)
        self._uc_resumen = ObtenerResumenAuditoria(self._queries)
        self._uc_exportar = ExportarAuditoriaCSV(self._queries)
        self._offset = 0
        self._total = 0

        self._build_ui()
        self._retranslate()
        self._buscar()

    def on_show(self) -> None:
        self._buscar()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.addLayout(self._build_resumen())
        root.addLayout(self._build_filtros())

        self.tabla = QTableWidget(0, 6)
        root.addWidget(self.tabla)

        paginacion = QHBoxLayout()
        self.lbl_estado = QLabel()
        self.btn_reintentar = QPushButton()
        self.btn_exportar = QPushButton()
        self.btn_anterior = QPushButton()
        self.btn_siguiente = QPushButton()
        paginacion.addWidget(self.lbl_estado)
        paginacion.addWidget(self.btn_reintentar)
        paginacion.addStretch(1)
        paginacion.addWidget(self.btn_exportar)
        paginacion.addWidget(self.btn_anterior)
        paginacion.addWidget(self.btn_siguiente)
        root.addLayout(paginacion)

        self.btn_buscar.clicked.connect(self._on_buscar)
        self.btn_limpiar.clicked.connect(self._on_limpiar)
        self.btn_anterior.clicked.connect(self._on_anterior)
        self.btn_siguiente.clicked.connect(self._on_siguiente)
        self.btn_reintentar.clicked.connect(self._buscar)
        self.btn_exportar.clicked.connect(self._on_exportar)

    def _build_resumen(self) -> QGridLayout:
        resumen = QGridLayout()
        self.lbl_accesos_hoy = QLabel("0")
        self.lbl_accesos_7_dias = QLabel("0")
        self.lbl_top_acciones = QLabel("-")
        resumen.addWidget(QLabel(self._tr("auditoria.resumen.accesos_hoy")), 0, 0)
        resumen.addWidget(self.lbl_accesos_hoy, 0, 1)
        resumen.addWidget(QLabel(self._tr("auditoria.resumen.accesos_7_dias")), 0, 2)
        resumen.addWidget(self.lbl_accesos_7_dias, 0, 3)
        resumen.addWidget(QLabel(self._tr("auditoria.resumen.top_acciones")), 1, 0)
        resumen.addWidget(self.lbl_top_acciones, 1, 1, 1, 3)
        return resumen

    def _build_filtros(self) -> QHBoxLayout:
        filtros = QHBoxLayout()
        self.input_usuario = QLineEdit()
        self.input_desde = QLineEdit()
        self.input_hasta = QLineEdit()
        self.combo_rango = QComboBox()
        self.combo_accion = QComboBox()
        self.combo_entidad = QComboBox()
        self.btn_buscar = QPushButton()
        self.btn_limpiar = QPushButton()

        filtros.addWidget(QLabel(self._tr("auditoria.filtro.rango")))
        filtros.addWidget(self.combo_rango)
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
        self.combo_rango.currentIndexChanged.connect(self._on_preset_cambiado)
        return filtros

    def _retranslate(self) -> None:
        self.btn_buscar.setText(self._tr("auditoria.accion.buscar"))
        self.btn_limpiar.setText(self._tr("auditoria.accion.limpiar"))
        self.btn_anterior.setText(self._tr("auditoria.accion.anterior"))
        self.btn_siguiente.setText(self._tr("auditoria.accion.siguiente"))
        self.btn_exportar.setText(self._tr("auditoria.accion.exportar_csv"))
        self.btn_reintentar.setText(self._tr("auditoria.accion.reintentar"))
        self.input_desde.setPlaceholderText(self._tr("auditoria.filtro.fecha_placeholder"))
        self.input_hasta.setPlaceholderText(self._tr("auditoria.filtro.fecha_placeholder"))
        self.tabla.setHorizontalHeaderLabels([self._tr(k) for k in _columnas_tabla()])
        self._cargar_combos()
        self._set_estado("idle", 0)

    def _cargar_combos(self) -> None:
        self._cargar_combo(self.combo_rango, self._opciones_rango())
        self._cargar_combo(self.combo_accion, self._opciones_accion())
        self._cargar_combo(self.combo_entidad, self._opciones_entidad())

    @staticmethod
    def _cargar_combo(combo: QComboBox, opciones: tuple[_FiltroCombo, ...]) -> None:
        combo.clear()
        for item in opciones:
            combo.addItem(item.key_i18n, item.value)

    def _opciones_rango(self) -> tuple[_FiltroCombo, ...]:
        return (
            _FiltroCombo(self._tr("auditoria.filtro.rango.hoy"), PRESET_HOY),
            _FiltroCombo(self._tr("auditoria.filtro.rango.7_dias"), PRESET_7_DIAS),
            _FiltroCombo(self._tr("auditoria.filtro.rango.30_dias"), PRESET_30_DIAS),
            _FiltroCombo(self._tr("auditoria.filtro.rango.personalizado"), PRESET_PERSONALIZADO),
        )

    def _opciones_accion(self) -> tuple[_FiltroCombo, ...]:
        return (
            _FiltroCombo(self._tr("auditoria.filtro.todas"), None),
            _FiltroCombo(self._tr("auditoria.accion.ver_historial"), AccionAuditoriaAcceso.VER_HISTORIAL_PACIENTE.value),
            _FiltroCombo(self._tr("auditoria.accion.ver_detalle_cita"), AccionAuditoriaAcceso.VER_DETALLE_CITA.value),
            _FiltroCombo(self._tr("auditoria.accion.copiar_informe"), AccionAuditoriaAcceso.COPIAR_INFORME_CITA.value),
            _FiltroCombo(self._tr("auditoria.accion.ver_detalle_receta"), AccionAuditoriaAcceso.VER_DETALLE_RECETA.value),
        )

    def _opciones_entidad(self) -> tuple[_FiltroCombo, ...]:
        return (
            _FiltroCombo(self._tr("auditoria.filtro.todas"), None),
            _FiltroCombo(self._tr("auditoria.entidad.paciente"), EntidadAuditoriaAcceso.PACIENTE.value),
            _FiltroCombo(self._tr("auditoria.entidad.cita"), EntidadAuditoriaAcceso.CITA.value),
            _FiltroCombo(self._tr("auditoria.entidad.receta"), EntidadAuditoriaAcceso.RECETA.value),
        )

    def _on_preset_cambiado(self) -> None:
        personalizado = self.combo_rango.currentData() == PRESET_PERSONALIZADO
        self.input_desde.setEnabled(personalizado)
        self.input_hasta.setEnabled(personalizado)

    def _on_buscar(self) -> None:
        self._offset = 0
        self._buscar()

    def _on_limpiar(self) -> None:
        self.input_usuario.clear()
        self.input_desde.clear()
        self.input_hasta.clear()
        self.combo_rango.setCurrentIndex(0)
        self.combo_accion.setCurrentIndex(0)
        self.combo_entidad.setCurrentIndex(0)
        self._offset = 0
        self._buscar()

    def _on_anterior(self) -> None:
        self._offset = max(0, self._offset - self._PAGE_SIZE)
        self._buscar()

    def _on_siguiente(self) -> None:
        if self._offset + self._PAGE_SIZE < self._total:
            self._offset += self._PAGE_SIZE
            self._buscar()

    def _buscar(self) -> None:
        self._set_estado("loading", 0)
        filtros = self._build_filtros()
        if filtros is None:
            return
        try:
            preset = self.combo_rango.currentData()
            resultado = self._uc_buscar.execute(filtros, self._PAGE_SIZE, self._offset, preset_rango=preset)
            resumen = self._uc_resumen.execute(filtros.desde_utc, filtros.hasta_utc)
        except Exception:
            self._set_estado("error", 0)
            return
        self._total = resultado.total
        self._render_filas(resultado.items)
        self._render_resumen(resumen)
        self._set_estado("empty" if self._total == 0 else "ok", len(resultado.items))

    def _on_exportar(self) -> None:
        if self._total == 0 or not self._confirmar_exportacion():
            return
        filtros = self._build_filtros()
        if filtros is None:
            return
        preset_rango = self.combo_rango.currentData()
        try:
            exportacion = self._uc_exportar.execute(filtros, preset_rango=preset_rango)
        except ExportacionAuditoriaDemasiadasFilasError as exc:
            self._mostrar_error_exportacion(exc.reason_code, permitir_reintento=False)
            return
        except ExportacionAuditoriaError as exc:
            self._mostrar_error_exportacion(exc.reason_code, permitir_reintento=False)
            return
        self._guardar_exportacion_con_reintento(exportacion.csv_texto, exportacion.filas, exportacion.nombre_archivo_sugerido, preset_rango)

    def _guardar_exportacion_con_reintento(self, csv_texto: str, total_filas: int, nombre_archivo: str, preset_rango: str | None) -> None:
        ruta_sugerida = self._ruta_sugerida_exportacion(nombre_archivo)
        while True:
            ruta_guardado, _ = QFileDialog.getSaveFileName(self, self._tr("auditoria.exportar.titulo_guardar"), ruta_sugerida, "CSV (*.csv)")
            if not ruta_guardado:
                return
            try:
                Path(ruta_guardado).write_text(csv_texto, encoding="utf-8")
            except OSError as exc:
                reason_code = mapear_error_exportacion(exc)
                self._registrar_fallo_exportacion(reason_code, total_filas, preset_rango, tiene_ruta=bool(ruta_guardado))
                if not self._mostrar_error_exportacion(reason_code, permitir_reintento=True):
                    return
                ruta_sugerida = ruta_guardado
                continue
            self._guardar_ultima_ruta_exportacion(ruta_guardado)
            QMessageBox.information(self, self._tr("auditoria.titulo"), self._tr("auditoria.export_ok"))
            return

    def _mostrar_error_exportacion(self, reason_code: str, *, permitir_reintento: bool) -> bool:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(self._tr("auditoria.export_error_titulo"))
        box.setText(self._tr(f"auditoria.export_error_texto_{reason_code}"))
        box.setInformativeText(self._tr(f"auditoria.export_error_sugerencia_{reason_code}"))
        boton_cancelar = box.addButton(self._tr("auditoria.cancelar"), QMessageBox.RejectRole)
        if not permitir_reintento:
            box.exec()
            return False
        boton_reintentar = box.addButton(self._tr("auditoria.reintentar"), QMessageBox.AcceptRole)
        box.exec()
        return box.clickedButton() == boton_reintentar and box.clickedButton() is not boton_cancelar

    def _ruta_sugerida_exportacion(self, nombre_archivo: str) -> str:
        ultima_ruta = self._settings.value(clave_ultima_ruta_exportacion_auditoria(), "", type=str)
        return normalizar_ruta_sugerida_exportacion(ultima_ruta or None, nombre_archivo)

    def _guardar_ultima_ruta_exportacion(self, ruta_guardado: str) -> None:
        carpeta = str(Path(ruta_guardado).expanduser().resolve().parent)
        self._settings.setValue(clave_ultima_ruta_exportacion_auditoria(), carpeta)

    def _registrar_fallo_exportacion(self, reason_code: str, total_filas: int, preset_rango: str | None, *, tiene_ruta: bool) -> None:
        LOGGER.warning(
            "auditoria_export_fail",
            extra={
                "action": "auditoria_export_fail",
                "reason_code": reason_code,
                "total_filas": total_filas,
                "preset_rango": preset_rango or "none",
                "tiene_ruta": tiene_ruta,
            },
        )

    def _confirmar_exportacion(self) -> bool:
        msg = self._tr("auditoria.exportar.confirmacion").format(total=self._total)
        return QMessageBox.question(self, self._tr("auditoria.titulo"), msg) == QMessageBox.Yes

    def _build_filtros(self) -> FiltrosAuditoriaAccesos | None:
        desde_text = self.input_desde.text().strip()
        hasta_text = self.input_hasta.text().strip()
        desde = self._parse_fecha_iso(desde_text)
        hasta = self._parse_fecha_iso(hasta_text)
        if desde_text and desde is None:
            return self._error_fecha(self._tr("auditoria.filtro.desde"))
        if hasta_text and hasta is None:
            return self._error_fecha(self._tr("auditoria.filtro.hasta"))
        return FiltrosAuditoriaAccesos(
            usuario_contiene=self.input_usuario.text().strip() or None,
            accion=self.combo_accion.currentData(),
            entidad_tipo=self.combo_entidad.currentData(),
            desde_utc=desde,
            hasta_utc=hasta,
        )

    def _error_fecha(self, campo: str) -> None:
        QMessageBox.warning(self, self._tr("auditoria.titulo"), self._tr("auditoria.error.fecha_invalida").format(campo=campo))
        return None

    @staticmethod
    def _parse_fecha_iso(value: str) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

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

    def _render_resumen(self, resumen) -> None:
        self.lbl_accesos_hoy.setText(str(resumen.accesos_hoy))
        self.lbl_accesos_7_dias.setText(str(resumen.accesos_ultimos_7_dias))
        top = [f"{item.accion} ({item.total})" for item in resumen.top_acciones]
        self.lbl_top_acciones.setText(", ".join(top) if top else self._tr("auditoria.resumen.sin_datos"))

    def _set_estado(self, estado: str, mostrados: int) -> None:
        if estado == "loading":
            texto = self._tr("auditoria.estado.cargando")
        elif estado == "empty":
            texto = self._tr("auditoria.estado.vacio")
        elif estado == "error":
            texto = self._tr("auditoria.estado.error")
        else:
            texto = self._tr("auditoria.paginacion.mostrando").format(mostrados=mostrados, total=self._total)
        self.lbl_estado.setText(texto)
        self.btn_reintentar.setVisible(estado == "error")
        self.btn_exportar.setEnabled(self._total > 0)
        self.btn_anterior.setEnabled(self._offset > 0 and estado == "ok")
        self.btn_siguiente.setEnabled(self._offset + mostrados < self._total and estado == "ok")

    def _tr(self, key: str) -> str:
        return self._i18n.t(key)


def _columnas_tabla() -> tuple[str, ...]:
    return (
        "auditoria.columna.fecha_hora",
        "auditoria.columna.usuario",
        "auditoria.columna.demo",
        "auditoria.columna.accion",
        "auditoria.columna.entidad",
        "auditoria.columna.id",
    )
