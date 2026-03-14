from clinicdesk.app.domain.seguros import EstadoOportunidadSeguro, validar_transicion_estado


def test_transicion_valida_en_pipeline() -> None:
    validar_transicion_estado(EstadoOportunidadSeguro.OFERTA_ENVIADA, EstadoOportunidadSeguro.EN_SEGUIMIENTO)


def test_transicion_invalida_lanza_error() -> None:
    try:
        validar_transicion_estado(EstadoOportunidadSeguro.DETECTADA, EstadoOportunidadSeguro.CONVERTIDA)
    except ValueError as exc:
        assert "Transicion invalida" in str(exc)
    else:
        raise AssertionError("Debio lanzar ValueError")
