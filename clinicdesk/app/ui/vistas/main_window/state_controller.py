from __future__ import annotations

from clinicdesk.app.ui.vistas.main_window.ui_layout_helpers import normalizar_alturas_inputs


def _normalize_input_heights(self) -> None:
    widgets = [
        getattr(self, "persona_combo", None),
        getattr(self, "fecha_input", None),
        getattr(self, "desde_input", None),
        getattr(self, "hasta_input", None),
        getattr(self, "notas_input", None),
    ]
    normalizar_alturas_inputs([widget for widget in widgets if widget is not None])
