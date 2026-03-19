from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.ui.bootstrap_ui import ResultadoReintentoPagina

_MAX_DETALLE = 120


class PageNoDisponible(QWidget):
    def __init__(
        self,
        *,
        i18n: I18nManager,
        nombre_pagina: str,
        codigo_error: str,
        detalles_cortos: str = "",
        on_reintentar: Callable[[], ResultadoReintentoPagina] | None = None,
    ) -> None:
        super().__init__()
        self._i18n = i18n
        self._nombre_pagina = nombre_pagina
        self._codigo_error = codigo_error
        self._detalles_cortos = detalles_cortos[:_MAX_DETALLE]
        self._on_reintentar = on_reintentar

        self._titulo = QLabel()
        self._descripcion = QLabel()
        self._detalle = QLabel()
        self._feedback = QLabel()
        self._boton_reintentar = QPushButton()
        self._boton_reintentar.clicked.connect(self._reintentar_carga)

        self._build_ui()
        self._apply_i18n()

    def _build_ui(self) -> None:
        self._titulo.setWordWrap(True)
        self._descripcion.setWordWrap(True)
        self._detalle.setWordWrap(True)
        self._feedback.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self._titulo)
        layout.addWidget(self._descripcion)
        layout.addWidget(self._detalle)
        layout.addWidget(self._boton_reintentar)
        layout.addWidget(self._feedback)
        layout.addStretch(1)

    def _apply_i18n(self) -> None:
        self._titulo.setText(self._i18n.t("placeholder.titulo"))
        self._descripcion.setText(self._i18n.t("placeholder.descripcion"))
        self._boton_reintentar.setText(self._i18n.t("placeholder.reintentar"))
        self._detalle.setText(self._build_detalle())

    def _build_detalle(self) -> str:
        if not self._detalles_cortos:
            return ""
        return self._i18n.t("placeholder.detalle").format(
            nombre_pagina=self._nombre_pagina,
            codigo_error=self._codigo_error,
            detalle=self._detalles_cortos,
        )

    def _reintentar_carga(self) -> None:
        if self._on_reintentar is None:
            return
        resultado = self._on_reintentar()
        if resultado.ok:
            self._actualizar_titulo_navegacion(resultado)
        if resultado.ok and self._reemplazar_por_pagina(resultado.pagina_recuperada):
            return
        self._feedback.setText(self._build_feedback(resultado))

    def _build_feedback(self, resultado: ResultadoReintentoPagina) -> str:
        clave = "placeholder.reintento_ok" if resultado.ok else "placeholder.reintento_fail"
        texto = self._i18n.t(clave)
        if resultado.mensaje:
            texto = f"{texto}: {resultado.mensaje[:_MAX_DETALLE]}"
        return texto

    def _reemplazar_por_pagina(self, pagina: object | None) -> bool:
        if not isinstance(pagina, QWidget):
            return False
        parent = self.parentWidget()
        while parent is not None:
            if isinstance(parent, QStackedWidget):
                indice = parent.indexOf(self)
                if indice == -1:
                    return False
                parent.insertWidget(indice, pagina)
                parent.setCurrentWidget(pagina)
                parent.removeWidget(self)
                self.deleteLater()
                return True
            parent = parent.parentWidget()
        return False

    def _actualizar_titulo_navegacion(self, resultado: ResultadoReintentoPagina) -> None:
        if not resultado.page_id or not resultado.titulo_pagina:
            return
        parent = self.parentWidget()
        while parent is not None:
            actualizador = getattr(parent, "actualizar_titulo_pagina", None)
            if callable(actualizador):
                actualizador(resultado.page_id, resultado.titulo_pagina)
                return
            parent = parent.parentWidget()
