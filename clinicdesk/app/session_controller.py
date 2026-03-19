from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from clinicdesk.app.bootstrap_logging import ContextLoggerAdapter


@dataclass(frozen=True)
class ContextoSesionAutenticada:
    username: str
    demo_mode: bool
    run_id: str


class FabricaVentanaPrincipal(Protocol):
    def crear_ventana_principal(
        self,
        contexto: ContextoSesionAutenticada,
        on_logout: Callable[[], None],
    ) -> Any: ...


class AplicacionSesion(Protocol):
    def setQuitOnLastWindowClosed(self, enabled: bool) -> None: ...


class I18nSesion(Protocol):
    def t(self, key: str, **kwargs: object) -> str: ...


def crear_sesion_autenticada(
    contexto_usuario: ContextoSesionAutenticada,
    factories: FabricaVentanaPrincipal,
    on_logout: Callable[[], None],
) -> Any:
    return factories.crear_ventana_principal(contexto_usuario, on_logout)


def debe_mantener_referencia_ventana_principal(ventana: Any) -> bool:
    return ventana is not None


class ControladorSesionAutenticada:
    def __init__(
        self,
        app: AplicacionSesion,
        i18n: I18nSesion,
        logger: ContextLoggerAdapter,
        factories: FabricaVentanaPrincipal,
        mostrar_error: Callable[[str], None],
    ) -> None:
        self._app = app
        self._i18n = i18n
        self._logger = logger
        self._factories = factories
        self._mostrar_error = mostrar_error
        self.ventana_principal: Any | None = None

    def transicionar_post_login(
        self,
        contexto: ContextoSesionAutenticada,
        on_logout: Callable[[], None],
    ) -> bool:
        self._logger.info("auth_login_accepted", extra={"action": "auth_login_accepted"})
        self._app.setQuitOnLastWindowClosed(False)
        try:
            self._cerrar_ventana_anterior()
            self._logger.info("main_window_create", extra={"action": "main_window_create"})
            ventana = crear_sesion_autenticada(contexto, self._factories, on_logout)
            if not debe_mantener_referencia_ventana_principal(ventana):
                self._registrar_fallo_transicion("main_window_init_failed")
                return False
            self.ventana_principal = ventana
            setattr(self._app, "ventana_principal", ventana)
            ventana.show()
            self._logger.info("main_window_show", extra={"action": "main_window_show"})
            if not ventana.isVisible():
                self._registrar_fallo_transicion("main_window_init_failed")
                return False
            self._app.setQuitOnLastWindowClosed(True)
            self._logger.info("post_login_transition_ok", extra={"action": "post_login_transition_ok"})
            return True
        except Exception as exc:  # pragma: no cover - protegido por test funcional
            self._registrar_fallo_transicion("unexpected_error", exc)
            return False

    def _registrar_fallo_transicion(self, reason_code: str, exc: Exception | None = None) -> None:
        extra = {"action": "post_login_transition_fail", "reason_code": reason_code, "exc_type": "none"}
        if exc is not None:
            extra["exc_type"] = type(exc).__name__
        self._logger.error("post_login_transition_fail", extra=extra)
        self._mostrar_error(self._i18n.t("session.error.open_failed"))

    def _cerrar_ventana_anterior(self) -> None:
        if self.ventana_principal is None:
            return
        self.ventana_principal.close()
        self.ventana_principal = None
