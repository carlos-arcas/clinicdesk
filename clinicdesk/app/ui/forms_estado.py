from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


ValidadorCampos = Callable[[dict[str, str]], dict[str, str]]


@dataclass(frozen=True, slots=True)
class EstadoFormulario:
    modificado: bool
    valido: bool
    guardando: bool
    errores_validacion: dict[str, str]
    error_guardado: str | None

    @property
    def listo_para_enviar(self) -> bool:
        return self.modificado and self.valido and not self.guardando

    @property
    def cambios_sin_guardar(self) -> bool:
        return self.modificado and not self.guardando


class ControladorEstadoFormulario:
    def __init__(self, *, validador: ValidadorCampos | None = None) -> None:
        self._validador = validador
        self._valores_iniciales: dict[str, str] = {}
        self._valores_actuales: dict[str, str] = {}
        self._errores_validacion: dict[str, str] = {}
        self._guardando = False
        self._error_guardado: str | None = None

    def inicializar(self, valores: dict[str, str]) -> None:
        self._valores_iniciales = dict(valores)
        self._valores_actuales = dict(valores)
        self._errores_validacion = {}
        self._guardando = False
        self._error_guardado = None

    @property
    def estado(self) -> EstadoFormulario:
        modificado = self._valores_actuales != self._valores_iniciales
        valido = not self._errores_validacion
        return EstadoFormulario(
            modificado=modificado,
            valido=valido,
            guardando=self._guardando,
            errores_validacion=dict(self._errores_validacion),
            error_guardado=self._error_guardado,
        )

    def actualizar_campo(self, campo: str, valor: str, *, validar: bool = True) -> EstadoFormulario:
        self._valores_actuales[campo] = valor
        if validar:
            self.validar()
        return self.estado

    def actualizar_valores(self, valores: dict[str, str], *, validar: bool = True) -> EstadoFormulario:
        self._valores_actuales = dict(valores)
        if validar:
            self.validar()
        return self.estado

    def validar(self) -> EstadoFormulario:
        if not self._validador:
            self._errores_validacion = {}
            return self.estado
        self._errores_validacion = dict(self._validador(dict(self._valores_actuales)))
        return self.estado

    def marcar_guardando(self, guardando: bool) -> EstadoFormulario:
        self._guardando = guardando
        return self.estado

    def registrar_error_guardado(self, mensaje: str) -> EstadoFormulario:
        self._error_guardado = mensaje
        return self.estado

    def limpiar_error_guardado(self) -> EstadoFormulario:
        self._error_guardado = None
        return self.estado

    def marcar_guardado_exitoso(self) -> EstadoFormulario:
        self._valores_iniciales = dict(self._valores_actuales)
        self._error_guardado = None
        self._guardando = False
        return self.estado
