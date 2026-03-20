from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from clinicdesk.app.session_controller import (
    ContextoSesionAutenticada,
    ControladorSesionAutenticada,
    crear_sesion_autenticada,
    debe_mantener_referencia_ventana_principal,
)


@dataclass
class VentanaFalsa:
    visible: bool = False
    closed: bool = False

    def show(self) -> None:
        self.visible = True

    def close(self) -> None:
        self.closed = True

    def isVisible(self) -> bool:
        return self.visible


class FabricaFalsa:
    def __init__(self) -> None:
        self.contexto: ContextoSesionAutenticada | None = None
        self.logout = None
        self.ventana = VentanaFalsa()

    def crear_ventana_principal(self, contexto: ContextoSesionAutenticada, on_logout):
        self.contexto = contexto
        self.logout = on_logout
        return self.ventana


class LoggerFalso:
    def __init__(self) -> None:
        self.eventos: list[tuple[str, dict[str, str] | None]] = []

    def info(self, mensaje: str, extra=None) -> None:
        self.eventos.append((mensaje, extra))

    def warning(self, mensaje: str, extra=None) -> None:
        self.eventos.append((mensaje, extra))

    def error(self, mensaje: str, extra=None) -> None:
        self.eventos.append((mensaje, extra))


class AppFalsa:
    def __init__(self) -> None:
        self.quit_on_last_window_closed = True
        self.historial: list[bool] = []

    def setQuitOnLastWindowClosed(self, enabled: bool) -> None:
        self.quit_on_last_window_closed = enabled
        self.historial.append(enabled)


class I18nFalso:
    def t(self, key: str, **kwargs: object) -> str:
        return key


def test_crear_sesion_autenticada_devuelve_ventana_no_nula() -> None:
    contexto = ContextoSesionAutenticada(username="demo", demo_mode=True, run_id="run-1")
    fabrica = FabricaFalsa()

    ventana = crear_sesion_autenticada(contexto, fabrica, on_logout=lambda: None)

    assert ventana is fabrica.ventana
    assert fabrica.contexto == contexto


def test_debe_mantener_referencia_ventana_principal() -> None:
    assert debe_mantener_referencia_ventana_principal(object()) is True
    assert debe_mantener_referencia_ventana_principal(None) is False


def test_controlador_guarda_referencia_en_app_y_controlador() -> None:
    fabrica = FabricaFalsa()
    app = AppFalsa()
    logger = LoggerFalso()
    errores: list[str] = []
    controlador = ControladorSesionAutenticada(app, I18nFalso(), logger, fabrica, errores.append)

    ok = controlador.transicionar_post_login(
        ContextoSesionAutenticada(username="ana", demo_mode=False, run_id="r1"),
        on_logout=lambda: None,
    )

    assert ok is True
    assert controlador.ventana_principal is fabrica.ventana
    assert getattr(app, "ventana_principal") is fabrica.ventana
    assert fabrica.ventana.isVisible() is True
    assert app.historial == [False, True]
    assert [evento[0] for evento in logger.eventos] == [
        "auth_login_accepted",
        "main_window_create",
        "main_window_show",
        "post_login_transition_ok",
    ]


def test_flujo_no_define_sys_exit_en_controlador() -> None:
    contenido = Path("clinicdesk/app/session_controller.py").read_text(encoding="utf-8")

    assert "sys.exit" not in contenido
    assert ".quit(" not in contenido


def test_controlador_reporta_error_si_fabrica_devuelve_none() -> None:
    class FabricaNula(FabricaFalsa):
        def crear_ventana_principal(self, contexto: ContextoSesionAutenticada, on_logout):
            self.contexto = contexto
            self.logout = on_logout
            return None

    fabrica = FabricaNula()
    app = AppFalsa()
    logger = LoggerFalso()
    errores: list[str] = []
    controlador = ControladorSesionAutenticada(app, I18nFalso(), logger, fabrica, errores.append)

    ok = controlador.transicionar_post_login(
        ContextoSesionAutenticada(username="ana", demo_mode=False, run_id="r1"),
        on_logout=lambda: None,
    )

    assert ok is False
    assert errores == ["session.error.open_failed"]
    assert logger.eventos[-1][1] == {
        "action": "post_login_transition_fail",
        "reason_code": "main_window_init_failed",
        "exc_type": "none",
    }
    assert app.historial == [False]


def test_controlador_falla_si_ventana_no_queda_visible() -> None:
    class VentanaInvisible(VentanaFalsa):
        def show(self) -> None:
            self.visible = False

    fabrica = FabricaFalsa()
    fabrica.ventana = VentanaInvisible()
    app = AppFalsa()
    logger = LoggerFalso()
    errores: list[str] = []
    controlador = ControladorSesionAutenticada(app, I18nFalso(), logger, fabrica, errores.append)

    ok = controlador.transicionar_post_login(
        ContextoSesionAutenticada(username="ana", demo_mode=False, run_id="r1"),
        on_logout=lambda: None,
    )

    assert ok is False
    assert controlador.ventana_principal is fabrica.ventana
    assert errores == ["session.error.open_failed"]
    assert app.historial == [False]
    assert logger.eventos[-1][1] == {
        "action": "post_login_transition_fail",
        "reason_code": "main_window_init_failed",
        "exc_type": "none",
    }


def test_controlador_cierra_ventana_anterior_antes_de_recrear() -> None:
    fabrica = FabricaFalsa()
    app = AppFalsa()
    logger = LoggerFalso()
    controlador = ControladorSesionAutenticada(app, I18nFalso(), logger, fabrica, lambda _msg: None)
    ventana_anterior = VentanaFalsa(visible=True)
    controlador.ventana_principal = ventana_anterior

    ok = controlador.transicionar_post_login(
        ContextoSesionAutenticada(username="ana", demo_mode=False, run_id="r2"),
        on_logout=lambda: None,
    )

    assert ok is True
    assert ventana_anterior.closed is True
    assert controlador.ventana_principal is fabrica.ventana


def test_controlador_reporta_error_si_factory_lanza_excepcion() -> None:
    class FabricaExplosiva:
        def crear_ventana_principal(self, contexto: ContextoSesionAutenticada, on_logout):
            raise RuntimeError("boom")

    app = AppFalsa()
    logger = LoggerFalso()
    errores: list[str] = []
    controlador = ControladorSesionAutenticada(app, I18nFalso(), logger, FabricaExplosiva(), errores.append)

    ok = controlador.transicionar_post_login(
        ContextoSesionAutenticada(username="ana", demo_mode=False, run_id="r1"),
        on_logout=lambda: None,
    )

    assert ok is False
    assert errores == ["session.error.open_failed"]
    assert logger.eventos[-1][1] == {
        "action": "post_login_transition_fail",
        "reason_code": "unexpected_error",
        "exc_type": "RuntimeError",
    }
    assert app.historial == [False]
