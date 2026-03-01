from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.container import AppContainer
from clinicdesk.app.i18n import I18nManager


class RecordatorioCitaDialog(QDialog):
    def __init__(self, container: AppContainer, i18n: I18nManager, cita_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._container = container
        self._i18n = i18n
        self._cita_id = cita_id
        self._canal_actual = "WHATSAPP"
        self._build_ui()
        self._load_preview()

    def _build_ui(self) -> None:
        self.setWindowTitle(self._i18n.t("recordatorio.dialogo.titulo"))
        self.setMinimumWidth(560)
        root = QVBoxLayout(self)

        self.lbl_resumen = QLabel(self._i18n.t("recordatorio.estado.cargando"), self)
        self.cmb_canal = QComboBox(self)
        self.cmb_canal.addItem(self._i18n.t("recordatorio.canal.whatsapp"), "WHATSAPP")
        self.cmb_canal.addItem(self._i18n.t("recordatorio.canal.email"), "EMAIL")
        self.cmb_canal.addItem(self._i18n.t("recordatorio.canal.llamada"), "LLAMADA")
        self.lbl_contacto = QLabel("", self)
        self.lbl_aviso = QLabel("", self)
        self.lbl_estado = QLabel("", self)

        self.txt_mensaje = QPlainTextEdit(self)
        self.txt_mensaje.setReadOnly(True)

        barra = QHBoxLayout()
        barra.addWidget(QLabel(self._i18n.t("recordatorio.canal.label"), self))
        barra.addWidget(self.cmb_canal)
        barra.addStretch(1)

        root.addWidget(self.lbl_resumen)
        root.addLayout(barra)
        root.addWidget(self.lbl_contacto)
        root.addWidget(self.lbl_aviso)
        root.addWidget(self.lbl_estado)
        root.addWidget(self.txt_mensaje)
        root.addLayout(self._crear_botonera())
        self.cmb_canal.currentIndexChanged.connect(self._on_canal_cambiado)

    def _crear_botonera(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        self.btn_copiar = QPushButton(self._i18n.t("recordatorio.boton.copiar"), self)
        self.btn_guardar = QPushButton(self._i18n.t("recordatorio.boton.guardar_preparado"), self)
        self.btn_enviado = QPushButton(self._i18n.t("recordatorio.boton.marcar_enviado"), self)
        self.btn_cerrar = QPushButton(self._i18n.t("recordatorio.boton.cerrar"), self)
        self.btn_cerrar.clicked.connect(self.reject)
        self.btn_copiar.clicked.connect(self._copiar_mensaje)
        self.btn_guardar.clicked.connect(self._guardar_preparado)
        self.btn_enviado.clicked.connect(self._marcar_enviado)
        layout.addWidget(self.btn_copiar)
        layout.addWidget(self.btn_guardar)
        layout.addWidget(self.btn_enviado)
        layout.addStretch(1)
        layout.addWidget(self.btn_cerrar)
        return layout

    def _on_canal_cambiado(self) -> None:
        self._canal_actual = self.cmb_canal.currentData()
        self._load_preview()

    def _load_preview(self) -> None:
        self.lbl_resumen.setText(self._i18n.t("recordatorio.estado.cargando"))
        try:
            datos = self._container.recordatorios_citas_facade.preparar_uc.recordatorios.obtener_datos_recordatorio_cita(self._cita_id)
            preview = self._container.recordatorios_citas_facade.preparar_uc.ejecutar(
                self._cita_id, self._canal_actual, self._i18n.t
            )
            estados = self._container.recordatorios_citas_facade.obtener_estado_uc.ejecutar(self._cita_id)
        except Exception:
            self._render_error(self._i18n.t("recordatorio.error.carga"))
            return
        if datos is None:
            self._render_error(self._i18n.t("recordatorio.error.no_encontrada"))
            return
        self.lbl_resumen.setText(self._i18n.t("recordatorio.resumen.cita").format(fecha=datos.inicio[:10], hora=datos.inicio[11:16], paciente=datos.paciente_nombre))
        contacto = datos.telefono if self._canal_actual in {"WHATSAPP", "LLAMADA"} else datos.email
        self.lbl_contacto.setText(self._i18n.t("recordatorio.contacto.disponible").format(valor=contacto or self._i18n.t("recordatorio.contacto.no_disponible")))
        self.lbl_aviso.setText("\n".join(preview.advertencias))
        self.txt_mensaje.setPlainText(preview.mensaje)
        self.btn_copiar.setEnabled(preview.puede_copiar)
        self.btn_guardar.setEnabled(preview.puede_copiar)
        self._actualizar_estado(estados)

    def _actualizar_estado(self, estados) -> None:
        for item in estados:
            if item.canal != self._canal_actual:
                continue
            fecha = _format_fecha_hora(item.updated_at_utc)
            estado = self._i18n.t(f"recordatorio.estado.{item.estado.lower()}")
            self.lbl_estado.setText(self._i18n.t("recordatorio.estado.actual").format(estado=estado, fecha=fecha))
            return
        self.lbl_estado.setText("")

    def _render_error(self, texto: str) -> None:
        self.lbl_resumen.setText(texto)
        self.lbl_contacto.setText("")
        self.lbl_aviso.setText(texto)
        self.txt_mensaje.setPlainText("")
        self.btn_copiar.setEnabled(False)
        self.btn_guardar.setEnabled(False)

    def _copiar_mensaje(self) -> None:
        QApplication.clipboard().setText(self.txt_mensaje.toPlainText())

    def _guardar_preparado(self) -> None:
        self._guardar_estado("PREPARADO")

    def _marcar_enviado(self) -> None:
        confirmacion = QMessageBox.question(
            self,
            self.windowTitle(),
            self._i18n.t("recordatorio.confirmacion.enviado"),
        )
        if confirmacion != QMessageBox.Yes:
            return
        self._guardar_estado("ENVIADO")

    def _guardar_estado(self, estado: str) -> None:
        try:
            self._container.recordatorios_citas_facade.registrar_uc.ejecutar(self._cita_id, self._canal_actual, estado)
        except Exception:
            QMessageBox.warning(self, self.windowTitle(), self._i18n.t("recordatorio.mensaje.error_guardado"))
            return
        QMessageBox.information(self, self.windowTitle(), self._i18n.t("recordatorio.mensaje.guardado"))
        self._load_preview()


def _format_fecha_hora(valor: str) -> str:
    try:
        dt = datetime.fromisoformat(valor)
    except ValueError:
        return valor
    return dt.strftime("%Y-%m-%d %H:%M")
