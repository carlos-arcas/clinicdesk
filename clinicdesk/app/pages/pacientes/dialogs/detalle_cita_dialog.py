from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.application.auditoria_acceso import AccionAuditoriaAcceso, EntidadAuditoriaAcceso
from clinicdesk.app.application.security import UserContext
from clinicdesk.app.application.usecases.obtener_detalle_cita import DetalleCitaDTO, DetalleCitaNoEncontradaError, ObtenerDetalleCita
from clinicdesk.app.application.usecases.registrar_auditoria_acceso import RegistrarAuditoriaAcceso
from clinicdesk.app.i18n import I18nManager


class DetalleCitaDialog(QDialog):
    def __init__(
        self,
        i18n: I18nManager,
        usecase: ObtenerDetalleCita,
        auditoria_uc: RegistrarAuditoriaAcceso,
        contexto_usuario: UserContext,
        cita_id: int,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._i18n = i18n
        self._usecase = usecase
        self._auditoria_uc = auditoria_uc
        self._contexto_usuario = contexto_usuario
        self._cita_id = cita_id
        self._build_ui()
        self._cargar_detalle()
        self._registrar_apertura()

    def _build_ui(self) -> None:
        self.setMinimumSize(860, 580)
        self.setWindowTitle(self._i18n.t("pacientes.historial.citas.detalle.titulo"))
        root = QVBoxLayout(self)

        self.lbl_estado = QLabel("")
        root.addWidget(self.lbl_estado)
        root.addWidget(self._build_cabecera())
        root.addWidget(QLabel(self._i18n.t("pacientes.historial.citas.detalle.informe")))

        self.txt_informe = QPlainTextEdit(self)
        self.txt_informe.setReadOnly(True)
        root.addWidget(self.txt_informe)

        root.addWidget(QLabel(self._i18n.t("pacientes.historial.citas.detalle.incidencias")))
        self.table_incidencias = QTableWidget(0, 3, self)
        self.table_incidencias.setHorizontalHeaderLabels(
            [
                self._i18n.t("pacientes.historial.citas.detalle.incidencias.fecha"),
                self._i18n.t("pacientes.historial.citas.detalle.incidencias.estado"),
                self._i18n.t("pacientes.historial.citas.detalle.incidencias.resumen"),
            ]
        )
        root.addWidget(self.table_incidencias)

        self.lbl_incidencias = QLabel("")
        root.addWidget(self.lbl_incidencias)
        root.addLayout(self._build_actions())

    def _build_cabecera(self) -> QWidget:
        cabecera = QWidget(self)
        form = QFormLayout(cabecera)
        self.lbl_fecha_hora = QLabel("")
        self.lbl_medico = QLabel("")
        self.lbl_sala = QLabel("")
        self.lbl_estado_cita = QLabel("")
        form.addRow(self._i18n.t("pacientes.historial.citas.detalle.fecha_hora"), self.lbl_fecha_hora)
        form.addRow(self._i18n.t("pacientes.historial.citas.detalle.medico"), self.lbl_medico)
        form.addRow(self._i18n.t("pacientes.historial.citas.detalle.sala"), self.lbl_sala)
        form.addRow(self._i18n.t("pacientes.historial.citas.detalle.estado"), self.lbl_estado_cita)
        return cabecera

    def _build_actions(self) -> QHBoxLayout:
        actions = QHBoxLayout()
        self.btn_copiar = QPushButton(self._i18n.t("pacientes.historial.citas.detalle.copiar_informe"), self)
        self.btn_cerrar = QPushButton(self._i18n.t("comun.cerrar"), self)
        self.btn_copiar.clicked.connect(self._copiar_informe)
        self.btn_cerrar.clicked.connect(self.accept)
        actions.addStretch(1)
        actions.addWidget(self.btn_copiar)
        actions.addWidget(self.btn_cerrar)
        return actions

    def _cargar_detalle(self) -> None:
        self.lbl_estado.setText(self._i18n.t("pacientes.historial.cargando"))
        try:
            detalle = self._usecase.execute(self._cita_id)
        except DetalleCitaNoEncontradaError:
            self._render_error(self._i18n.t("pacientes.historial.citas.detalle.error.no_encontrada"))
            return
        except Exception:
            self._render_error(self._i18n.t("pacientes.historial.citas.detalle.error.carga"))
            return
        self._render_detalle(detalle)

    def _render_detalle(self, detalle: DetalleCitaDTO) -> None:
        self.lbl_estado.setText("")
        self.lbl_fecha_hora.setText(f"{detalle.fecha} {detalle.hora_inicio} - {detalle.hora_fin}")
        self.lbl_medico.setText(detalle.medico)
        self.lbl_sala.setText(detalle.sala)
        self.lbl_estado_cita.setText(detalle.estado)
        self.txt_informe.setPlainText(detalle.informe)
        self._render_incidencias(detalle)

    def _render_incidencias(self, detalle: DetalleCitaDTO) -> None:
        self.table_incidencias.setRowCount(0)
        if not detalle.incidencias:
            self.lbl_incidencias.setText(self._i18n.t("pacientes.historial.citas.detalle.sin_incidencias"))
            return
        self.lbl_incidencias.setText(
            self._i18n.t("pacientes.historial.citas.detalle.total_incidencias").format(total=detalle.total_incidencias)
        )
        for incidencia in detalle.incidencias:
            row = self.table_incidencias.rowCount()
            self.table_incidencias.insertRow(row)
            self.table_incidencias.setItem(row, 0, QTableWidgetItem(incidencia.fecha_hora))
            self.table_incidencias.setItem(row, 1, QTableWidgetItem(incidencia.estado))
            self.table_incidencias.setItem(row, 2, QTableWidgetItem(incidencia.resumen))

    def _registrar_apertura(self) -> None:
        self._auditoria_uc.execute(
            contexto_usuario=self._contexto_usuario,
            accion=AccionAuditoriaAcceso.VER_DETALLE_CITA,
            entidad_tipo=EntidadAuditoriaAcceso.CITA,
            entidad_id=self._cita_id,
        )

    def _render_error(self, mensaje: str) -> None:
        self.lbl_estado.setText(mensaje)
        self.btn_copiar.setEnabled(False)

    def _copiar_informe(self) -> None:
        QApplication.clipboard().setText(self.txt_informe.toPlainText())
        self._auditoria_uc.execute(
            contexto_usuario=self._contexto_usuario,
            accion=AccionAuditoriaAcceso.COPIAR_INFORME_CITA,
            entidad_tipo=EntidadAuditoriaAcceso.CITA,
            entidad_id=self._cita_id,
        )
        QMessageBox.information(
            self,
            self._i18n.t("pacientes.historial.citas.detalle.titulo"),
            self._i18n.t("pacientes.historial.citas.detalle.copiado"),
        )
