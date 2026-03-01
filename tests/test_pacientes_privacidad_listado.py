from clinicdesk.app.application.services.pacientes_listado_contrato import ContratoListadoPacientesService
from clinicdesk.app.domain.pacientes_mascaras import (
    enmascarar_documento,
    enmascarar_email,
    enmascarar_telefono,
    enmascarar_texto_general,
)
from clinicdesk.app.domain.pacientes_privacidad import (
    NIVEL_SENSIBILIDAD_POR_ATRIBUTO,
    NivelSensibilidad,
    nivel_sensibilidad_de_atributo,
)


def test_mapa_sensibilidad_atributos_tipicos() -> None:
    assert NIVEL_SENSIBILIDAD_POR_ATRIBUTO["nombre"] is NivelSensibilidad.PUBLICO
    assert NIVEL_SENSIBILIDAD_POR_ATRIBUTO["documento"] is NivelSensibilidad.PERSONAL
    assert NIVEL_SENSIBILIDAD_POR_ATRIBUTO["telefono"] is NivelSensibilidad.PERSONAL
    assert NIVEL_SENSIBILIDAD_POR_ATRIBUTO["num_historia"] is NivelSensibilidad.SENSIBLE
    assert NIVEL_SENSIBILIDAD_POR_ATRIBUTO["alergias"] is NivelSensibilidad.SENSIBLE


def test_mapa_sensibilidad_default_conservador() -> None:
    assert nivel_sensibilidad_de_atributo("campo_inexistente") is NivelSensibilidad.SENSIBLE


def test_enmascarar_documento() -> None:
    assert enmascarar_documento("40000014") == "******14"
    assert enmascarar_documento("AB") == "AB"
    assert enmascarar_documento("") == ""
    assert enmascarar_documento(None) == ""


def test_enmascarar_telefono() -> None:
    assert enmascarar_telefono("610000314") == "*** *** 314"
    assert enmascarar_telefono("31") == "31"
    assert enmascarar_telefono("") == ""
    assert enmascarar_telefono(None) == ""


def test_enmascarar_email() -> None:
    assert enmascarar_email("a@b.com") == "a***@b.com"
    assert enmascarar_email("ab@dominio.es") == "a***@dominio.es"
    assert enmascarar_email("") == ""
    assert enmascarar_email(None) == ""


def test_enmascarar_texto_general() -> None:
    assert enmascarar_texto_general("Calle Mayor 3") == "C********** 3"
    assert enmascarar_texto_general("AB") == "**"
    assert enmascarar_texto_general("") == ""
    assert enmascarar_texto_general(None) == ""


def test_formatter_listado_publico_y_sensible() -> None:
    service = ContratoListadoPacientesService()

    assert service.formatear_valor_listado("nombre", "Ana") == "Ana"
    assert service.formatear_valor_listado("documento", "40000014") == "******14"
    assert service.formatear_valor_listado("num_historia", "HIST-0001") == "H******01"


def test_contrato_lista_atributos_ordenados_y_claves_i18n() -> None:
    service = ContratoListadoPacientesService()

    atributos = service.atributos_disponibles()
    assert atributos[0].nombre == "id"
    assert atributos[1].nombre == "tipo_documento"
    assert atributos[2].clave_i18n == "pacientes.documento"
