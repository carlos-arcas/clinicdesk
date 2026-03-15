from clinicdesk.app.pages.pacientes.coordinador_carga import CoordinadorCargaPacientes, SolicitudCargaPacientes


def _solicitud(token: int) -> SolicitudCargaPacientes:
    return SolicitudCargaPacientes(token=token, seleccion_id=token, activo=True, texto=f"t{token}")


def test_coordinador_lanza_primera_y_encola_ultima() -> None:
    coordinador = CoordinadorCargaPacientes()

    assert coordinador.registrar(_solicitud(1)) is True
    assert coordinador.registrar(_solicitud(2)) is False
    assert coordinador.registrar(_solicitud(3)) is False

    siguiente = coordinador.finalizar(1)

    assert siguiente is not None
    assert siguiente.token == 3
    assert coordinador.es_token_activo(3)


def test_coordinador_ignora_finalizacion_de_token_obsoleto() -> None:
    coordinador = CoordinadorCargaPacientes()
    coordinador.registrar(_solicitud(4))
    coordinador.registrar(_solicitud(5))

    assert coordinador.finalizar(3) is None
    assert coordinador.es_token_activo(4)
