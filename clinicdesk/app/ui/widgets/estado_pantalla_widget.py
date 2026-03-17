from __future__ import annotations

from collections.abc import Callable
import logging

from PySide6.QtCore import QThread, Signal

from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QProgressBar,
    QWidget,
)

from clinicdesk.app.i18n import I18nManager


class EstadoPantallaWidget(QWidget):
    solicitar_loading = Signal(str)
    solicitar_empty = Signal(str, object, object)
    solicitar_error = Signal(str, object, object)
    solicitar_processing = Signal(str)
    solicitar_content = Signal(object)

    def __init__(self, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._i18n = i18n
        self._i18n.subscribe(self._retranslate)
        self._contenido: QWidget | None = None
        self._cta_handler: Callable[[], None] | None = None
        self._retry_handler: Callable[[], None] | None = None
        self._mensaje_loading: str | None = None
        self._mensaje_empty: str | None = None
        self._cta_text_key: str | None = None
        self._mensaje_error: str | None = None
        self._detalle_tecnico: str | None = None
        self._mensaje_processing: str | None = None
        self._estado_actual = "loading"

        self._stack = QStackedWidget(self)
        self._vista_loading = self._crear_vista_estado()
        self._lbl_loading = QLabel("", self._vista_loading)
        self._vista_loading.layout().addWidget(self._lbl_loading)

        self._vista_empty = self._crear_vista_estado()
        self._lbl_empty = QLabel("", self._vista_empty)
        self._btn_empty_cta = QPushButton("", self._vista_empty)
        self._btn_empty_cta.setVisible(False)
        self._btn_empty_cta.clicked.connect(self._on_cta_clicked)
        self._vista_empty.layout().addWidget(self._lbl_empty)
        self._vista_empty.layout().addWidget(self._btn_empty_cta)

        self._vista_error = self._crear_vista_estado()
        self._lbl_error = QLabel("", self._vista_error)
        self._lbl_error_detalle = QLabel("", self._vista_error)
        self._lbl_error_detalle.setVisible(False)
        self._btn_retry = QPushButton("", self._vista_error)
        self._btn_retry.setVisible(False)
        self._btn_retry.clicked.connect(self._on_retry_clicked)
        self._vista_error.layout().addWidget(self._lbl_error)
        self._vista_error.layout().addWidget(self._lbl_error_detalle)
        self._vista_error.layout().addWidget(self._btn_retry)

        self._vista_processing = self._crear_vista_estado()
        self._lbl_processing = QLabel("", self._vista_processing)
        self._progress_processing = QProgressBar(self._vista_processing)
        self._progress_processing.setRange(0, 0)
        self._vista_processing.layout().addWidget(self._lbl_processing)
        self._vista_processing.layout().addWidget(self._progress_processing)

        self._stack.addWidget(self._vista_loading)
        self._stack.addWidget(self._vista_empty)
        self._stack.addWidget(self._vista_error)
        self._stack.addWidget(self._vista_processing)

        self.solicitar_loading.connect(self._aplicar_loading)
        self.solicitar_empty.connect(self._aplicar_empty)
        self.solicitar_error.connect(self._aplicar_error)
        self.solicitar_processing.connect(self._aplicar_processing)
        self.solicitar_content.connect(self._aplicar_content)

        root = QVBoxLayout(self)
        root.addWidget(self._stack)
        self._retranslate()

    @property
    def estado_actual(self) -> str:
        return self._estado_actual

    def set_loading(self, mensaje_key: str) -> None:
        if not self._permitir_mutacion_estado(accion="set_loading"):
            self.solicitar_loading.emit(mensaje_key)
            return
        self._aplicar_loading(mensaje_key)

    def _aplicar_loading(self, mensaje_key: str) -> None:
        self._mensaje_loading = mensaje_key
        self._estado_actual = "loading"
        self._lbl_loading.setText(self._i18n.t(mensaje_key))
        self._lbl_loading.setAccessibleName(self._i18n.t(mensaje_key))
        self._stack.setCurrentWidget(self._vista_loading)

    def set_empty(
        self,
        mensaje_key: str,
        cta_text_key: str | None = None,
        on_cta: Callable[[], None] | None = None,
    ) -> None:
        if not self._permitir_mutacion_estado(accion="set_empty"):
            self.solicitar_empty.emit(mensaje_key, cta_text_key, on_cta)
            return
        self._aplicar_empty(mensaje_key, cta_text_key, on_cta)

    def _aplicar_empty(
        self,
        mensaje_key: str,
        cta_text_key: str | None = None,
        on_cta: Callable[[], None] | None = None,
    ) -> None:
        self._mensaje_empty = mensaje_key
        self._cta_text_key = cta_text_key
        self._cta_handler = on_cta
        self._estado_actual = "empty"
        self._lbl_empty.setText(self._i18n.t(mensaje_key))
        self._lbl_empty.setAccessibleName(self._i18n.t(mensaje_key))
        self._btn_empty_cta.setVisible(cta_text_key is not None)
        if cta_text_key:
            self._btn_empty_cta.setText(self._i18n.t(cta_text_key))
            self._btn_empty_cta.setFocus()
        self._stack.setCurrentWidget(self._vista_empty)

    def set_error(
        self,
        mensaje_key: str,
        detalle_tecnico: str | None = None,
        on_retry: Callable[[], None] | None = None,
    ) -> None:
        if not self._permitir_mutacion_estado(accion="set_error"):
            self.solicitar_error.emit(mensaje_key, detalle_tecnico, on_retry)
            return
        self._aplicar_error(mensaje_key, detalle_tecnico, on_retry)

    def _aplicar_error(
        self,
        mensaje_key: str,
        detalle_tecnico: str | None = None,
        on_retry: Callable[[], None] | None = None,
    ) -> None:
        self._mensaje_error = mensaje_key
        self._detalle_tecnico = detalle_tecnico
        self._retry_handler = on_retry
        self._estado_actual = "error"
        self._lbl_error.setText(self._i18n.t(mensaje_key))
        self._lbl_error.setAccessibleName(self._i18n.t(mensaje_key))
        self._lbl_error_detalle.setVisible(detalle_tecnico is not None)
        self._lbl_error_detalle.setText(detalle_tecnico or "")
        self._btn_retry.setVisible(on_retry is not None)
        if on_retry is not None:
            self._btn_retry.setText(self._i18n.t("ux_states.retry"))
            self._btn_retry.setFocus()
        self._stack.setCurrentWidget(self._vista_error)

    def set_processing(self, mensaje_key: str) -> None:
        if not self._permitir_mutacion_estado(accion="set_processing"):
            self.solicitar_processing.emit(mensaje_key)
            return
        self._aplicar_processing(mensaje_key)

    def _aplicar_processing(self, mensaje_key: str) -> None:
        self._mensaje_processing = mensaje_key
        self._estado_actual = "processing"
        self._lbl_processing.setText(self._i18n.t(mensaje_key))
        self._lbl_processing.setAccessibleName(self._i18n.t(mensaje_key))
        self._stack.setCurrentWidget(self._vista_processing)

    def set_ready(self, widget: QWidget) -> None:
        self.set_content(widget)

    def set_content(self, widget: QWidget) -> None:
        if not self._permitir_mutacion_estado(accion="set_content"):
            self.solicitar_content.emit(widget)
            return
        self._aplicar_content(widget)

    def _aplicar_content(self, widget: object) -> None:
        if not isinstance(widget, QWidget):
            self._logger.warning(
                "estado_pantalla_widget_widget_invalido",
                extra={"action": "estado_pantalla_widget_widget_invalido", "tipo": type(widget).__name__},
            )
            return
        if widget.thread() is not self.thread():
            self._logger.warning(
                "estado_pantalla_widget_thread_invalido",
                extra={"action": "estado_pantalla_widget_thread_invalido", "metodo": "set_content"},
            )
            return
        if self._contenido is not widget:
            if self._contenido is not None:
                self._stack.removeWidget(self._contenido)
                if self._contenido.parent() is self._stack:
                    self._contenido.setParent(None)
            self._contenido = widget
            if self._stack.indexOf(widget) == -1:
                self._stack.addWidget(widget)
        self._estado_actual = "content"
        self._stack.setCurrentWidget(widget)

    def _on_cta_clicked(self) -> None:
        if self._cta_handler is not None:
            self._cta_handler()

    def _on_retry_clicked(self) -> None:
        if self._retry_handler is not None:
            self._retry_handler()

    def _retranslate(self) -> None:
        if not self._permitir_mutacion_estado(accion="retranslate"):
            self._logger.warning(
                "estado_pantalla_widget_retranslate_fuera_hilo_gui",
                extra={"action": "estado_pantalla_widget_retranslate_fuera_hilo_gui"},
            )
            return
        if self._estado_actual == "loading" and self._mensaje_loading:
            self._lbl_loading.setText(self._i18n.t(self._mensaje_loading))
        if self._mensaje_empty:
            self._lbl_empty.setText(self._i18n.t(self._mensaje_empty))
        if self._cta_text_key:
            self._btn_empty_cta.setText(self._i18n.t(self._cta_text_key))
        if self._mensaje_error:
            self._lbl_error.setText(self._i18n.t(self._mensaje_error))
        if self._mensaje_processing:
            self._lbl_processing.setText(self._i18n.t(self._mensaje_processing))
        self._btn_retry.setText(self._i18n.t("ux_states.retry"))

    @staticmethod
    def _crear_vista_estado() -> QWidget:
        vista = QWidget()
        layout = QVBoxLayout(vista)
        layout.addStretch(1)
        return vista

    def _permitir_mutacion_estado(self, *, accion: str) -> bool:
        if QThread.currentThread() is self.thread():
            return True
        self._logger.warning(
            "estado_pantalla_widget_mutacion_fuera_hilo_gui",
            extra={"action": "estado_pantalla_widget_mutacion_fuera_hilo_gui", "metodo": accion},
        )
        return False
