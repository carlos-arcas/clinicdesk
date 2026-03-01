from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QPushButton, QWidget

from .pagina_base import PaginaBase, _I18nProtocol


class PaginaSync(PaginaBase):
    def __init__(
        self,
        i18n: _I18nProtocol,
        on_abrir_guia: Callable[[], None],
        parent: QWidget | None = None,
    ) -> None:
        self._on_abrir_guia = on_abrir_guia
        super().__init__(i18n=i18n, parent=parent)

    def _construir_widgets(self) -> None:
        self._boton_ver_guia = QPushButton(self)
        self._boton_ver_guia.clicked.connect(self._on_abrir_guia)
        self._layout_principal.addWidget(self._boton_ver_guia)

    def actualizar_textos(self) -> None:
        self._titulo.setText(self._i18n.t("wizard.sync.titulo"))
        self._descripcion.setText(self._i18n.t("wizard.sync.descripcion"))
        self._boton_ver_guia.setText(self._i18n.t("wizard.sync.ver_guia"))
