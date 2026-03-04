from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Callable, Generic, Sequence, TypeVar

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.application.preferencias.preferencias_usuario import (
    MARCADOR_REDACTADO,
    PreferenciasService,
    sanitize_search_text,
)
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.ui.quick_search_debounce import DespachadorDebounce

TResultado = TypeVar("TResultado")


@dataclass(frozen=True, slots=True)
class ContextoBusquedaRapida(Generic[TResultado]):
    contexto_id: str
    titulo_key: str
    placeholder_key: str
    empty_key: str
    buscar_async: Callable[[str, Callable[[Sequence[TResultado]], None]], None]
    on_select: Callable[[TResultado], None]
    render_item: Callable[[TResultado], str]


class QuickSearchDialog(QDialog):
    def __init__(
        self,
        i18n: I18nManager,
        preferencias_service: PreferenciasService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._i18n = i18n
        self._preferencias_service = preferencias_service
        self._contexto: ContextoBusquedaRapida[object] | None = None
        self._resultados: list[object] = []
        self._token_busqueda = 0
        self._debounce = DespachadorDebounce(delay_ms=250)

        self.setModal(False)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.resize(620, 420)

        root = QVBoxLayout(self)
        self._input = QLineEdit(self)
        self._lista = QListWidget(self)
        self._estado = QLabel(self)
        self._estado.setWordWrap(True)

        root.addWidget(self._input)
        root.addWidget(self._lista)
        root.addWidget(self._estado)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_debounce_timeout)

        self._input.textChanged.connect(self._on_text_changed)
        self._input.returnPressed.connect(self._on_enter)
        self._lista.itemActivated.connect(self._on_item_activated)

    def open_for(self, contexto: ContextoBusquedaRapida[object]) -> None:
        self._contexto = contexto
        self._resultados = []
        self._token_busqueda += 1
        preferencias = self._preferencias_service.get()
        busqueda_guardada = preferencias.last_search_by_context.get(contexto.contexto_id, "")
        self.setWindowTitle(self._i18n.t(contexto.titulo_key))
        self._input.setPlaceholderText(self._i18n.t(contexto.placeholder_key))
        self._input.setText(busqueda_guardada if busqueda_guardada != MARCADOR_REDACTADO else "")
        self._lista.clear()
        self._estado.setText(self._i18n.t(contexto.empty_key))
        self.show()
        self.raise_()
        self.activateWindow()
        self._input.setFocus()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def _on_text_changed(self, texto: str) -> None:
        if self._contexto is None:
            return
        self._debounce.registrar(texto.strip(), self._ahora_ms())
        self._timer.start(self._debounce.siguiente_espera_ms(self._ahora_ms()))

    def _on_debounce_timeout(self) -> None:
        texto = self._debounce.extraer_si_listo(self._ahora_ms())
        if texto is None:
            self._timer.start(self._debounce.siguiente_espera_ms(self._ahora_ms()))
            return
        self._disparar_busqueda(texto)

    def _disparar_busqueda(self, texto: str) -> None:
        if self._contexto is None:
            return
        self._token_busqueda += 1
        token = self._token_busqueda
        self._estado.setText("…")

        def _resolver(resultados: Sequence[object]) -> None:
            if token != self._token_busqueda:
                return
            self._resultados = list(resultados)
            self._lista.clear()
            for resultado in self._resultados:
                self._lista.addItem(QListWidgetItem(self._contexto.render_item(resultado)))
            if self._lista.count() > 0:
                self._lista.setCurrentRow(0)
            self._estado.setText(self._i18n.t(self._contexto.empty_key) if not self._resultados else "")

        self._contexto.buscar_async(texto, _resolver)

    def _on_enter(self) -> None:
        item = self._lista.currentItem()
        if item is None:
            return
        self._on_item_activated(item)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        if self._contexto is None:
            return
        fila = self._lista.row(item)
        if fila < 0 or fila >= len(self._resultados):
            return
        self._contexto.on_select(self._resultados[fila])
        self.close()

    def closeEvent(self, event) -> None:  # noqa: N802
        self._guardar_ultima_busqueda_contexto()
        super().closeEvent(event)

    def _guardar_ultima_busqueda_contexto(self) -> None:
        if self._contexto is None:
            return
        preferencias = self._preferencias_service.get()
        texto_seguro = sanitize_search_text(self._input.text())
        if texto_seguro is None:
            preferencias.last_search_by_context.pop(self._contexto.contexto_id, None)
        else:
            preferencias.last_search_by_context[self._contexto.contexto_id] = texto_seguro
        self._preferencias_service.set(preferencias)

    @staticmethod
    def _ahora_ms() -> int:
        return int(monotonic() * 1000)
