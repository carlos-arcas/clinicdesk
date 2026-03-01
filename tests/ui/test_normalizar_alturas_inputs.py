from clinicdesk.app.ui.vistas.main_window.ui_layout_helpers import normalizar_alturas_inputs


class FakeSize:
    def __init__(self, height: int) -> None:
        self._height = height

    def height(self) -> int:
        return self._height


class FakeWidget:
    def __init__(self, height: int) -> None:
        self._height = height
        self.fixed_height = None

    def sizeHint(self) -> FakeSize:
        return FakeSize(self._height)

    def setFixedHeight(self, value: int) -> None:
        self.fixed_height = value


class FakeWithoutSizeHint:
    def __init__(self) -> None:
        self.fixed_height = None

    def setFixedHeight(self, value: int) -> None:
        self.fixed_height = value


def test_normaliza_alturas_al_maximo() -> None:
    widgets = [FakeWidget(20), FakeWidget(30), FakeWidget(25)]

    normalizar_alturas_inputs(widgets)

    assert [widget.fixed_height for widget in widgets] == [30, 30, 30]


def test_no_falla_si_un_widget_no_tiene_size_hint() -> None:
    con_hint = FakeWidget(24)
    sin_hint = FakeWithoutSizeHint()

    normalizar_alturas_inputs([con_hint, sin_hint])

    assert con_hint.fixed_height == 24
    assert sin_hint.fixed_height == 24


def test_no_falla_con_lista_vacia() -> None:
    normalizar_alturas_inputs([])
