from __future__ import annotations

import pytest

from clinicdesk.app.common.search_utils import normalize_search_text
from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Paciente


def test_paciente_validar_normaliza_campos_texto_para_canonicalizacion() -> None:
    paciente = Paciente(
        tipo_documento=TipoDocumento.DNI,
        documento=" 12345678 ",
        nombre=" Laura ",
        apellidos=" Gomez ",
        telefono=" 600123123 ",
        email="  laura@example.test  ",
        direccion="  Calle 1  ",
        num_historia=" H-1 ",
        alergias=" Penicilina ",
        observaciones="  Nota clínica breve  ",
    )

    paciente.validar()

    assert paciente.documento == "12345678"
    assert paciente.nombre == "Laura"
    assert paciente.apellidos == "Gomez"
    assert paciente.telefono == "600123123"
    assert paciente.email == "laura@example.test"
    assert paciente.direccion == "Calle 1"
    assert paciente.num_historia == "H-1"
    assert paciente.alergias == "Penicilina"
    assert paciente.observaciones == "Nota clínica breve"


def test_paciente_validar_rechaza_telefono_no_canonico() -> None:
    paciente = Paciente(
        tipo_documento=TipoDocumento.DNI,
        documento="12345678",
        nombre="Laura",
        apellidos="Gomez",
        telefono="+34 600123123",
    )

    with pytest.raises(ValidationError, match="Teléfono debe ser numérico"):
        paciente.validar()


def test_normalize_search_text_aplica_trim_y_descarta_vacios() -> None:
    assert normalize_search_text("  paciente  ") == "paciente"
    assert normalize_search_text("   ") is None
    assert normalize_search_text(None) is None


# TODO(security-field-protection-001): cuando exista hash/cifrado por campo,
# añadir tests de integración para verificar escritura dual (claro + protegido)
# y lectura preferente desde columnas protegidas.
