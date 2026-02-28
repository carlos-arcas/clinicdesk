from __future__ import annotations

import base64
import os
from datetime import date

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.infrastructure.sqlite.repos_pacientes import PacientesRepository


def test_paciente_pii_is_encrypted_at_rest_when_flag_enabled(db_connection) -> None:
    previous = {k: os.environ.get(k) for k in ("CLINICDESK_FIELD_CRYPTO", "CLINICDESK_FIELD_KEY", "CLINICDESK_FIELD_HASH_KEY")}
    os.environ["CLINICDESK_FIELD_CRYPTO"] = "1"
    os.environ["CLINICDESK_FIELD_KEY"] = base64.urlsafe_b64encode(b"k" * 32).decode("ascii")
    os.environ["CLINICDESK_FIELD_HASH_KEY"] = base64.urlsafe_b64encode(b"h" * 32).decode("ascii")

    try:
        repo = PacientesRepository(db_connection)
        paciente_id = repo.create(
            Paciente(
                tipo_documento=TipoDocumento.DNI,
                documento="77711122",
                nombre="Nora",
                apellidos="Luna",
                telefono="612888111",
                email="nora@example.test",
                fecha_nacimiento=date(1990, 1, 1),
                direccion="Av. Central 10",
                activo=True,
                num_historia=None,
                alergias=None,
                observaciones=None,
            )
        )

        row = db_connection.execute(
            "SELECT documento, email, telefono, direccion, documento_enc, email_enc, telefono_enc, direccion_enc "
            "FROM pacientes WHERE id = ?",
            (paciente_id,),
        ).fetchone()
        assert row is not None
        assert row["documento"] != "77711122"
        assert row["email"] is None
        assert row["telefono"] is None
        assert row["direccion"] is None
        assert row["documento_enc"]
        assert row["email_enc"]
        assert row["telefono_enc"]
        assert row["direccion_enc"]

        restored = repo.get_by_id(paciente_id)
        assert restored is not None
        assert restored.documento == "77711122"
        assert restored.email == "nora@example.test"
        assert restored.telefono == "612888111"
        assert restored.direccion == "Av. Central 10"
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
