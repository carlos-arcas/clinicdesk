from __future__ import annotations

import pytest

from clinicdesk.app.application.auditoria.metadata_segura import (
    CLAVES_METADATA_AUDITORIA_PERMITIDAS,
    MetadataAuditoriaError,
    sanitizar_metadata_auditoria,
)


def test_contrato_claves_metadata_no_permite_campos_hash_ni_enc() -> None:
    assert "paciente_id_hash" not in CLAVES_METADATA_AUDITORIA_PERMITIDAS


def test_sanitizar_metadata_auditoria_redacta_valores_pii() -> None:
    metadata = {
        "reason_code": "email ana@test.com telefono 600123123",
        "medico_id": 12,
    }

    saneada = sanitizar_metadata_auditoria(metadata)

    assert saneada["medico_id"] == 12
    assert saneada["reason_code"] == "email [REDACTED_EMAIL] telefono [REDACTED_PHONE]"


@pytest.mark.parametrize("clave", ["email", "documento", "telefono", "observaciones", "paciente_id_hash"])
def test_sanitizar_metadata_auditoria_bloquea_clave_sensible(clave: str) -> None:
    with pytest.raises(MetadataAuditoriaError):
        sanitizar_metadata_auditoria({clave: "valor"})
