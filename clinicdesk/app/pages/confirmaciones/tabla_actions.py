from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from clinicdesk.app.pages.confirmaciones.acciones_whatsapp_rapido import EstadoAccionRapidaWhatsAppDTO


def crear_actions_confirmacion(
    parent: QWidget,
    texto_riesgo: str,
    texto_recordatorio: str,
    texto_preparando: str,
    estado_whatsapp: EstadoAccionRapidaWhatsAppDTO,
    whatsapp_en_curso: bool,
    tooltip_texto: str,
    on_ver_riesgo: Callable[[], None],
    on_preparar_recordatorio: Callable[[], None],
) -> QWidget:
    actions = QWidget(parent)
    lay = QHBoxLayout(actions)
    lay.setContentsMargins(0, 0, 0, 0)
    btn_riesgo = QPushButton(texto_riesgo, actions)
    btn_recordatorio = QPushButton(texto_recordatorio, actions)
    btn_recordatorio.setVisible(estado_whatsapp.visible)
    btn_recordatorio.setEnabled(estado_whatsapp.enabled and not whatsapp_en_curso)
    if whatsapp_en_curso:
        btn_recordatorio.setText(texto_preparando)
    if tooltip_texto:
        btn_recordatorio.setToolTip(tooltip_texto)
    btn_riesgo.clicked.connect(on_ver_riesgo)
    btn_recordatorio.clicked.connect(on_preparar_recordatorio)
    lay.addWidget(btn_riesgo)
    lay.addWidget(btn_recordatorio)
    return actions
