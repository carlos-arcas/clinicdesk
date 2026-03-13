from clinicdesk.app.ui.forms_estado import ControladorEstadoFormulario


def _validador(valores: dict[str, str]) -> dict[str, str]:
    errores: dict[str, str] = {}
    if not valores.get("nombre"):
        errores["nombre"] = "requerido"
    return errores


def test_controlador_estado_formulario_ciclo_basico() -> None:
    ctrl = ControladorEstadoFormulario(validador=_validador)
    ctrl.inicializar({"nombre": ""})

    estado_inicial = ctrl.validar()
    assert not estado_inicial.modificado
    assert not estado_inicial.valido
    assert not estado_inicial.listo_para_enviar

    estado_editado = ctrl.actualizar_valores({"nombre": "Ana"})
    assert estado_editado.modificado
    assert estado_editado.valido
    assert estado_editado.listo_para_enviar

    estado_guardando = ctrl.marcar_guardando(True)
    assert estado_guardando.guardando
    assert not estado_guardando.listo_para_enviar

    estado_error = ctrl.registrar_error_guardado("fallo")
    assert estado_error.error_guardado == "fallo"

    estado_ok = ctrl.marcar_guardado_exitoso()
    assert not estado_ok.modificado
    assert estado_ok.valido
    assert estado_ok.error_guardado is None
