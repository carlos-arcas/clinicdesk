from __future__ import annotations

from clinicdesk.app.common.log_redaction import redact_text, redact_value


def test_redact_text_masks_email_dni_and_phone() -> None:
    text = "Contacto: juan.perez@example.com doc 12345678 tel +54 11 5555 6666"

    redacted = redact_text(text)

    assert "juan.perez@example.com" not in redacted
    assert "12345678" not in redacted
    assert "+54 11 5555 6666" not in redacted
    assert redacted.count("***") >= 3


def test_redact_value_masks_sensitive_keys_recursively() -> None:
    payload = {
        "nombre": "Juan Perez",
        "contacto": {"email": "jp@example.com", "telefono": "1133344455"},
        "items": [{"documento": "12345678"}],
    }

    redacted = redact_value(payload)

    assert redacted["nombre"] == "***"
    assert redacted["contacto"]["email"] == "***"
    assert redacted["contacto"]["telefono"] == "***"
    assert redacted["items"][0]["documento"] == "***"
